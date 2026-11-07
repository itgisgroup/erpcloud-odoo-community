# ERPCloud MCP Center — release 20.0.1.3.0

## OAuth sign-in update

OAuth-capable assistants now start with a direct Odoo sign-in. Consent shows the requesting application, account, company, return address and requested scopes. A read-only connection is issued automatically when the user consents. **Allow changes** remains unticked and requires an existing manager-approved key whose exact model operations are shown. Authorization codes, access tokens and rotating refresh tokens are bound to the MCP resource URL; an attempt to redeem a code for another resource is rejected. Reuse of a rotated refresh token revokes the family. Existing OAuth clients must sign in again after upgrade because old grants lack an audience.

QA on 2026-11-07: clean Odoo 20 CE install **14 tests, 0 failed, 0 errors** (`../reports/erpcloud_mcp_center-test.log`); local and public HTTPS OAuth browser flows passed (`../reports/mcp_center_oauth_qa.json`, `../reports/mcp_center_oauth_public_qa.json`), including automatic key issuance, read-only default, audience rejection, MCP tool discovery and refresh replay rejection. Selected write consent passed local browser QA with create/delete of a disposable partner and token revocation (`../reports/mcp_center_oauth_write_qa.json`). The real Claude/ChatGPT UI connection remains unverified; this endpoint uses a temporary QA tunnel. New consent screenshot: `static/description/screenshot_oauth_consent_en.png`.

## Delivered

- Original, responsive MCP Center client action in its own root menu, with Vietnamese and English UI. Odoo backend views and other modules are untouched.
- Streamable HTTP MCP, scoped expiring Bearer keys, OAuth discovery and PKCE, key rotation and revocation.
- Four read tools: identity, sales follow-up briefing, customer lookup and product lookup. Quote-scope keys add quotation proposal. The proposal has a preview and human approval; approval creates only an Odoo Sales draft.
- Traceable activity, source links, local connection self-test, client setup guidance, one-time secret reveal, and user guides in both languages.
- Collapsible desktop sidebar and per-connection grants for three core Odoo models and four curated operations; ungranted tools are hidden and direct calls are denied.
- Dynamic catalog of installed persistent Odoo models, with per-token read/create/update/delete grants, bounded generic tools and an OAuth consent selector showing the chosen connection's model grants. Generic writes have idempotency keys; delete requires an exact model/record confirmation.
- Cohesive original SVG navigation icons, a refined dark sidebar, consistent card styling and a mobile layout checked for text overlap and horizontal overflow.
- The model access card now always shows Read/Create/Update/Delete. The safe default remains read-only; managers can enable write scope in that card, after which each operation is still selected separately and checked against Odoo ACLs.
- Odoo 20 Community dependencies: `base`, `web`, `sale`. LGPL-3. No ERPCloud private addon and no sample business records on normal install.

## Verification evidence

The release gate is a fresh Odoo 20 Community database test via `tools/test-module.ps1`. Its log is `../reports/erpcloud_mcp_center-test.log` in the workspace; the latest clean run on 2026-11-07 for 20.0.1.2.1 recorded **14 tests, 0 failed, 0 errors**. The suite covers key scope/revocation, dynamic model CRUD and idempotency, model permission filtering, direct-call denial, protocol lifecycle, quotation approval/rejection/idempotency, price drift, cross-user and cross-company denial.

The disposable browser QA database was tested locally and again through `https://mcp.erpcloud.vn` after its public HTTPS route was configured. Evidence in the workspace reports:

- `reports/mcp_center_upgrade_qa.log`: separate fresh install followed by immediate module upgrade on Odoo 20 CE for the previous version. The public QA database was subsequently upgraded to 20.0.1.2.1 and verified through the browser.
- `reports/mcp_center_model_scope_ui_qa.json`: on public HTTPS, all four operations visible in read-only mode; write operations disabled initially; manager switch enables Odoo-authorized operations; a write-scope key retained selected Read/Create/Update grants and was revoked; 1440px desktop and 360px mobile have no overflow or browser errors.
- `reports/mcp_center_browser_qa.json`: desktop VI/EN UI, one-time key reveal, same-origin HTTPS connection test, 360px mobile width, no browser errors.
- `reports/mcp_center_ui_layout_qa.json`: 360px, 768px and 1440px icon loading, six desktop menu icons, no horizontal overflow, no step-icon/text overlap and no browser errors after the redesign. `reports/mcp_center_ui_mobile_steps.png` records the mobile steps.
- `reports/mcp_center_permission_qa.json`: 242px/72px sidebar open/closed and persistence, restricted tool discovery, direct-call denial, grant-preserving rotation and revoked old key.
- `reports/mcp_center_oauth_qa.json`: OAuth discovery, dynamic registration, consent, token, refresh and refresh-token reuse denial; unauthenticated and foreign-origin requests denied.
- `reports/mcp_center_quote_qa.json`: customer/product lookup, quotation proposal idempotency, pending approval, approved draft, source link.
- `reports/mcp_center_dynamic_qa.json`: dynamic model selection, read/create/update/delete via MCP, idempotent retry, cross-model denial and browser errors.
- `reports/mcp_center_oauth_write_qa.json`: OAuth write consent displayed model grants and permitted the selected token's create/delete tools.
- `static/description/screenshot_*.png`: real screenshots from the QA build. The overview, connection and mobile screenshots were refreshed through public HTTPS after the original local-address warning was resolved. The marketing cover is composed from a real screenshot.

## Deployment and limits

Set a public HTTPS `web.base.url` and proxy route to `/mcp` before remote client use. Local self-test proves only Odoo-side protocol and tool discovery. The disposable staging endpoint `https://mcp.erpcloud.vn/mcp` passed public OAuth/PKCE and MCP CRUD simulation on 2026-11-07; its tunnel runs on the QA workstation and is not a production availability guarantee. A live ChatGPT/Claude connector test still requires the relevant signed-in client account and remains a separate customer rollout gate. OAuth client behavior may vary by host. Generic CRUD is limited to explicitly granted persistent models and the Odoo user's normal rights; it never runs arbitrary model methods or SQL. Quotation proposals still require human approval.

Support: info@erpcloud.vn.
