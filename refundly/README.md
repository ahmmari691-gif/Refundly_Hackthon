# Refundly
English-language local prototype with a real Python rule engine and HTTP API. Python 3.9+; no pip installation or API keys required.

## Run
```sh
cd /Users/masha/Documents/Codex/2026-11-14/x20/outputs/depositback
python3 app.py
```
Open http://127.0.0.1:8000. Stop with Ctrl+C. Use `python3 app.py --port 8001` for a different port.

## Features
- Responsive three-step review, five state reference cards, per-deduction classification.
- Amount validation, deadline context, conditional remedies, unexplained withholding.
- Editable demand/follow-up letters, TXT download, browser PDF printing.
- Calendar reminder download. Sample case button.
- No persistence: refreshing clears entered data. API requests stay on localhost; optional Google Fonts requests do not contain form data.

## Scope
This is an informational demo, not legal advice or a production legal service. No payment processing, email sending, AI provider, or automatic email reminders is configured. Letters use deterministic templates. No fixed asset lifetimes are represented as law. Classifications rely on the user's description of wear/damage and do not adjudicate facts. Dispatch method, tenancy exemptions, historical effective dates, and city ordinances require individual review. Python's standard-library HTTP server is for local demonstration; use a production server and security review before public deployment.

Sources reviewed November 14, 2026: links in `app.py` and the UI. California direct statute retrieval returned 403; checked official California Courts guidance at https://selfhelp.courts.ca.gov/guide-security-deposits-california . Texas context: https://guides.sll.texas.gov/landlord-tenant-law/security-deposit-refunds . Illinois: official legislature ActID 2202. Rules are deliberately conservative; penalties are conditional text, not promised recovery.

## Tests
```sh
python3 -m unittest -v
```

## Version 2
The homepage is at `/`; the existing Python-backed review is at `/review.html`. Navy, ivory, and beige styling follows the supplied references. All functionality remains local; nothing is deployed. Lady Justice artwork was generated with the built-in ImageGen tool; see `ARTWORK.md` for its prompt.

## Refundly branding
Renamed to Refundly across both pages, letter downloads, print titles, and reminders. Original user-supplied logo: `static/assets/refundly-logo.jpg`. CSS frames its existing whitespace; artwork is unchanged.
