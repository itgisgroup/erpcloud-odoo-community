# Release evidence — 20.0.1.0.0

Prepared: 2026-11-03 (Asia/Saigon)

## Product and ownership

- Free app; no `price` key, paid activation, external API, or tracking.
- ERPCloud original source and artwork. LGPL-3 license text included.
- Declared dependency: Odoo standard `contacts` only.
- Market scan: [general phone search](https://apps.odoo.com/apps/modules/19.0/contact_search_by_phone) and [contact validation](https://apps.odoo.com/apps/modules/19.0/contact_validation) exist. This app's explicit scope is full Vietnamese mobile equivalence (`0`, `+84`, `0084`) without rewriting stored numbers.

## Tests

- Odoo 20 Community source commit `24b59ae7617e6b6ccf466d8b8cfebd541baa8b89`.
- Clean disposable database and only declared dependency, run with `..\tools\test-module.ps1 -Module vn_mobile_lookup` from this directory. Result: `0 failed, 0 error(s) of 5 tests`; log at `..\reports\vn_mobile_lookup-test.log`.
- Focused tests cover number forms, invalid input, computed-key refresh, country scope, `display_name` and `name_search`, and domain restriction.
- Separate disposable demo database: installed module, used synthetic contact, verified `0912345678` returns contact stored as `+84 912 345 678` in the real Contacts UI, captured genuine screenshots, then uninstalled the module. `UNINSTALL_PASS`: original phone remained unchanged.
- Test and demo databases are disposable. No production database was modified.

## Media

- `static/description/icon.png`, `cover.png`, `screenshot-contact.png`, `screenshot-search.png`.
- Social artwork, two-language captions, and screen-recording script at `../media/vn_mobile_lookup/`.

## Publication

Package with `..\tools\package-module.ps1 -Module vn_mobile_lookup` from this directory. Publisher repository registration and Odoo Apps listing verification require the ERPCloud publisher account. Confirm that the store accepts Odoo 20 before selecting this version for publication; no Odoo 19 compatibility is claimed.
