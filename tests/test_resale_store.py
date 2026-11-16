"""Tests for the resale single write path (skills/resale/scripts/resale_store.py).

These must be green BEFORE any data moves — the migration trusts this module
to refuse bad records, so the refusals are what gets tested first.

Concurrency tests use real processes (not threads): the races being defended
against are two Claude sessions / a dashboard and a skill, i.e. separate
processes contending for the same file.
"""

from __future__ import annotations

import csv
import multiprocessing as mp
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

RESALE_DIR = Path(__file__).resolve().parents[1] / "skills" / "resale" / "scripts"
sys.path.insert(0, str(RESALE_DIR))

import resale_store as rs  # noqa: E402

TODAY = date.today().isoformat()

COMPLETE_FB_SALE = {
    "platform": "fbmp",
    "price": 25,
    "date": "2026-06-28",
    "date_basis": "exact",
    "fees": 0,
    "shipping_charged": 0,
    "shipping_cost": 0,
    "refund": 0,
}
COMPLETE_EBAY_SALE = {
    "platform": "ebay",
    "price": 40,
    "date": "2026-07-02",
    "date_basis": "exact",
    "fees": 5.2,
    "shipping_charged": 8,
    "shipping_cost": 7.5,
    "refund": 0,
    "order_id": "12-34567-89012",
}


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------


@pytest.fixture
def store(tmp_path, monkeypatch):
    """An empty store rooted at a tmpdir."""
    monkeypatch.setenv("RESALE_BASE", str(tmp_path))
    (tmp_path / "items").mkdir()
    return tmp_path


def minimal(**over) -> dict:
    d = {
        "name_en": "SodaStream Terra Sparkling Water Maker",
        "name_zh": "SodaStream 气泡水机",
        "category": "coffee",
        "condition": "used_good",
        "price_ask": 25,
        "acquisition": {
            "date": "2024-03-01",
            "date_basis": "release_date",
            "price": 89.99,
            "source": "msrp",
            "confidence": "medium",
        },
    }
    d.update(over)
    return d


def new(**over):
    item, rev, _ = rs.create(minimal(**over))
    return item, rev


def sell(uid: str = "R001", **sale):
    return rs.update(uid, {"disposition": "sold", "sale": {**COMPLETE_FB_SALE, **sale}})


def legacy_closed(store: Path, uid: str, **fields) -> Path:
    """A closed record still sitting in items/ — the pre-archive state of the
    102 finished items. Written raw, the way the old store left them."""
    folder = store / "items" / f"{uid}-legacy-thing"
    (folder / "photos").mkdir(parents=True)
    (folder / "photos" / "a.jpg").write_bytes(b"x")
    (folder / "photos" / "clip.mp4").write_bytes(b"x")
    payload = {
        "uid": uid,
        "category": "misc",
        "created": "2026-06-01",
        "updated": "2026-06-01",
        **fields,
    }
    (folder / "item.yaml").write_text(yaml.safe_dump(payload, allow_unicode=True))
    return folder


# --------------------------------------------------------------------------
# roundtrip + canonical form
# --------------------------------------------------------------------------


def test_create_then_load_roundtrips(store):
    item, rev = new()
    assert item.uid == "R001"
    assert (store / "items" / "R001-sodastream-terra-sparkling-water-maker").is_dir()
    back, rev2 = rs.load("R001")
    assert rev2 == rev
    assert back.model_dump() == item.model_dump()


def test_create_makes_no_evidence_dir(store):
    new()
    assert not (rs.item_dir("R001") / "evidence").exists()
    assert (rs.item_dir("R001") / "photos").is_dir()


def test_create_only_makes_available_items(store):
    """items/ is the current wave; a closed record is born in years/ via a transition."""
    with pytest.raises(rs.Invalid) as e:
        rs.create(minimal(price_ask=None, disposition="kept", disposition_date=TODAY))
    assert "CREATE_AVAILABLE_ONLY" in str(e.value)


def test_slug_is_ascii_only_and_capped(store):
    item, _ = new(name_en=None, name_zh="乐高 Game Boy 10306", category="lego")
    folder = rs.item_dir(item.uid).name
    assert folder.isascii(), folder
    assert rs.DIR_RE.match(folder), folder


def test_multiline_strings_use_literal_blocks(store):
    new(description_en="line one\nline two\n")
    text = (rs.item_dir("R001") / "item.yaml").read_text()
    assert "description_en: |" in text, text


def test_dates_serialize_as_iso_strings_not_yaml_timestamps(store):
    new()
    text = (rs.item_dir("R001") / "item.yaml").read_text()
    assert "date: '2024-03-01'" in text
    reloaded, _ = rs.load("R001")
    assert reloaded.acquisition.date == date(2024, 3, 1)


def test_write_is_atomic_no_tmp_left_behind(store):
    new()
    rs.update("R001", {"price_ask": 30})
    leftovers = [
        p.name for p in rs.item_dir("R001").iterdir() if p.name.startswith(".item.")
    ]
    assert leftovers == []


def test_rev_changes_on_write(store):
    _, rev1 = new()
    _, rev2 = rs.update("R001", {"price_ask": 31})
    assert rev1 != rev2


# --------------------------------------------------------------------------
# validators — each one is a refused write
# --------------------------------------------------------------------------


def test_unknown_field_is_refused(store):
    with pytest.raises(rs.Invalid) as e:
        rs.create(minimal(cost_basis=30))
    assert "cost_basis" in str(e.value)


def test_sold_without_price_is_refused(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"disposition": "sold", "sale": {"platform": "fbmp"}})
    assert "price" in str(e.value)


def test_sold_without_platform_is_refused(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"disposition": "sold", "sale": {"price": 25}})
    assert "platform" in str(e.value)


def test_sold_refused_unless_every_tax_field_is_present(store):
    """The item leaves items/ the moment it is sold — there is no later
    backfill window, so an incomplete sale is never written."""
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update(
            "R001", {"disposition": "sold", "sale": {"platform": "fbmp", "price": 25}}
        )
    msg = str(e.value)
    assert "TAX_INCOMPLETE" in msg
    for f in ("sale.date", "sale.received"):
        assert f in msg, f
    assert rs.item_dir("R001").exists()  # nothing moved


def test_ebay_sale_needs_order_id(store):
    new()
    sale = {k: v for k, v in COMPLETE_EBAY_SALE.items() if k != "order_id"}
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"disposition": "sold", "sale": sale})
    assert "sale.order_id" in str(e.value)
    item, _ = rs.update("R001", {"disposition": "sold", "sale": COMPLETE_EBAY_SALE})
    assert item.disposition == "sold"


