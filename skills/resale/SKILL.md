---
name: resale
description: "Sell your own used things: photos become eBay, Facebook Marketplace and Mercari drafts; when sales are final, record them and write the year's tax worksheet. resale_store.py is the only writer."
allowed-tools: [Read, Bash, Glob, Grep, AskUserQuestion]
---

# Resale

The seller is selling personal things they own, usually below what they paid. The
skill has two jobs:

| The seller says | Read |
|---|---|
| "list these" / a folder of photos / "edit the R1xx draft" | `references/list.md` |
| "these sold, update" / "do the tax table" | `references/tax.md` |

Everything else (publishing, repricing, withdrawing, deleting, messaging buyers,
meeting them) the seller does. Bookkeeping they report in chat: "took it off FB"
→ `set R0xx platforms.fbmp.status=delisted`; "keeping it" → `kept R0xx`.

## Setup, once

- **Data folder:** `$RESALE_BASE`, default `~/resale`. It holds `items/`, `years/`
  and `config.yaml`. Keep it in a private git repo if you want history.
- **`config.yaml`** in the data folder. Ask the seller for anything missing and
  write it there (it is a plain file):
  ```yaml
  filing: single, Texas            # printed on the tax report
  form_1099k: [ebay]               # platforms that send the seller a 1099-K
  pickup_text: "Pickup at <a public place near you>."   # appended on Facebook only
  ```
- **The store**, in this skill's folder: `scripts/resale_store.py`. Always run it
  with its full path: `uv run <skill folder>/scripts/resale_store.py <cmd> …`
  (`uv` installs its dependencies; `…` in the references means this command).
- **Dashboard:** `uv run <skill folder>/scripts/dashboard/server.py`, then open
  `http://127.0.0.1:8377` (for sale) or `#tax` (sold and tax).

## Two invariants

1. **`resale_store.py` is the only writer** of `items/*/item.yaml` and
   `years/*/R*.yaml`. The plugin's hook blocks Edit, Write and shell redirects onto
   them. A non-zero exit means the write was refused: show the seller stderr and fix
   the input; never retry with altered values.
   Commands: `new | get | ls | set | sold | kept | dispose | void | correct | check | tax | order`.
2. **Never guess.** Unknown condition, category, model, cost, date or fee → look it
   up in the browser, then ask. No comparable sales → show what you found and let
   the seller decide. The store refuses incomplete sales and tax tables on purpose.

## Browser

- Use a browser that is already signed in to eBay and Facebook: this plugin's
  `resale-browser` (Playwright with a persistent profile; the seller signs in once
  in the window it opens), or the app's built-in browser pane. A pane without a
  file-upload tool can fill the text and leave the photos to the seller.
- Find elements by role and name, or a CSS selector, from a fresh snapshot. Never
  reuse a ref; refs change after every upload and page load.
- Per session: at most 15 eBay drafts and 20 Facebook drafts. Captcha or a block →
  stop and tell the seller.
- Read numbers (fees, shipping, order ids) off the seller pages, never from memory.
- Upload straight from `items/<uid>-*/photos/` and `videos/`.

## Other platforms (only when the seller asks)

- **Mercari:** ships nationwide, no local pickup.
- **Swappa:** catalog-only categories (phones, tablets, laptops, watches, some cameras).
- **Fred Miranda:** camera gear; one Buy & Sell post can hold several items and
  posting needs a paid membership. Vet every buyer with `references/fm-buyer-vetting.md`
  before the seller replies.
