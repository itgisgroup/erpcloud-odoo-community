# ERPCloud MCP Center — release 20.0.1.0.0

## Delivered

- Original, responsive MCP Center client action in its own root menu, with Vietnamese and English UI. Odoo backend views and other modules are untouched.
- Streamable HTTP MCP, scoped expiring Bearer keys, OAuth discovery and PKCE, key rotation and revocation.
- Four read tools: identity, sales follow-up briefing, customer lookup and product lookup. Quote-scope keys add quotation proposal. The proposal has a preview and human approval; approval creates only an Odoo Sales draft.
- Traceable activity, source links, local connection self-test, client setup guidance, one-time secret reveal, and user guides in both languages.
- Odoo 20 Community dependencies: `base`, `web`, `sale`. LGPL-3. No ERPCloud private addon and no sample business records on normal install.

## Verification evidence

The release gate is a fresh Odoo 20 Community database test via `tools/test-module.ps1`. Its log is `../reports/erpcloud_mcp_center-test.log` in the workspace; the module test suite covers key scope/revocation, protocol lifecycle, quotation approval/rejection/idempotency, price drift, cross-user and cross-company denial.

The disposable local browser QA database was tested at `http://127.0.0.1:18032`. Evidence in the workspace reports:

- `reports/mcp_center_browser_qa.json`: desktop VI/EN UI, one-time key reveal, local connection test, 360px mobile width, no browser errors.
- `reports/mcp_center_oauth_qa.json`: OAuth discovery, dynamic registration, consent, token, refresh and refresh-token reuse denial; unauthenticated and foreign-origin requests denied.
- `reports/mcp_center_quote_qa.json`: customer/product lookup, quotation proposal idempotency, pending approval, approved draft, source link.
- `static/description/screenshot_*.png`: real screenshots from the local QA build. The marketing cover is composed from a real screenshot.

## Deployment and limits

Set a public HTTPS `web.base.url` and proxy route to `/mcp` before remote client use. Local self-test proves only Odoo-side protocol and tool discovery. A live ChatGPT/Claude connector test requires an externally reachable HTTPS Odoo instance and the relevant client account; this is a separate customer rollout gate. OAuth client behavior may vary by host. This release does not confirm sales, post invoices, send messages or execute arbitrary Odoo methods.

Support: info@erpcloud.vn.