def test_sale_date_set_but_basis_unknown_is_refused(store):
    new()
    with pytest.raises(rs.Invalid):
        rs.update(
            "R001",
            {
                "disposition": "sold",
                "sale": {**COMPLETE_FB_SALE, "date_basis": "unknown"},
            },
        )


def test_disposition_sold_without_sale_block_is_refused(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"disposition": "sold"})
    assert "SALE_BLOCK_MISMATCH" in str(e.value)


def test_sale_block_without_sold_disposition_is_refused(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"sale": COMPLETE_FB_SALE})
    assert "SALE_BLOCK_MISMATCH" in str(e.value)


def test_available_needs_ask_price(store):
    with pytest.raises(rs.Invalid) as e:
        rs.create(minimal(price_ask=None))
    assert "ASK_PRICE_REQUIRED" in str(e.value)


def test_available_needs_condition(store):
    with pytest.raises(rs.Invalid) as e:
        rs.create(minimal(condition=None))
    assert "CONDITION_REQUIRED" in str(e.value)


def test_sold_needs_cost_basis(store):
    new(acquisition={})
    with pytest.raises(rs.Invalid) as e:
        sell()
    assert "ACQUISITION_REQUIRED" in str(e.value)


def test_kept_needs_a_date_and_void_a_reason(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"disposition": "kept"})
    assert "DISPOSITION_INCOMPLETE" in str(e.value)
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"disposition": "void", "disposition_date": TODAY})
    assert "DISPOSITION_INCOMPLETE" in str(e.value)


def test_acquisition_after_sale_is_refused(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        sell(date="2023-01-01")
    assert "DATE_ORDER" in str(e.value)


def test_refund_cannot_exceed_gross(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        sell(refund=99)
    assert "REFUND_EXCEEDS_GROSS" in str(e.value)


def test_sloppy_date_is_refused(store):
    with pytest.raises(rs.Invalid):
        rs.create(
            minimal(
                acquisition={
                    "date": "2024-3-1",
                    "date_basis": "estimate",
                    "price": 10,
                    "source": "msrp",
                    "confidence": "low",
                }
            )
        )


def test_bad_category_is_refused(store):
    with pytest.raises(rs.Invalid):
        rs.create(minimal(category="咖啡"))


def test_uid_is_immutable(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"uid": "R999"})
    assert "UID_IMMUTABLE" in str(e.value)


def test_dotted_patch_keys_nest(store):
    new()
    item, _ = rs.update("R001", {"acquisition.price": 55.5})
    assert item.acquisition.price == 55.5
    assert item.acquisition.source == "msrp"  # sibling survived the merge


def test_platform_status_writes_are_draft_delisted_sold_only(store):
    """We only ever hold drafts; the seller publishes himself. 'active' was written
    by nobody and guarded by a dead check — it is no longer a writable value."""
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"platforms.ebay.status": "active"})
    assert "STATUS_WRITE" in str(e.value)
    for s in ("draft", "delisted"):
        item, _ = rs.update("R001", {"platforms.fbmp.status": s})
        assert item.platforms["fbmp"].status == s


# --------------------------------------------------------------------------
# lifecycle — closing an item moves it to years/<year>/<uid>.yaml
# --------------------------------------------------------------------------


def test_sold_moves_record_to_years_and_deletes_the_folder(store):
    new()
    (rs.item_dir("R001") / "photos" / "a.jpg").write_bytes(b"x")
    item, rev = sell()
    assert not list((store / "items").glob("R001-*"))
    archived = store / "years" / "2026" / "R001.yaml"
    assert archived.exists()
    back, rev2 = rs.load("R001")
    assert back.sale.price == 25 and rev2 == rev


def test_kept_dispose_void_archive_by_disposition_year(store):
    for name, disp in [("One", "kept"), ("Two", "disposed"), ("Three", "void")]:
        item, _ = new(name_en=name)
        rs.update(
            item.uid,
            {
                "disposition": disp,
                "disposition_date": "2025-12-30",
                "disposition_reason": "r",
            },
        )
    assert sorted(p.name for p in (store / "years" / "2025").glob("R*.yaml")) == [
        "R001.yaml",
        "R002.yaml",
        "R003.yaml",
    ]
    assert list((store / "items").iterdir()) == [] or all(
        p.name.startswith(".") for p in (store / "items").iterdir()
    )


def test_uid_is_not_reused_after_archive(store):
    new()
    sell()
    item, _ = new(name_en="Next Thing")
    assert item.uid == "R002"


def test_archived_record_is_in_load_all_and_flagged(store):
    new()
    new(name_en="Still Listed")
    sell("R001")
    rows = {i.uid: i for i, _ in rs.load_all()}
    assert set(rows) == {"R001", "R002"}
    wave = {i.uid for i, _ in rs.load_all(archived=False)}
    assert wave == {"R002"}
    assert rs.view(rows["R001"])["archived"] is True
    assert rs.view(rows["R002"])["archived"] is False


def test_archived_record_accepts_a_field_fix_in_place(store):
    new()
    sell()
    item, _ = rs.update("R001", {"sale.fees": 1.5})
    assert item.sale.fees == 1.5
    assert (store / "years" / "2026" / "R001.yaml").exists()


def test_archived_record_moves_when_its_year_changes(store):
    new()
    sell()
    rs.update("R001", {"sale.date": "2025-11-02"})
    assert not (store / "years" / "2026" / "R001.yaml").exists()
    assert (store / "years" / "2025" / "R001.yaml").exists()


def test_archived_record_cannot_change_disposition(store):
    new()
    sell()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"disposition": "available", "sale": None})
    assert "ARCHIVED" in str(e.value)


def test_archived_sale_cannot_be_made_incomplete(store):
    new()
    sell()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"sale.fees": None})
    assert "TAX_INCOMPLETE" in str(e.value)


def test_archive_sweep_moves_legacy_closed_items(store, capsys):
    legacy_closed(store, "R005", disposition="kept", disposition_date="2026-08-01")
    legacy_closed(
        store,
        "R006",
        disposition="sold",
        acquisition={"price": 10},
        sale={**COMPLETE_FB_SALE},
    )
    new()  # R007, available — untouched
    rs.main(["archive"])
    out = capsys.readouterr().out
    assert '"archived": 2' in out
    assert (store / "years" / "2026" / "R005.yaml").exists()
    assert (store / "years" / "2026" / "R006.yaml").exists()
    assert [
        p.name for p in (store / "items").iterdir() if not p.name.startswith(".")
    ] == [rs.item_dir("R007").name]


