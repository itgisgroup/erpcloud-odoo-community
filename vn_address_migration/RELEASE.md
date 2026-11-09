# Pilot 02 candidate — 20.0.1.0.0

Source: `data/odoo20/odooapps/vn_address_migration/`.
Working branch: `feature/pilot02-vn_address_migration` in
`.pilot-checkouts/erpcloud-odoo-community` (branched from `20.0`).

Scope: Odoo 20 Community, Free, code LGPL-3, direct dependency `contacts`.
Not published; QA and Release remain with the Lead.

## What was built (FR-01..FR-06)

- `vn.address.mapping`: old ward → new ward + new province, `classification`
  (unchanged/renamed/merged/divided), `phan` (full/partial),
  `is_default_new_ward` (divided 1→many), resolution source fields.
- `vn.address.migration`: proposal + review queue + immutable audit. Snapshots
  old street/street2/city/state/country/zip, holds proposed city/state, the
  chosen mapping and candidate list; states draft/review/applied/skipped.
- Scan (`_scan_partners`): offline, from packaged data, batch or single. Direct
  (single unambiguous row) → draft; divided/ambiguous → review with candidates
  and default flag; no match → review/unmatched. Never writes source until apply.
- Apply (`action_apply`): writes only mapped `city`/`state_id` after an explicit
  user action; checks write access on the migration and on the contact (ACL).
  Records `applied_uid`/`applied_date`. `unlink` is blocked (audit trail).
- Security: user/manager groups, `ir.model.access` (read+create for internal
  users; write for managers; no unlink), multi-company record rule. The addon
  never escalates permissions.
- Views: menu under Contacts (Quét địa chỉ / Hàng đợi rà soát / Mapping cũ→mới),
  tree+form for both models, scan wizard.

## Data — FINAL (Release confirmed 2026-11-09)

`data/vn.address.mapping.csv` is the authoritative 10,602-row dataset
(unchanged 149 / renamed 92 / merged 9,328 / divided 1,033) replacing the 6-row
sample. Source confirmed by Release: `undertheseanlp/address` (Apache-2.0,
Hugging Face) on top of `vietnamadminunits` v1.0.4 (MIT, PyPI); legal basis:
National Assembly resolutions (01/07/2025), per-province Standing Committee
resolutions and Decision 19/2025/QĐ-TTg. 90 rows have key-derived names flagged
for QA backfill; `source_resolution`/`source_clause` and ward codes are empty
(source does not provide them). See `data/DATA_NOTES.md`.

## Test status — BLOCKED (not executed here)

Model tests are written in `tests/test_vn_address_migration.py` (8 tests: merge
direct, divided review + default + choice, ambiguous, unmatched, no source
overwrite until apply, audit + no unlink, normalization, ACL user/manager).
They were **not executed**: the host has Docker Desktop stopped and no local
Python/Postgres, so `tools/test-module.ps1` (which drives the disposable
`odooapps_vn_address_migration_test` database) cannot run. QA should run:

    & .\data\odoo20\odooapps\tools\test-module.ps1 -Module vn_address_migration

once the Docker Compose Odoo 20 test stack is available, and record
`reports/vn_address_migration-test.log`.

## Handover

- Branch: `feature/pilot02-vn_address_migration` (HEAD recorded in git).
- Module path: `data/odoo20/odooapps/vn_address_migration/`.
- Blockers: (1) clean-install/model tests pending a running Docker/Python host;
  (2) final mapping dataset + attribution string awaiting Release confirmation.
- Next: QA runs `test-module.ps1` on a disposable DB and verifies the scan →
  review → apply → audit flow on desktop/mobile; Release finalizes data source
  and attribution before packaging.
