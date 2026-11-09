# Pilot candidate — 20.0.1.0.0

Source: `data/odoo20/odooapps/vn_delivery_address_copy/`.

Scope: Odoo 20 Community, Free, LGPL-3, `contacts` only. No publisher push or publication. Independent QA, desktop/mobile clipboard checks, ZIP validation, portal content, and release approval remain separate gates.

The model tests cover order and separators, whitespace and missing values, a name-only contact, individual and company contacts, each source field, related state/country names, and preservation of source fields.

## Developer verification — 2026-11-09

- Command: `& .\data\odoo20\odooapps\tools\test-module.ps1 -Module vn_delivery_address_copy` from the workspace root. The script resets and removes only `odooapps_vn_delivery_address_copy_test`.
- Build: local Odoo 20 source in `odoo-20.0/`; module version `20.0.1.0.0`; direct dependency `contacts`.
- Result: clean install passed; three `TestDeliveryAddressCopy` methods started; `0 failed, 0 error(s) of 3 tests`. The database was removed by the script.
- Log: `data/odoo20/odooapps/reports/vn_delivery_address_copy-test.log`.
- Core widget confirmed in `odoo-20.0/addons/web/static/src/views/fields/copy_clipboard/copy_clipboard_field.js` and its XML template. The widget only renders its copy button for a nonempty value.

Uninstall, browser clipboard behavior, independent QA, screenshots, and publication remain unverified.