def test_archive_sweep_refuses_an_incomplete_legacy_sale(store, capsys):
    legacy_closed(
        store,
        "R005",
        disposition="sold",
        acquisition={"price": 10},
        sale={"platform": "fbmp", "price": 5},
    )
    with pytest.raises(SystemExit) as e:
        rs.main(["archive"])
    assert e.value.code == 1
    assert "TAX_INCOMPLETE" in capsys.readouterr().err
    assert (store / "items" / "R005-legacy-thing").exists()


def test_check_flags_a_closed_item_still_in_items(store, capsys):
    legacy_closed(store, "R005", disposition="kept", disposition_date="2026-08-01")
    with pytest.raises(SystemExit):
        rs.main(["check"])
    assert "archive" in capsys.readouterr().err


def test_same_uid_in_items_and_years_is_a_conflict(store):
    new()
    (store / "years" / "2026").mkdir(parents=True)
    (store / "years" / "2026" / "R001.yaml").write_text("uid: R001\n")
    with pytest.raises(rs.Invalid) as e:
        rs.load_all()
    assert "R001" in str(e.value)


# --------------------------------------------------------------------------
# photo intake — verify, then delete the source; all-or-nothing
# --------------------------------------------------------------------------


def _jpg(path: Path, size=(40, 30), color=(200, 10, 10)) -> Path:
    from PIL import Image

    Image.new("RGB", size, color).save(path, "JPEG")
    return path


def _png(path: Path, size=(33, 21)) -> Path:
    from PIL import Image

    Image.new("RGB", size, (1, 2, 3)).save(path, "PNG")
    return path


def _heic(path: Path, size=(64, 48)) -> Path:
    from PIL import Image
    import pillow_heif

    pillow_heif.register_heif_opener()
    Image.new("RGB", size, (1, 2, 3)).save(path, "HEIF")
    return path


@pytest.fixture
def shoot(tmp_path):
    """A temp folder the seller names — outside the store."""
    d = tmp_path.parent / f"{tmp_path.name}-shoot"
    d.mkdir()
    return d


def test_intake_jpg_is_sha_verified_and_source_deleted(store, shoot):
    src = _jpg(shoot / "IMG_1.jpg")
    sha = rs._sha256(src)
    item, _, manifest = rs.create(minimal(), photos_from=[shoot])
    dest = rs.item_dir(item.uid) / "photos" / "IMG_1.jpg"
    assert rs._sha256(dest) == sha
    assert manifest["imported"][0]["sha8"] == sha[:8]
    assert not shoot.exists()  # emptied, so the folder is removed too


def test_intake_converts_heic_and_png_to_jpg_with_same_dims(store, shoot):
    _heic(shoot / "IMG_2.HEIC", (64, 48))
    _png(shoot / "shot.png", (33, 21))
    item, _, manifest = rs.create(minimal(), photos_from=[shoot])
    ph = rs.item_dir(item.uid) / "photos"
    assert sorted(p.name for p in ph.iterdir()) == ["IMG_2.jpg", "shot.jpg"]
    dims = {m["photo"].split("/")[-1]: m["dims"] for m in manifest["imported"]}
    assert dims == {"IMG_2.jpg": "64x48", "shot.jpg": "33x21"}
    assert not shoot.exists()


def test_intake_leaves_unsupported_files_and_keeps_the_folder(store, shoot):
    """Verify step 3 from the handoff: 1 jpg + 1 heic + 1 txt (+ a video, which moves)."""
    _jpg(shoot / "a.jpg")
    _heic(shoot / "b.heic")
    (shoot / "notes.txt").write_text("receipt")
    (shoot / "clip.mp4").write_bytes(b"\0")
    (shoot / ".DS_Store").write_bytes(b"\0")
    item, _, manifest = rs.create(minimal(), photos_from=[shoot])
    assert len(manifest["imported"]) == 2
    assert sorted(Path(p).name for p in manifest["left"]) == ["notes.txt"]
    assert sorted(p.name for p in shoot.iterdir()) == ["notes.txt"]


def test_intake_failure_deletes_nothing_and_creates_nothing(store, shoot, monkeypatch):
    _jpg(shoot / "a.jpg")
    _jpg(shoot / "b.jpg", color=(0, 0, 255))
    real = rs._sha256
    calls = {"n": 0}

    def flaky(p):
        calls["n"] += 1
        return "0" * 64 if Path(p).name == "b.jpg" and "photos" in str(p) else real(p)

    monkeypatch.setattr(rs, "_sha256", flaky)
    with pytest.raises(rs.Invalid) as e:
        rs.create(minimal(), photos_from=[shoot])
    assert "b.jpg" in str(e.value)
    assert sorted(p.name for p in shoot.iterdir()) == ["a.jpg", "b.jpg"]
    assert not list((store / "items").glob("R001-*"))


def test_intake_refuses_a_name_collision(store, shoot):
    _jpg(shoot / "IMG_3.jpg")
    _png(shoot / "IMG_3.png")
    with pytest.raises(rs.Invalid) as e:
        rs.create(minimal(), photos_from=[shoot])
    assert "IMG_3.jpg" in str(e.value)
    assert len(list(shoot.iterdir())) == 2


def test_intake_refuses_cloud_synced_folders(store, tmp_path):
    cloud = tmp_path / "Library" / "CloudStorage" / "GoogleDrive-x" / "My Drive"
    cloud.mkdir(parents=True)
    _jpg(cloud / "a.jpg")
    with pytest.raises(rs.Invalid) as e:
        rs.create(minimal(), photos_from=[cloud])
    assert "CLOUD_SOURCE" in str(e.value)
    assert (cloud / "a.jpg").exists()


def test_intake_accepts_individual_files(store, shoot):
    a = _jpg(shoot / "a.jpg")
    _jpg(shoot / "b.jpg")
    item, _, manifest = rs.create(minimal(), photos_from=[a])
    assert [p.name for p in rs.photos(item.uid)] == ["a.jpg"]
    assert sorted(p.name for p in shoot.iterdir()) == [
        "b.jpg"
    ]  # folder not empty, kept


def test_cli_new_prints_the_manifest(store, shoot, capsys):
    _jpg(shoot / "a.jpg")
    rs.main(
        [
            "new",
            "--name-en",
            "Thing",
            "--category",
            "misc",
            "--condition",
            "new",
            "--price-ask",
            "10",
            "--photos",
            str(shoot),
        ]
    )
    out = capsys.readouterr().out
    assert "a.jpg" in out and "✓" in out


