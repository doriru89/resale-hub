# Fred Miranda — vet a buyer before replying

Read when a buyer PMs or replies on an FM thread (or the seller asks "is this buyer
OK?"). Everything below is public on FM once logged in; read it with Playwright,
never from memory. Output: a table of the six checks + one verdict line.
The seller decides; unvetted buyers get no reply.

## Where the data is

| Data | URL |
|---|---|
| Profile: registered, posts, city, feedback Great/Fair/Poor | `/forum/viewprofile.php?Action=viewprofile&username=<name>` |
| Every feedback: reviewer, date, source thread | `/forum/feedback/<uid>/<page>` (uid is in the profile's feedback table `onclick`) |
| Recent posts, with dates | `/forum/recent/<name>/` |

How feedback works (FM topic 638369): both sides must post in the sale thread;
one feedback per unique member ("member-based, not transaction-based"). FM does
not verify a sale happened — sock-puppet accounts can trade feedback, so the
reviewers must be checked too.

## The six checks

| # | Check | Pass |
|---|---|---|
| 1 | Account age | registered ≥ 3 years ago |
| 2 | Feedback | ≥ 20 Great, 0 Poor |
| 3 | Recency | ≥ 1 feedback in the last 12 months |
| 4 | Reviewers are real | spot-check 3 reviewers: each registered years ago, own feedback ≥ 10 |
| 5 | Consistent history | recent posts match their interests and city; no gap of 2+ years followed by a sudden high-value buy (hijacked-account pattern); feedback spread across years, not bunched in a few weeks |
| 6 | Conduct (in PM) | stays on FM PM; ships to their PayPal address; no rush, no overpayment, no "my assistant", no off-site email |

Any fail on 1–2 → ignore. A fail on 3–6 → show the seller; they decide.

## Deal flow once vetted

Local (preferred): cash, meet at a bank branch, teller checks the bills.
Shipped: video call showing lens + serial → buyer pays PayPal G&S to the listed
price → record the packing on video with the serial visible → insured, tracked
shipping with signature to the PayPal transaction address → trade FM feedback in
the thread.
