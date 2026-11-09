# Vietnam Address Migration

Free addon for Odoo 20 Community. It migrates Vietnamese contacts from the old
3-level administrative address (province / district / ward) to the 2-level
structure in force since 01/07/2025, without touching source address fields
until a user explicitly applies a proposal.

The addon provides:

- an **old ward → new ward** mapping table (with new province, classification
  `unchanged / renamed / merged / divided`, a `phan` full/partial flag and the
  resolution source);
- a **scan** tool (batch or per contact) that finds old 3-level addresses offline
  from packaged data and creates proposals;
- a **review queue** for ambiguous, divided and unmatched cases where the user
  picks the destination;
- a full **audit trail** (old/new values, actor, time, source resolution, state)
  that cannot be deleted.

## Install

Add this directory to an Odoo 20 addons path, update the Apps list, and install
**Vietnam Address Migration**. The only direct dependency is `contacts`.
Odoo Online cannot install third-party Python addons.

## Use

Open **Contacts ▸ Địa chỉ di cư ▸ Quét địa chỉ**, select one or more contacts and
press **Quét**. The addon only creates proposals (`draft`/`review`); it never
modifies `street`, `city`, `state_id` or `country_id` by itself.

- A clear merge is proposed directly (`direct`, `draft`).
- A split (one old ward → several new wards) or an ambiguous/no-match address
  goes to the **review** queue; pick a destination ward, then **Áp dụng**.
- Applying writes the proposed `city`/`state_id` and records who/when in the
  audit page. Records keep the audit trail and cannot be deleted (archive only).

## Scope and limits

The addon does **not** rebuild the Vietnamese administrative-unit catalog (that
is the scope of `vn_address`), does not geocode, does not issue invoices and does
not require an external service. Applying only changes the mapped `city` and
`state_id`; `street`, `street2`, `zip` and `country_id` are left for the user to
review. Permissions follow the current ACL/record rules: users only scan contacts
they can read, and only managers (or users with write access to both the
migration record and the contact) can apply.

## Data provenance — DRAFT, pending Release confirmation

The bundled `data/vn.address.mapping.csv` is a **6-row illustrative sample**,
not the authoritative dataset. Per the SRS the final data source and the exact
attribution string must be confirmed by Release before the full dataset is
packaged. Candidate sources:

| Source | License |
|---|---|
| [`undertheseanlp/address`](https://huggingface.co/undertheseanlp/address) (recommended) | packaging Apache-2.0; upstream `vietnamadminunits` MIT |
| [`dorabot-io/dia-chi`](https://github.com/dorabot-io/dia-chi) | code MIT; data CC BY 4.0 |

**DRAFT attribution (not final):** administrative data generated from
`undertheseanlp/address` (Apache-2.0, Hugging Face) on top of `vietnamadminunits`
v1.0.4 (MIT, PyPI); legal basis: National Assembly resolutions (effective
01/07/2025), per-province Standing Committee resolutions and Decision
19/2025/QĐ-TTg (code table). See `data/DATA_NOTES.md`.

## License and support

Copyright ERPCloud. LGPL-3. Support: info@erpcloud.vn.