# --------------------------------------------------------------------------
# photos at rest
# --------------------------------------------------------------------------


def test_photos_raises_on_heic(store):
    new()
    (rs.item_dir("R001") / "photos" / "R001_main_01.jpg").write_bytes(b"x")
    (rs.item_dir("R001") / "photos" / "IMG_1.HEIC").write_bytes(b"x")
    with pytest.raises(rs.Invalid) as e:
        rs.photos("R001")
    assert "IMG_1.HEIC" in str(e.value)


def test_photos_raises_on_mp4(store):
    new()
    (rs.item_dir("R001") / "photos" / "clip.mp4").write_bytes(b"x")
    with pytest.raises(rs.Invalid):
        rs.photos("R001")


def test_photos_accepts_uppercase_jpg(store):
    new()
    (rs.item_dir("R001") / "photos" / "IMG_4513.JPG").write_bytes(b"x")
    assert [p.name for p in rs.photos("R001")] == ["IMG_4513.JPG"]


def test_archived_item_has_no_photos(store):
    new()
    sell()
    assert rs.photos("R001") == []


# --------------------------------------------------------------------------
# load_all — never skips a broken file
# --------------------------------------------------------------------------


def test_load_all_reports_every_bad_file_not_just_the_first(store):
    new()
    new(name_en="Second Thing")
    (rs.item_dir("R001") / "item.yaml").write_text("category: misc\n")
    (rs.item_dir("R002") / "item.yaml").write_text("not: a valid item\n")
    with pytest.raises(rs.Invalid) as e:
        rs.load_all()
    joined = "\n".join(e.value.errors)
    assert "R001" in joined and "R002" in joined


def test_folder_without_item_yaml_is_illegal(store):
    (store / "items" / "R050-orphan-photos").mkdir()
    with pytest.raises(rs.Invalid) as e:
        rs.load_all()
    assert "intake/" in str(e.value)


def test_hand_named_folder_is_rejected(store):
    (store / "items" / "R050_Old_Style_CJK_中文").mkdir()
    with pytest.raises(rs.Invalid) as e:
        rs.load_all()
    assert "R<digits>-<ascii-slug>" in str(e.value)


def test_two_folders_for_one_uid_raise_not_pick_first(store):
    new()
    (store / "items" / "R001-duplicate-by-finder").mkdir()
    with pytest.raises(rs.Conflict):
        rs.item_dir("R001")
    with pytest.raises(rs.Invalid) as e:
        rs.load_all()
    assert "claim" in str(e.value)


def test_years_dir_ignores_non_record_files(store):
    new()
    sell()
    (store / "years" / "2026" / "tax.csv").write_text("x")
    (store / "years" / "2026" / "ebay_orders.json").write_text("[]")
    assert [i.uid for i, _ in rs.load_all()] == ["R001"]


# --------------------------------------------------------------------------
# optimistic lock
# --------------------------------------------------------------------------


def test_stale_rev_is_a_conflict(store):
    _, rev = new()
    rs.update("R001", {"price_ask": 30})  # someone else writes
    with pytest.raises(rs.Conflict) as e:
        rs.update("R001", {"price_ask": 99}, expected_rev=rev)
    assert "changed since you read it" in str(e.value)
    assert rs.load("R001")[0].price_ask == 30  # the stale write did NOT land


def test_matching_rev_is_accepted(store):
    _, rev = new()
    item, _ = rs.update("R001", {"price_ask": 30}, expected_rev=rev)
    assert item.price_ask == 30


def test_view_exposes_derived_fields(store):
    new()
    (rs.item_dir("R001") / "photos" / "R001_main_01.jpg").write_bytes(b"x")
    v = rs.view(rs.load("R001")[0])
    assert v["photos"] and v["tax"] is None and v["archived"] is False
    assert "route" not in v and "evidence" not in v and "listed" not in v
    assert "photos" not in rs.load("R001")[0].model_dump()  # derived, never stored


# --------------------------------------------------------------------------
# concurrency — real processes
# --------------------------------------------------------------------------


def _w_update(args):
    basedir, uid, n = args
    os.environ["RESALE_BASE"] = basedir
    sys.path.insert(0, str(RESALE_DIR))
    import resale_store as store_mod

    for _ in range(50):
        try:
            store_mod.update(uid, {"notes": f"writer {n} pid {os.getpid()}"})
            return os.getpid()
        except store_mod.Conflict:
            continue
    return 0


def _w_create(args):
    basedir, n = args
    os.environ["RESALE_BASE"] = basedir
    sys.path.insert(0, str(RESALE_DIR))
    import resale_store as store_mod

    item, _, _ = store_mod.create(
        {
            "name_en": f"Concurrent Thing {n}",
            "category": "misc",
            "condition": "used_good",
            "price_ask": 1,
        }
    )
    return item.uid, os.getpid()


@pytest.mark.slow
def test_200_concurrent_updates_to_one_item_leave_it_valid(store):
    new()
    ctx = mp.get_context("spawn")
    with ctx.Pool(8) as pool:
        results = pool.map(_w_update, [(str(store), "R001", i) for i in range(200)])
    assert all(results), "a writer gave up after 50 attempts"
    assert len(set(results)) > 1, f"only one worker process: {set(results)}"
    item, _ = rs.load("R001")  # parses => the file is not torn
    assert item.notes.startswith("writer ")
    assert len(rs.load_all()) == 1


@pytest.mark.slow
def test_20_concurrent_creates_get_20_distinct_uids(store):
    ctx = mp.get_context("spawn")
    with ctx.Pool(8) as pool:
        results = pool.map(_w_create, [(str(store), i) for i in range(20)])
    uids = [u for u, _ in results]
    pids = {pid for _, pid in results}
    assert pids != {os.getpid()}, "workers ran in-process — this proves nothing"
    assert len(pids) > 1, f"only one worker process: {pids}"
    assert len(set(uids)) == 20, sorted(uids)
    assert sorted(uids) == [f"R{i:03d}" for i in range(1, 21)]
    assert len(rs.load_all()) == 20


# --------------------------------------------------------------------------
# tax — refuses a partial worksheet; writes years/<year>/tax.csv
# --------------------------------------------------------------------------


