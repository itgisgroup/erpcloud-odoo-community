# Changelog

## 20.0.1.0.0 — 2026-11-09

- Initial Odoo 20 Community pilot: old-to-new ward mapping table, offline scan
  that creates draft/review proposals, review queue for divided/ambiguous/
  unmatched cases, immutable audit trail, and ACL-respecting apply action.
- Shipped mapping data is the authoritative 10,602-row dataset generated from
  `undertheseanlp/address` (Apache-2.0) / `vietnamadminunits` v1.0.4 (MIT); 90
  rows carry key-derived names flagged for QA backfill (see `data/DATA_NOTES.md`).
