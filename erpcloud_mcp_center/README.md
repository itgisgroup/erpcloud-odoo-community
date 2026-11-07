# ERPCloud MCP Center — Odoo 20 Community

An original, full-screen MCP workspace for Odoo business users. Connect an AI assistant, control each connection's owner and lifetime, read sourced sales follow-up data, and submit quotation previews for human approval.

## Requirements

- Odoo 20 Community with `base`, `web`, and Odoo's standard `sale` module.
- A public HTTPS Odoo URL for remote AI applications. Localhost works for local testing only.
- The connecting Odoo user needs the normal Odoo access rights for each business record. Quote proposals also need a user who may create sales quotations.

No ERPCloud private addon is required. Installation adds no sample customer or product data and does not replace Odoo core views.

## Install

1. Copy `erpcloud_mcp_center` into an Odoo addons path.
2. Refresh Apps and install **ERPCloud MCP Center**.
3. Open the **MCP Center** root menu. The initial key scope is read only. In **Connect AI → Odoo model access**, all four operations are visible; an MCP Center manager can click **Enable write scope** to select Create, Update and Delete separately.
4. A system administrator or **MCP Center Manager** may issue a quote proposal key. Assign **MCP Center Approver** to users allowed to approve proposals.
5. Set `web.base.url` to the actual HTTPS origin. If an AI client is hosted elsewhere, ensure it can reach `https://your-odoo/mcp`.

## What is included

- Streamable HTTP MCP endpoint at `/mcp`, with JSON-RPC initialize, tools/list, tools/call and sessions.
- OAuth discovery, dynamic client registration, PKCE authorization, refresh and revocation endpoints for remote clients; personal Bearer keys for clients that support them.
- Scoped, expiring keys with one-time reveal, rotation, revocation and a per-key request budget.
- Per-key choices for Odoo customer lookup, product lookup, quotation briefing and human-reviewed quotation proposal. Unselected tools are hidden and denied on direct invocation; Odoo user rights still apply.
- Searchable catalog of installed persistent Odoo models. A manager can grant per-token read, create, update and delete operations; generic MCP tools enforce the token grant and the real Odoo user's ACLs/record rules. OAuth consent displays the selected connection and its model grants.
- Generic model read/write tools filter unsafe fields and bound result size. A stable request key prevents duplicate create/update/delete actions after retries. Delete requires an exact model and record confirmation.
- `whoami`, `customer_lookup`, `product_lookup`, and `sales_followup_briefing` read tools. Lookups let an assistant resolve real customer/product names before proposing a quotation. The briefing returns source document links and remains within the owner's Odoo rights and company.
- `quotation_propose` prepares a preview; a named approver must approve it in MCP Center. Approval rechecks prices and taxes and creates only a **draft** sale order. Repeated requests cannot create duplicate orders.
- An activity trail with trace IDs. Secrets and full prompt contents are not stored in that trail.
- Original desktop and mobile UI with Vietnamese and English interface copy.
- Collapsible desktop sidebar with a remembered preference.

## Scope and limits

The curated workflow supports sales quotations; generic CRUD can operate on any explicitly granted installed persistent model within Odoo's normal security rules. It does not send or confirm orders through a special workflow, run arbitrary Odoo methods or connect to messaging channels. OAuth and third-party client UI compatibility depend on the client's current plan, policies and implementation; validate against the target client before customer rollout.

The connection test in MCP Center exercises local MCP initialization and tool discovery. It does not prove that a remote AI provider can reach a private Odoo server.

## Support and license

Support: **info@erpcloud.vn**. License: **LGPL-3.0**. See [LICENSE](LICENSE).