def test_tax_refuses_when_a_legacy_sale_is_incomplete(store, capsys):
    legacy_closed(
        store,
        "R005",
        disposition="sold",
        acquisition={"price": 10},
        sale={
            "platform": "fbmp",
            "price": 5,
            "date": "2026-06-28",
            "date_basis": "exact",
        },
    )
    with pytest.raises(SystemExit) as e:
        rs.main(["tax", "--year", "2026"])
    assert e.value.code == 2
    out = capsys.readouterr().out
    assert "REFUSED" in out and "sale.received" in out
    assert not (store / "years" / "2026" / "tax.csv").exists()


def order(oid: str = "12-34567-89012", **kw):
    """One eBay order as Seller Hub shows it — what the 1099-K is built from."""
    o = {
        "date": "2026-07-02",
        "price": 40,
        "ship_charged": 8,
        "fees": 5.2,
        "ship_cost": 7.5,
        "refund": 0,
        "status": "completed",
        **kw,
    }
    args = ["order", oid]
    for k, v in o.items():
        args += ["--" + k.replace("_", "-"), str(v)]
    rs.main(args)


def tax_report():
    return rs.tax_report(2026)


def test_tax_computes_the_worksheet_and_writes_csv(store, capsys):
    new()
    sell()
    new(name_en="Second")
    rs.update("R002", {"disposition": "sold", "sale": COMPLETE_EBAY_SALE})
    order()
    capsys.readouterr()
    rs.main(["tax", "--year", "2026"])
    out = capsys.readouterr().out
    assert '"sales": 2' in out
    assert '"gross": 73.0' in out  # 25 + 40 + 8 shipping charged
    assert '"ebay": 48.0' in out  # the 1099-K cross-check number
    rows = list(csv.DictReader((store / "years" / "2026" / "tax.csv").open()))
    assert [r["uid"] for r in rows] == ["R001", "R002"]
    assert rows[0]["gain"] == "0.00"  # cost 89.99 > net 25 — a loss, never a gain
    assert rows[0]["offset"] == "0.00"  # FB cash: on no 1099-K, nothing to back out
    assert rows[1]["offset"] == "48.00"  # gross incl. shipping, not the 35.30 net
    assert '"schedule1_1099k_entry": 48.0' in out  # eBay only
    assert rows[1]["order_id"] == "12-34567-89012"


def _ebay_item(cost: float, price: float, received: float, source: str = "receipt"):
    acq = {**minimal()["acquisition"], "price": cost, "source": source}
    new(acquisition=acq)
    rs.update(
        "R001",
        {
            "disposition": "sold",
            "sale": {
                "platform": "ebay",
                "price": price,
                "received": received,
                "date": "2026-07-02",
                "date_basis": "exact",
                "order_id": "12-34567-89012",
            },
        },
    )
    return rs.tax_view(rs.load("R001")[0])


def test_offset_is_the_whole_1099k_gross_when_fees_turn_a_sale_into_a_loss(store):
    # gross 35 > cost 30, but fees leave 25 < cost: still a personal-use loss,
    # so all 35 on the 1099-K is backed out — min(gross, cost) would tax 5.
    t = _ebay_item(cost=30, price=35, received=25)
    assert (t["gain"], t["offset"]) == (0, 35)


def test_offset_never_goes_negative_when_label_exceeds_payout(store):
    t = _ebay_item(cost=299, price=46.24, received=0)
    assert t["offset"] == 46.24


def test_a_gain_item_has_no_offset(store):
    t = _ebay_item(cost=20, price=60, received=50)
    assert (t["gain"], t["offset"]) == (30, 0)


def test_cost_gate_refuses_a_sale_near_an_msrp_cost(store):
    # received 25 of an MSRP "cost" 30 (83%): a 17% discount would make it a
    # gain, so the real price paid is required before the sale is recorded.
    with pytest.raises(rs.Invalid) as e:
        _ebay_item(cost=30, price=35, received=25, source="msrp")
    assert "acquisition.real_cost" in str(e.value)


def test_cost_gate_passes_once_the_seller_gives_the_real_cost(store):
    t = _ebay_item(cost=30, price=35, received=25, source="seller")
    assert t["complete"]


def test_cost_gate_ignores_a_sale_far_below_msrp(store):
    t = _ebay_item(cost=100, price=65, received=59, source="msrp")
    assert t["complete"]


def test_cli_fb_sale_defaults_to_the_listed_price(store, capsys):
    """FB: whatever it was listed at is what it sold for, unless told otherwise."""
    new()
    _sold("--platform", "fbmp", "--date", "2026-06-28")
    s = rs.load("R001")[0].sale
    assert (s.price, s.received) == (25, 25)


def test_cli_ebay_sale_still_needs_a_price(store):
    new()
    with pytest.raises(SystemExit):
        _sold(
            "--platform",
            "ebay",
            "--received",
            "20",
            "--date",
            "2026-06-28",
            "--order",
            "12-34567-89012",
        )


def test_tax_only_counts_the_requested_year(store, capsys):
    new()
    sell(date="2025-12-31")
    rs.main(["tax", "--year", "2026"])
    assert '"sales": 0' in capsys.readouterr().out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def test_cli_exit_1_on_invalid(store):
    new()
    with pytest.raises(SystemExit) as e:
        rs.main(["set", "R001", "category=不存在的类目"])
    assert e.value.code == 1


def test_cli_exit_3_on_conflict(store):
    _, rev = new()
    rs.update("R001", {"price_ask": 30})
    with pytest.raises(SystemExit) as e:
        rs.main(["set", "R001", "price_ask=99", "--rev", rev])
    assert e.value.code == 3


def _sold(*args):
    rs.main(["sold", "R001", *args])


def test_cli_fb_sale_received_is_the_price(store, capsys):
    """FB is face-to-face cash: what the seller received IS the price."""
    new()
    _sold("--platform", "fbmp", "--price", "25", "--date", "2026-06-28")
    assert '"ok": true' in capsys.readouterr().out
    s = rs.load("R001")[0].sale
    assert (s.received, s.date_basis) == (25, "exact")
    assert rs.tax_view(rs.load("R001")[0])["net"] == 25


def test_cli_ebay_sale_needs_what_the_seller_actually_received(store, capsys):
    new()
    with pytest.raises(SystemExit) as e:
        _sold(
            "--platform",
            "ebay",
            "--price",
            "40",
            "--date",
            "2026-06-28",
            "--order",
            "1-2-3",
        )
    assert e.value.code == 1
    assert "sale.received" in capsys.readouterr().err
    _sold(
        "--platform",
        "ebay",
        "--price",
        "40",
        "--ship-charged",
        "8",
        "--received",
        "36.12",
        "--date",
        "2026-06-28",
        "--order",
        "1-2-3",
    )
    t = rs.tax_view(rs.load("R001")[0])
    assert (t["gross"], t["net"]) == (48, 36.12)


