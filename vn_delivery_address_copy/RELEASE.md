# Pilot candidate — 20.0.1.0.1

Source: `data/odoo20/odooapps/vn_delivery_address_copy/`.

Scope: Odoo 20 Community, Free, LGPL-3, direct dependency `contacts`. The publisher branch and portal are outside this pilot commit.

## Developer checks — 2026-11-09

- `& .\data\odoo20\odooapps\tools\test-module.ps1 -Module vn_delivery_address_copy` passed on disposable database `odooapps_vn_delivery_address_copy_test`: three post-tests, zero failures or errors. The script removed the database. Log: `reports/vn_delivery_address_copy-test.log`.
- Odoo core's `CopyClipboardChar` supplies the copy button and clipboard content. Version 20.0.1.0.1 adds scoped CSS to wrap the displayed address without changing the copied value. CSS source commit: `5d19f7ecd3b9a8fd5571b8e4006ca824af42e7c9`.
- The disposable QA UI database was upgraded to 20.0.1.0.1. Its owner reported the browser script passed desktop and mobile. Agent A inspected the fresh form-sheet screenshots and confirmed that the full address is visible at both widths. Independent QA must rerun against the final media/source commit; the browser pass here is not an independent QA sign-off.

## Media provenance

- `icon.png` and `cover.png` are original illustrations generated for this module with the built-in image generator: a contact card and address line flowing to a clipboard, violet/coral/ivory palette, without logos or third-party UI. They are artwork, not screenshots.
- `screenshot_contact_desktop.png` and `screenshot_contact_mobile.png` were copied unchanged from `reports/qa-browser/pilot-contact-sheet-{desktop,mobile}.png` captured after the CSS fix on the disposable Odoo 20 QA database. Both show the complete address and the core copy confirmation. The contact names include `(QA)` to make synthetic data clear.
- `screenshot_no_address.png` was copied unchanged from the fresh `reports/qa-browser/pilot-empty-desktop.png`. It shows the empty-address message and no copy button.
- No customer data is used. The source browser images and script remain in `reports/qa-browser/`, outside the addon package.

Previous independent QA of commit `fdd973e8` passed clean install, model logic and uninstall, but reported truncated UI text and missing media. The truncation and media are addressed in this candidate. The final commit still needs independent QA, package/ZIP verification, and release approval before publication.
