# Tax — sweep what sold, then write the year's table

The seller triggers this only when every sale is final. The platforms say what sold,
the store records it, the table comes out of the store. `…` = the store command.

**Net = what actually reached the seller.** eBay collects the buyer's payment,
keeps its fees, label and sales tax, and pays out the rest — that payout is
`--received`. FB is face-to-face cash: received = price, nothing to enter.

## 1. Collect every sale (read-only)

- **eBay** — Seller Hub → Orders (`https://www.ebay.com/sh/ord`), the whole year,
  **every order including canceled and refunded ones**. Open each order page
  (`https://www.ebay.com/mesh/ord/details?orderid=<id>`) and record it — the
  order ledger is what the 1099-K is built from, separate from the items:
  ```
  … order 12-34567-89012 --date 2026-10-02 --price 89 --ship-charged 9.50 \
        --fees 12.08 --ship-cost 10.00 --refund 0 --status completed --title "…"
  ```
  `--status` is the page's heading: `completed`, `partially_refunded`, `refunded`
  or `canceled`. Canceled = off the 1099-K; refunded = still on it, even if the
  thing never shipped and sold elsewhere (then record the item's real sale).
- **FB** — `https://www.facebook.com/marketplace/you/selling`, filter Sold; the
  Marketplace inbox for the agreed price and date.
- Anything else the seller mentions (local, Fred Miranda, rednote) — ask price and date.

## 2. Match each sale to a record

`… ls --json` lists the current wave. Match by title + price; no match or two
candidates → ask the seller. One order covering several items: split price and
payout across the uids so they add up to the order, and give each `--lot <name>`.

## 3. Record

The record needs `acquisition.price` first (ask the seller if missing; add
`acquisition.date` too if they know it).

**Cost gate (the store enforces it).** `sold` and `tax` refuse with
`missing: acquisition.real_cost` when the cost is `msrp`/`estimate` and they received
≥ 60% of it — a discount they likely got could make it a taxable gain. Ask the seller
what they actually paid (after discounts, + sales tax + shipping) and where the
proof is, then `… set R0xx acquisition.price=<paid> acquisition.source=seller`
(`order_page`/`receipt` if you read it off one). Never pick a number yourself.
Ask through the dashboard, not chat: start `uv run python
<skill folder>/scripts/dashboard/server.py`, open `http://127.0.0.1:8377/#tax` — the
"Add the real purchase price" box lists every gated item; the seller fills what they paid and presses
"Copy for Claude", which pastes the exact `set` commands back. Run them, re-run `tax`.
If a pasted number equals the item's sale price, they answered the wrong question —
ask again before writing.

Then:

```
… sold R1xx --platform ebay --price 89 --ship-charged 9.50 --received 76.42 \
      --date 2026-10-02 --order 12-34567-89012
… sold R1xx --platform fbmp --date 2026-10-04          # FB: price = price_ask
… sold R1xx --platform fbmp --price 100 --date 2026-10-04  # only if they took less
```

Add `--approx` only if the date is a best recollection. `sold` refuses anything
incomplete, then moves the record to `years/<year>/` and deletes its photos.
Not sold but done: `kept R1xx`, or `dispose R1xx --reason …`.
Recorded wrongly after closing (e.g. "sold" but really donated):
`… correct R1xx --to disposed --date <day> --reason "donated to Goodwill"` —
closed → kept/disposed/void only; the reason keeps what it was before.

## 4. Table and cross-check

`… tax --year 2026` refuses (exit 2) while any sale is incomplete or the order
ledger and the items disagree: an eBay sale with no order, a sale pointing at a
canceled order, a shipped order no item records, or any amount off by a cent.
Otherwise it writes `years/<year>/tax.csv` and prints the report.

**Where it goes.** Filing status and state come from `config.yaml`. `tax` prints the
numbers; nothing here is computed by hand:
- `schedule1_1099k_entry` — federal, the 1099-K line at the top of Schedule 1
  (TY2024+; confirm it is still there on the new year's form). The gross of every
  non-canceled eBay order, minus the gross of gain sales. `orders_without_item`
  lists the refunded orders in it that no item sold through.
- `form_8949` — every sale with a gain, any platform. Empty = no 8949.
- FB / local / rednote losses: on no 1099-K, not reported (Schedule D instr.).
- State returns: some states issue their own 1099-K at a lower threshold; back it
  out the same way and check the state's instructions before filing.

When eBay's 1099-K arrives, compare its gross with `ebay_orders.gross` and show
the seller the gap (both exclude the sales tax eBay collected). A gap means an order
missing from the ledger or a wrong status. Report: sales recorded (uid · platform · price ·
received), year totals, the 1099-K comparison, anything still open.
