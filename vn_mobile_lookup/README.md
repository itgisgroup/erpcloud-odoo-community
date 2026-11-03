# Vietnam Mobile Lookup

Free Odoo 20 module by ERPCloud. Find a contact by a Vietnamese mobile number even when its stored form differs from the query:

| Stored in `phone` | Search in Contacts name box | Match |
| --- | --- | --- |
| `+84 912 345 678` | `0912345678` | Yes |
| `0912 345 678` | `+84 912 345 678` | Yes |
| `0084 912 345 678` | `0912345678` | Yes |

The module adds an indexed, computed lookup key. It does not edit `phone`, call an external service, enforce uniqueness, or validate whether a number is currently assigned. It recognizes only Vietnamese ten-digit mobile prefixes `03`, `05`, `07`, `08`, and `09`. Contacts explicitly assigned to another country are excluded from the Vietnamese lookup. Normal name, email, tax ID, and reference search remains available.

## Install

Copy `vn_mobile_lookup` to an Odoo 20 addons path, update the Apps list, and install **Vietnam Mobile Lookup**. The only dependency is Odoo's standard `contacts` module. Tested on Odoo 20 Community in a self-hosted Docker instance. Odoo.sh and Enterprise have not yet been tested; Odoo Online does not install Python addons.

## Use

Open **Contacts**, type a complete Vietnamese mobile number in the **Name** search option, and select the result. The same lookup is available where Odoo uses contact name suggestions. Entering a partial number continues to use Odoo's normal search behavior.

## Privacy and license

Search runs inside Odoo with the requesting user's normal access rights. No phone number is transmitted to ERPCloud. Licensed under LGPL-3; see `LICENSE`.

Support: info@erpcloud.vn