def test_cli_sold_date_is_required_and_approx_is_a_flag(store, capsys):
    new()
    with pytest.raises(SystemExit):
        _sold("--platform", "fbmp", "--price", "25")
    _sold("--platform", "fbmp", "--price", "25", "--date", "2026-06-28", "--approx")
    assert rs.load("R001")[0].sale.date_basis == "approx"


def test_cli_sold_refuses_an_already_sold_item(store, capsys):
    new()
    _sold("--platform", "fbmp", "--price", "25", "--date", "2026-06-28")
    with pytest.raises(SystemExit) as e:
        _sold("--platform", "fbmp", "--price", "30", "--date", "2026-06-29")
    assert e.value.code == 1
    assert "ALREADY_SOLD" in capsys.readouterr().err
    assert rs.load("R001")[0].sale.price == 25


def test_cli_set_keeps_text_as_text(store, capsys):
    """Values are YAML-parsed only for non-text fields: a description with
    'Condition: …' or a numeric model/eBay id stays a string."""
    new()
    desc = "Nice thing.\n\nCondition: used. Selling.\n\nIncludes: box."
    rs.main(
        [
            "set",
            "R001",
            f"description_en={desc}",
            "title_en=Foo: bar",
            "model=820",
            "platforms.ebay.status=draft",
            "platforms.ebay.code=358688715567",
            "price_ask=30",
            "notes=",
        ]
    )
    i = rs.load("R001")[0]
    assert i.description_en == desc and i.title_en == "Foo: bar"
    assert i.model == "820" and i.platforms["ebay"].code == "358688715567"
    assert i.price_ask == 30.0 and i.notes is None


def test_cli_set_bad_yaml_is_a_refusal_not_a_traceback(store, capsys):
    new()
    with pytest.raises(SystemExit) as e:
        rs.main(["set", "R001", "price_market={low: 1"])
    assert e.value.code == 1


def test_archive_sweep_checks_destinations_before_moving_anything(store, capsys):
    legacy_closed(store, "R005", disposition="kept", disposition_date="2026-08-01")
    legacy_closed(store, "R006", disposition="kept", disposition_date="2026-08-01")
    (store / "years" / "2026").mkdir(parents=True)
    (store / "years" / "2026" / "R006.yaml").write_text("uid: R006\n")
    with pytest.raises(SystemExit):
        rs.main(["archive"])
    assert (store / "items" / "R005-legacy-thing").exists()


def test_cli_ls_defaults_to_the_current_wave(store, capsys):
    new()
    new(name_en="Other")
    sell("R001")
    rs.main(["ls"])
    out = capsys.readouterr().out
    assert "R002" in out and "R001" not in out
    rs.main(["ls", "--all"])
    assert "R001" in capsys.readouterr().out


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------


def test_dims_with_decimals_are_accepted(store):
    item, _ = new(dims_in="12.5x8.5x4.5")
    assert item.dims_in == "12.5x8.5x4.5"


PICKUP = (
    "\n\nLocal pickup near the library. "
    "Free delivery within 20 miles if you buy $100+ or multiple items."
)


def test_check_refuses_delivery_text_on_an_available_item(store):
    item, _ = new(description_en="A nice thing." + PICKUP)
    problems = _check_problems()
    assert any("delivery-policy text" in p and item.uid in p for p in problems), (
        problems
    )
    assert any("references/list.md" in p for p in problems), problems


# --------------------------------------------------------------------------
# unknown fields: pydantic is extra="ignore", so the refusal is
# explicit — a silently dropped field is a write that reports success and
# loses data, which is the whole failure class this store exists to kill.
# --------------------------------------------------------------------------


def test_unknown_nested_field_is_refused(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"acquisition": {"cost_basis": 30}})
    assert "acquisition.cost_basis" in str(e.value)


def test_unknown_field_in_a_listing_is_refused(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update(
            "R001", {"platforms": {"ebay": {"status": "draft", "listing_id": "x"}}}
        )
    assert "platforms.ebay.listing_id" in str(e.value)


def test_unknown_dotted_key_is_refused(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"acquisition.cost_basis": 30})
    assert "UNKNOWN_FIELD" in str(e.value)


def test_a_known_field_set_to_null_still_works(store):
    """The unknown-field check must not turn explicit nulls into refusals."""
    new()
    item, _ = rs.update("R001", {"brand": None, "acquisition": {"note": None}})
    assert item.brand is None and item.acquisition.note is None


def test_stale_key_on_disk_still_loads(store):
    """extra='ignore': a dead key disappears lazily on the next write."""
    item, _ = new()
    p = rs.item_dir(item.uid) / "item.yaml"
    p.write_text(p.read_text() + "title_fb: an old value\n", encoding="utf-8")
    back, _ = rs.load(item.uid)
    assert not hasattr(back, "title_fb")


def _check_problems() -> list[str]:
    """Run the REAL `check` CLI against this tmp store and return its errors."""
    import json

    r = subprocess.run(
        [sys.executable, str(RESALE_DIR / "resale_store.py"), "check"],
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )
    if r.returncode == 0:
        return []
    payload = json.loads((r.stdout or r.stderr).strip().splitlines()[-1])
    return payload.get("errors", [])


def test_real_cost_can_be_backfilled_on_an_archived_sale(store, capsys):
    """The cost-gate fix in tax.md: `set` on a record already in years/."""
    _ebay_item(cost=30, price=35, received=25, source="seller")
    rs.main(["set", "R001", "acquisition.price=22", "acquisition.source=receipt"])
    t = rs.tax_view(rs.load("R001")[0])
    assert (t["gain"], t["offset"], t["complete"]) == (3, 0, True)


# --------------------------------------------------------------------------
# eBay orders: the 1099-K is built from orders, gain/loss from items
# --------------------------------------------------------------------------


def _ebay_sold(uid: str = "R001", **sale):
    rs.update(uid, {"disposition": "sold", "sale": {**COMPLETE_EBAY_SALE, **sale}})


def test_a_canceled_order_is_not_on_the_1099k(store):
    # Sold on FB the same day; the eBay order was canceled.
    new()
    sell()
    order(
        "11-11111-11111",
        price=95,
        ship_charged=19.7,
        fees=17.52,
        ship_cost=0,
        refund=97.58,
        status="canceled",
    )
    r = tax_report()
    assert r["problems"] == [] and r["schedule1_1099k_entry"] == 0


