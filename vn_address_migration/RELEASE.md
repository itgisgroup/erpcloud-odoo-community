# Pilot 02 candidate — 20.0.1.0.0

Source: `data/odoo20/odooapps/vn_address_migration/`.
Working branch: `feature/pilot02-vn_address_migration` in `.pilot-checkouts/erpcloud-odoo-community`.
Scope: Odoo 20 Community, Free, LGPL-3, direct dependency `contacts`.
Not published; final QA and Release remain with the factory Lead.

## Implementation

- Offline 10,602-row Vietnamese old ward to new ward mapping. Source and known 90 key-derived names are documented in `data/DATA_NOTES.md`.
- Scan creates proposals; it never edits contacts. Divided and ambiguous matches require review. Applying uses the selected candidate mapping, checks both migration and contact write access, and records actor and time. Audit records cannot be deleted.
- Odoo 20 security uses `res.groups.privilege` and `ir.access`; the global company restriction remains in force. Odoo 20 list views and dynamic form expressions replace removed `tree` and `attrs` syntax.
- A migration manager also needs Contacts edit permission (`base.group_partner_manager`) to apply a proposal; the module does not grant that permission implicitly.

## Automated QA — passed 2026-11-09

Command from `erpcloud-apps` root:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File data\odoo20\odooapps\tools\test-module.ps1 -Module vn_address_migration

Clean disposable DB `odooapps_vn_address_migration_test`: module install and 8 post-install tests, 0 failures, 0 errors. Log: `data/odoo20/odooapps/reports/vn_address_migration-test.log`.

The tests cover direct, divided, ambiguous and unmatched scans; source preservation before apply; selected candidate application; audit/no deletion; normalisation; and permissions for ordinary and manager users.

## Remaining release gates

- Manual desktop and mobile scan → review → apply → audit check.
- Review 90 source rows with key-derived names and decide publish treatment.
- Release packages the reviewed Git commit and ZIP, then publishes through the portal workflow. This candidate has not been published.
