# List — photos → price → description → eBay + FB drafts

Output: one record in `items/` and a saved, read-back draft on eBay and on FB.
The seller publishes. `…` below = the store command from SKILL.md.

**The record is the drafter's whole brief.** Steps 1–4 decide everything with
the seller and write it with `new`/`set`; steps 5–6 read it back with `… get R1xx`
and nothing else. A decision that lives only in chat never reaches the form.

## 1. Identify

The seller names a temp folder of photos. One folder per item — if it mixes items,
sort them into `<folder>/_resale/<item>/` first (`new --photos` deletes sources).
Identify the item from them (labels, model
numbers); ask when brand, model, variant or condition tier is unclear. Ask for
cost and purchase date if they know them (order page, receipt); otherwise leave
them — the tax sweep asks again. **Exception:** once the ask price is set (step 2),
if it is ≥ 60% of MSRP, ask now for what they actually paid (after discounts, plus
sales tax and shipping) — otherwise the store's cost gate stops the sale later.

## 2. Price

Sources, all read-only:
1. **Terapeak** (Seller Hub → Research, logged in):
   `https://www.ebay.com/sh/research?marketplace=EBAY-US&keywords=<brand model>&dayRange=90&tabName=SOLD&limit=50`
   — widen `dayRange` to 180/365 when there are few rows.
2. **Used prices elsewhere**, by web search — always, not only when
   Terapeak is thin: Swappa, MPB, KEH, Camera West, Reddit. Retail used prices
   bound the top; a 2nd source catches a skewed Terapeak window.
3. **eBay public sold search** (few Terapeak rows): `https://www.ebay.com/sch/i.html?_nkw=<query>&LH_Sold=1&LH_Complete=1`
   in the logged-in browser. Go slow; captcha → stop and ask.

Method:
- Classify each row by title: `new/sealed · used-clean · defect · wrong-variant`.
  Only the exact variant and condition count. URL condition filters don't filter.
