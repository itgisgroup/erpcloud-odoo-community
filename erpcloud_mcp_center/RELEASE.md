# ERPCloud MCP Center — release 20.0.1.2.0

## Delivered

- Original, responsive MCP Center client action in its own root menu, with Vietnamese and English UI. Odoo backend views and other modules are untouched.
- Streamable HTTP MCP, scoped expiring Bearer keys, OAuth discovery and PKCE, key rotation and revocation.
- Four read tools: identity, sales follow-up briefing, customer lookup and product lookup. Quote-scope keys add quotation proposal. The proposal has a preview and human approval; approval creates only an Odoo Sales draft.
- Traceable activity, source links, local connection self-test, client setup guidance, one-time secret reveal, and user guides in both languages.
- Collapsible desktop sidebar and per-connection grants for three core Odoo models and four curated operations; ungranted tools are hidden and direct calls are denied.
- Dynamic catalog of installed persistent Odoo models, with per-token read/create/update/delete grants, bounded generic tools and an OAuth consent selector showing the chosen connection's model grants. Generic writes have idempotency keys; delete requires an exact model/record confirmation.
- Cohesive original SVG navigation icons, a refined dark sidebar, consistent card styling and a mobile layout checked for text overlap and horizontal overflow.
- Odoo 20 Community dependencies: `base`, `web`, `sale`. LGPL-3. No ERPCloud private addon and no sample business records on normal install.

## Verification evidence

The release gate is a fresh Odoo 20 Community database test via `tools/test-module.ps1`. Its log is `../reports/erpcloud_mcp_center-test.log` in the workspace; the latest clean run on 2026-11-07 after the visual redesign recorded **14 tests, 0 failed, 0 errors**. The suite covers key scope/revocation, dynamic model CRUD and idempotency, model permission filtering, direct-call denial, protocol lifecycle, quotation approval/rejection/idempotency, price drift, cross-user and cross-company denial.

The disposable local browser QA database was tested at `http://127.0.0.1:18032`. Evidence in the workspace reports:

- `reports/mcp_center_upgrade_qa.log`: separate fresh install followed by immediate module upgrade on Odoo 20 CE for the previous version; the existing local UI database was upgraded from 20.0.1.1.0 to 20.0.1.2.0 successfully.
- `reports/mcp_center_browser_qa.json`: desktop VI/EN UI, one-time key reveal, local connection test, 360px mobile width, no browser errors.
- `reports/mcp_center_ui_layout_qa.json`: 360px, 768px and 1440px icon loading, six desktop menu icons, no horizontal overflow, no step-icon/text overlap and no browser errors after the redesign. `reports/mcp_center_ui_mobile_steps.png` records the mobile steps.
- `reports/mcp_center_permission_qa.json`: 242px/72px sidebar open/closed and persistence, restricted tool discovery, direct-call denial, grant-preserving rotation and revoked old key.
- `reports/mcp_center_oauth_qa.json`: OAuth discovery, dynamic registration, consent, token, refresh and refresh-token reuse denial; unauthenticated and foreign-origin requests denied.
- `reports/mcp_center_quote_qa.json`: customer/product lookup, quotation proposal idempotency, pending approval, approved draft, source link.
- `reports/mcp_center_dynamic_qa.json`: dynamic model selection, read/create/update/delete via MCP, idempotent retry, cross-model denial and browser errors.
- `reports/mcp_center_oauth_write_qa.json`: OAuth write consent displayed model grants and permitted the selected token's create/delete tools.
- `static/description/screenshot_*.png`: real screenshots from the local QA build. The marketing cover is composed from a real screenshot.

## Deployment and limits

Set a public HTTPS `web.base.url` and proxy route to `/mcp` before remote client use. Local self-test proves only Odoo-side protocol and tool discovery. The disposable staging endpoint `https://mcp.erpcloud.vn/mcp` passed public OAuth/PKCE and MCP CRUD simulation on 2026-11-07; its tunnel runs on the QA workstation and is not a production availability guarantee. A live ChatGPT/Claude connector test still requires the relevant signed-in client account and remains a separate customer rollout gate. OAuth client behavior may vary by host. Generic CRUD is limited to explicitly granted persistent models and the Odoo user's normal rights; it never runs arbitrary model methods or SQL. Quotation proposals still require human approval.

Support: info@erpcloud.vn.