def test_a_refunded_order_with_no_item_is_still_backed_out(store):
    # eBay order refunded, never shipped; the watch sold on FB.
    new()
    sell()
    order(
        "22-22222-22222",
        price=365,
        ship_charged=6.37,
        fees=54.57,
        ship_cost=0,
        refund=316.8,
        status="refunded",
    )
    r = tax_report()
    assert r["problems"] == [] and r["schedule1_1099k_entry"] == 371.37
    assert [o["order_id"] for o in r["orders_without_item"]] == ["22-22222-22222"]


def test_a_sale_cannot_be_a_canceled_order(store):
    new()
    _ebay_sold()
    order(status="canceled")
    assert any("canceled" in p for p in tax_report()["problems"])


def test_a_completed_order_with_no_item_refuses_the_table(store):
    new()
    sell()
    order()
    assert any("12-34567-89012" in p for p in tax_report()["problems"])


def test_an_ebay_sale_with_no_order_refuses_the_table(store):
    new()
    _ebay_sold()
    assert any("not in ebay_orders.json" in p for p in tax_report()["problems"])


def test_record_and_order_must_agree_to_the_cent(store):
    new()
    _ebay_sold(price=15)
    order(price=14.95)
    assert any("price" in p for p in tax_report()["problems"])


def test_a_gain_on_ebay_leaves_the_1099k_line_for_form_8949(store):
    new(acquisition={**minimal()["acquisition"], "price": 10, "source": "receipt"})
    _ebay_sold()
    order()
    r = tax_report()
    assert r["schedule1_1099k_entry"] == 0
    assert r["form_8949"] == [{"uid": "R001", "gain": 25.3, "holding": "long"}]


def test_tax_refuses_while_orders_disagree(store, capsys):
    new()
    _ebay_sold()
    with pytest.raises(SystemExit) as e:
        rs.main(["tax", "--year", "2026"])
    assert e.value.code == 2
    assert not (store / "years" / "2026" / "tax.csv").exists()


def test_household_settings_come_from_config_yaml(store):
    new()
    _ebay_sold()
    assert rs.tax_view(rs.load("R001")[0])["on_1099k"] is True
    (store / "config.yaml").write_text("filing: single, Texas\nform_1099k: []\n")
    assert rs.tax_view(rs.load("R001")[0])["on_1099k"] is False
    assert rs.settings()["filing"] == "single, Texas"


def test_order_status_is_validated(store):
    with pytest.raises(SystemExit):
        order(status="returned")


# --------------------------------------------------------------------------
# correct: a closed record recorded wrongly (sold, but really donated)
# --------------------------------------------------------------------------


def test_correct_turns_a_wrong_sale_into_a_donation(store):
    new()
    sell()
    rs.main(
        [
            "correct",
            "R001",
            "--to",
            "disposed",
            "--date",
            "2026-07-20",
            "--reason",
            "donated to Goodwill",
        ]
    )
    item = rs.load("R001")[0]
    assert (item.disposition, item.sale) == ("disposed", None)
    assert item.disposition_reason == "CORRECTED from sold: donated to Goodwill"
    assert tax_report()["sales"] == 0


def test_correct_needs_a_reason(store):
    new()
    sell()
    with pytest.raises(SystemExit):
        rs.main(["correct", "R001", "--to", "disposed", "--date", "2026-07-20"])


def test_correct_cannot_make_a_sale(store):
    new()
    rs.main(["kept", "R001"])
    with pytest.raises(SystemExit):
        rs.main(
            ["correct", "R001", "--to", "sold", "--date", "2026-07-20", "--reason", "x"]
        )


def test_correct_only_touches_closed_records(store):
    new()
    with pytest.raises(SystemExit):
        rs.main(
            [
                "correct",
                "R001",
                "--to",
                "disposed",
                "--date",
                "2026-07-20",
                "--reason",
                "x",
            ]
        )


# --------------------------------------------------------------------------
# per-platform price + title cap
# --------------------------------------------------------------------------


def test_platform_price_is_stored_when_it_differs_from_ask(store):
    new(price_ask=400)
    item, _ = rs.update(
        "R001", {"platforms.fbmp.status": "draft", "platforms.fbmp.price": 390}
    )
    assert item.platforms["fbmp"].price == 390


def test_platform_price_equal_to_ask_is_dropped(store):
    """One fact, one place: a platform price that repeats price_ask is not kept."""
    new(price_ask=400)
    item, _ = rs.update(
        "R001", {"platforms.ebay.status": "draft", "platforms.ebay.price": 400}
    )
    assert item.platforms["ebay"].price is None


def test_fb_sale_defaults_to_the_fb_listing_price(store, capsys):
    new(price_ask=400, acquisition={**minimal()["acquisition"], "price": 1000})
    rs.update("R001", {"platforms.fbmp.status": "draft", "platforms.fbmp.price": 390})
    rs.main(["sold", "R001", "--platform", "fbmp", "--date", "2026-06-28"])
    item, _ = rs.load("R001")
    assert item.sale.price == 390


def test_ls_shows_platform_prices(store, capsys):
    new(price_ask=400)
    rs.update(
        "R001",
        {
            "platforms.fbmp.status": "draft",
            "platforms.fbmp.price": 390,
            "platforms.ebay.status": "draft",
            "platforms.ebay.price": 425,
        },
    )
    capsys.readouterr()
    rs.main(["ls"])
    out = capsys.readouterr().out
    assert "fb 390" in out and "eb 425" in out


def test_title_over_80_is_refused_at_write(store):
    with pytest.raises(rs.Invalid) as e:
        new(title_en="x" * 81)
    assert "TITLE_TOO_LONG" in str(e.value)
    new(title_en="x" * 80)


# --------------------------------------------------------------------------
# the record is the drafter's whole brief (R-RESALE-BRIEF-01)
# --------------------------------------------------------------------------


BRIEF = {
    "title_en": "SodaStream Terra",
    "description_en": "Works.",
    "weight_lb": 3,
    "dims_in": "12x9x6",
}


def _photos(uid: str, *names: str) -> None:
    for n in names:
        (rs.item_dir(uid) / "photos" / n).write_bytes(b"x")