- Normalize to buyer all-in (price + shipping; Terapeak's average excludes shipping).
- **Ask = median all-in − our shipping (~$8–11 for a ≤2 lb parcel), rounded down to a 9.**
- **Floor = 25th percentile** — below it is a giveaway price; don't go there.
- **Ceiling = volume sellers' free-shipping price** — they win every tie.
- No "complete in box" premium on commodity electronics.
- High-value gear: FB / Fred Miranda ≈ MPB Excellent × 0.8; eBay = that figure
  grossed up for eBay fees.
- Zero usable comps → show what you found; the seller decides.
- Check platform restrictions (e.g. Huawei audio cannot be sold on eBay).

Show the seller the classified table (listing · price · shipping · class · all-in) and
the proposed ask **before** writing. The record holds one `price_ask` and
`price_market: {low, high}` (p25–p75); a platform priced differently gets
`platforms.<ebay|fbmp>.price=N` in step 4 (a repeat of `price_ask` is dropped;
`ls` shows `[fb 390 eb 425]`).
Platforms are per item: eBay for shippable things; FB-only when a return would
hurt (phones, drones with wear). FB ask ≤ eBay net (eBay price × 0.87) — if the
eBay net is higher, raise FB.

## 3. Title and description

- `title_en` is the one title for every platform, ≤80 chars (eBay limit; the
  store refuses longer), brand + model + key variant first.
- `description_en` skeleton (60–90 words under $100, 80–120 to $500, 100–150 above):

```
<Product name + the one thing that sets it apart>

- <spec>
- <spec>
- <spec, if needed>

Condition: <honest, specific>. <Why selling — "upgrading to the X", "consolidating my camera kit">.

Includes: <exact contents>.

Happy to take more pictures.
```

- Quote MSRP only if the item is still sold new at that price or was discontinued
  recently; otherwise use market framing ("comparable used ones sell $X–Y").
- $500+: add "Zelle, Venmo, PayPal, or cash."
- No pickup/delivery text in `description_en` (`check` refuses it) — FB adds it on the form.
- Plain words: "is"/"has", no adjective triplets, at most one em dash.
- Show the seller the title and description before creating the record.

## 4. Write the brief

```
… new --name-en "Shokz OpenRun Pro 2" --category headphones --condition used_good \
      --price-ask 99 --set brand=Shokz model=S820 weight_lb=0.8 dims_in=10x8x6 \
      title_en="…" description_en="…" --photos /path/to/temp-folder
… set R1xx platforms.ebay.status=planned platforms.fbmp.status=planned \
      platforms.fbmp.price=89 "platforms.fbmp.photos=[a.jpg, c.jpg, …]" \
      "platforms.fbmp.category=Video Games"
```

- `--category` / `--condition` are the schema's enums (`new, open_box, used_good,
  acceptable, parts`).
- `dims_in` is the **shipping box, one standard size up; product size is only the
  floor**. If the seller reuses shipping boxes, take the smallest standard box that fits,
  then go one size up in the same row. Flat items (laptops, keyboards, frames) go
  one size up within the flat row. Under-stated dims → they pay the difference at
  drop-off.
  - cube-ish: 8×6×6 · 10×8×6 · 12×9×6 · 12×10×8 · 12×12×8 · 15×12×10 · 16×12×12 ·
    18×14×12 · 20×16×12 · 24×18×18
  - flat: 14×10×4 · 16×10×4 · 18×12×4
- `new --photos`: `.jpg` copied and sha256-checked; `.heic`/`.png` become `.jpg`
  with dimensions checked; `.mp4`/`.mov` go to `videos/` (git-ignored), sha256-checked.
  Sources are deleted only after every file passed; an emptied folder is removed;
  Google Drive folders are refused. Paste the printed ✓ manifest to the seller as
  their receipt. `LEFT IN PLACE` files → ask them.
- `platforms.<p>.status=planned` = the seller chose that platform; no draft yet. The
  store refuses it until the brief is complete: `title_en`, `description_en`, and
  for eBay `weight_lb` + `dims_in`; more photos than the form takes (FB 10, eBay
  24) → `platforms.<p>.photos` is required — the pick in upload order, names from
  `photos/`. Absent = every photo in name order. FB: each photo shows something
  different (overview, every angle, defects, accessories), no near-duplicates.
- `platforms.fbmp.category` only when it isn't the obvious pick for the item.
- Dispatch the drafter with just `draft R1xx on ebay, fbmp`. A change while it runs
  is a `set`, then "re-read R1xx" — never a correction by message.

## 5. eBay draft

Run `… get R1xx` before starting the form; every value below comes from it.

1. `https://www.ebay.com/sl/prelist/home` → search `<brand> <model> <type>`.
2. Pick the closest catalog match (same brand + model; for model kits the grade
   must match) or "Continue without match".
3. Condition dialog — read the options that exist: `new`→New; `open_box`→Open box,
   else New other, else Used + "Open box, never used" in condition description;
   `used_good`/`acceptable`→Used; `parts`→For parts or not working. Other scales (video games, shoes) → pick the
   obvious tier or ask.
4. Form, in this order (photo upload invalidates every ref — re-snapshot after it):
   - Photos: "Upload from computer", `upload.ebay` in one `browser_file_upload`;
     a video from `videos` too (≤1 min).
   - Title: replace the prefilled one with `title_en` (`input[name='title']`).
   - Condition description (used only, `textarea[name='itemConditionDescription']`):
     the Condition/Includes lines.
   - Description: `browser_type` natively into the textbox inside
     `iframe[name="se-rte-frame__summary"]` (setting innerHTML is discarded on save).
     Body = `description_en` without the Condition line. Then click the title field
     to blur, so the hidden `textarea[name='description']` syncs.
   - Price: `platforms.ebay.price`, else `price_ask`; Buy It Now.
   - Item specifics: fill only the required `*` ones, from the record. Brand, MPN
     and Model come from `brand`/`model` — overwrite what the catalog or a seller
     match prefilled (they are often wrong), clear what the record doesn't know.
     Never "Apply all".
   - Shipping: calculated. Overwrite weight (`[aria-label='Enter weight in pounds']`
     / `…ounces`) and dims (`…package length|width|depth in inches`) from
     `weight_lb`/`dims_in`.
5. "Save for later" (never "List it"). The draft id is in the form URL.
6. **Reopen and read back**: `https://www.ebay.com/sl/list?mode=AddItem&draft_id=<id>`
   — title, price, condition, brand, and a non-empty description. Only then record:

```
… set R1xx platforms.ebay.status=draft platforms.ebay.date=YYYY-MM-DD \
      "platforms.ebay.url=https://www.ebay.com/sl/list?mode=AddItem&draft_id=<id>"
```

## 6. FB Marketplace draft

Run `… get R1xx` again before this form — the record may have changed.

1. `https://www.facebook.com/marketplace/create/item`, form
   `[role='form'][aria-label='Marketplace']`.
2. "Add photos": `upload.fbmp` in one upload, in that order. Every file in
   `videos`: add it on the edit page after the first save, make it the first media
   item (buyers see it while swiping), and wait ~2 min before read-back — FB is
   still processing it.
3. Title = `title_en`. Price = `platforms.fbmp.price`, else `price_ask` (integer). Description =
   `description_en` + blank line + `pickup_text` from `config.yaml` (ask once if it
   is missing; pickup only, no delivery).
4. Category: combobox "Category" → dialog `[role='dialog'][aria-label='Drop-down menu']`.
   `platforms.fbmp.category` if set; else the obvious one (phone accessories go
   under Mobile phones). Unsure → stop and report; the main session asks the seller.
5. Condition: `new`→New, `open_box`→Used - like new, `used_good`→Used - good,
   `acceptable`/`parts`→Used - fair (say "for parts" in the title).
6. "Save Draft" (enabled once title, price, category and condition are set).
7. On `https://www.facebook.com/marketplace/you/selling` get the id:
   `[...document.querySelectorAll('a[href*="listing_id"]')]` filtered by the title.
   Open `https://www.facebook.com/marketplace/edit/?listing_id=<id>` and read the
   fields back (photo count and order too), then:

```
… set R1xx platforms.fbmp.status=draft platforms.fbmp.date=YYYY-MM-DD \
      "platforms.fbmp.url=https://www.facebook.com/marketplace/edit/?listing_id=<id>"
```

## 7. Editing a draft later

Open it by its stored url (eBay Resume link / FB edit link), change the fields,
save, reopen and read back — the same proof as creating it. Record price or text
changes with `set`.

## Report

Steps 5–6 run in a fresh subagent (browser work eats context), briefed with only
uid + platforms; the main session then reopens every draft itself and checks it
against `get` — the drafter doesn't sign off its own work. One table per session: uid · title · eBay draft ✓/✗ · FB draft ✓/✗ · price(s) ·
anything the seller must decide.