def test_planned_listing_holds_a_price_before_any_draft_exists(store):
    new(price_ask=400, **BRIEF)
    item, _ = rs.update(
        "R001", {"platforms.fbmp.status": "planned", "platforms.fbmp.price": 390}
    )
    assert item.platforms["fbmp"].status == "planned"
    assert item.platforms["fbmp"].price == 390


def test_planned_listing_needs_the_text_it_will_draft_from(store):
    new()
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"platforms.fbmp.status": "planned"})
    assert "BRIEF_INCOMPLETE" in str(e.value) and "title_en" in str(e.value)


def test_planned_ebay_listing_needs_weight_and_box(store):
    new(**{k: v for k, v in BRIEF.items() if k not in ("weight_lb", "dims_in")})
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"platforms.ebay.status": "planned"})
    assert "weight_lb" in str(e.value) and "dims_in" in str(e.value)
    rs.update("R001", {"platforms.fbmp.status": "planned"})  # FB is pickup only


def test_platform_photo_order_is_kept_and_must_exist(store):
    new(**BRIEF)
    _photos("R001", "a.jpg", "b.jpg", "c.jpg")
    item, _ = rs.update(
        "R001",
        {
            "platforms.fbmp.status": "planned",
            "platforms.fbmp.photos": ["c.jpg", "a.jpg"],
        },
    )
    assert item.platforms["fbmp"].photos == ["c.jpg", "a.jpg"]
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"platforms.fbmp.photos": ["c.jpg", "zz.jpg"]})
    assert "PHOTO_MISSING" in str(e.value) and "zz.jpg" in str(e.value)


def test_platform_photos_cannot_repeat_or_exceed_the_platform_limit(store):
    new(**BRIEF)
    names = [f"{n:02d}.jpg" for n in range(11)]
    _photos("R001", *names)
    with pytest.raises(rs.Invalid) as e:
        rs.update(
            "R001", {"platforms.fbmp.status": "planned", "platforms.fbmp.photos": names}
        )
    assert "PHOTO_LIMIT" in str(e.value)
    with pytest.raises(rs.Invalid) as e:
        rs.update(
            "R001",
            {
                "platforms.fbmp.status": "planned",
                "platforms.fbmp.photos": ["00.jpg", "00.jpg"],
            },
        )
    assert "PHOTO_REPEAT" in str(e.value)


def test_planning_fb_with_more_than_10_photos_forces_the_pick(store):
    new(**BRIEF)
    names = [f"{n:02d}.jpg" for n in range(11)]
    _photos("R001", *names)
    with pytest.raises(rs.Invalid) as e:
        rs.update("R001", {"platforms.fbmp.status": "planned"})
    assert "PHOTO_PICK_REQUIRED" in str(e.value)
    rs.update(
        "R001",
        {"platforms.fbmp.status": "planned", "platforms.fbmp.photos": names[:10]},
    )


def test_platform_category_is_stored_verbatim(store, capsys):
    new(**BRIEF)
    rs.main(
        [
            "set",
            "R001",
            "platforms.fbmp.status=planned",
            "platforms.fbmp.category=Video Games",
        ]
    )
    item, _ = rs.load("R001")
    assert item.platforms["fbmp"].category == "Video Games"


def test_get_resolves_each_platforms_upload_set(store):
    new(**BRIEF)
    _photos("R001", "a.jpg", "b.jpg", "c.jpg")
    item, _ = rs.update(
        "R001",
        {
            "platforms.fbmp.status": "planned",
            "platforms.fbmp.photos": ["c.jpg", "a.jpg"],
            "platforms.ebay.status": "planned",
        },
    )
    v = rs.view(item)
    ph = rs.item_dir("R001") / "photos"
    assert v["upload"]["fbmp"] == [str(ph / "c.jpg"), str(ph / "a.jpg")]
    assert v["upload"]["ebay"] == [str(ph / n) for n in ("a.jpg", "b.jpg", "c.jpg")]


def test_check_flags_a_platform_photo_that_went_missing(store):
    new(**BRIEF)
    _photos("R001", "a.jpg", "b.jpg")
    rs.update(
        "R001", {"platforms.fbmp.status": "planned", "platforms.fbmp.photos": ["b.jpg"]}
    )
    (rs.item_dir("R001") / "photos" / "b.jpg").unlink()
    assert any("b.jpg" in p for p in _check_problems())


def test_closing_ignores_platform_photos_that_are_deleted_with_the_folder(store):
    new(**BRIEF)
    _photos("R001", "a.jpg")
    rs.update(
        "R001", {"platforms.fbmp.status": "planned", "platforms.fbmp.photos": ["a.jpg"]}
    )
    sell()
    assert rs.load("R001")[0].platforms["fbmp"].photos == ["a.jpg"]


# ---- videos move with the photos -----------------------------------------


def test_intake_moves_videos_into_videos_dir_after_verify(store, shoot):
    _jpg(shoot / "a.jpg")
    (shoot / "clip.MP4").write_bytes(b"\0video")
    (shoot / "walk.mov").write_bytes(b"\0mov")
    sha = rs._sha256(shoot / "clip.MP4")
    item, _, manifest = rs.create(minimal(), photos_from=[shoot])
    vd = rs.item_dir(item.uid) / "videos"
    assert sorted(p.name for p in vd.iterdir()) == ["clip.MP4", "walk.mov"]
    assert rs._sha256(vd / "clip.MP4") == sha
    assert sorted(r["video"].split("/")[-1] for r in manifest["videos"]) == [
        "clip.MP4",
        "walk.mov",
    ]
    assert manifest["left"] == []
    assert not shoot.exists()
    assert rs.view(item)["videos"] == [str(vd / "clip.MP4"), str(vd / "walk.mov")]


def test_video_verify_failure_deletes_nothing(store, shoot, monkeypatch):
    _jpg(shoot / "a.jpg")
    (shoot / "clip.mp4").write_bytes(b"\0video")
    real = rs._sha256
    monkeypatch.setattr(
        rs,
        "_sha256",
        lambda p: "0" * 64 if "videos" in str(p) else real(p),
    )
    with pytest.raises(rs.Invalid):
        rs.create(minimal(), photos_from=[shoot])
    assert sorted(p.name for p in shoot.iterdir()) == ["a.jpg", "clip.mp4"]
    assert not list((store / "items").glob("R001-*"))


def test_no_videos_no_videos_dir(store, shoot):
    _jpg(shoot / "a.jpg")
    item, _, _ = rs.create(minimal(), photos_from=[shoot])
    assert not (rs.item_dir(item.uid) / "videos").exists()
    assert rs.view(item)["videos"] == []
