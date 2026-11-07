# Changelog

## 20.0.1.2.0 — 2026-11-07

- Searchable catalog of installed persistent Odoo models, with per-token read/create/update/delete grants.
- Generic model tools use Odoo ACLs and record rules, bounded safe fields, company isolation and idempotent write request keys.
- OAuth consent now shows the connection and model grants to select before authorization.
- Refined MCP Center navigation with a cohesive original SVG icon set, dark collapsible sidebar, clearer cards and mobile layout.

## 20.0.1.1.0 — 2026-11-07

- Collapsible desktop sidebar with a remembered preference.
- Per-connection Odoo model and workflow permissions for customer lookup, product lookup, sales briefing and quotation proposal.
- Hidden tools and direct calls are both denied when the connection lacks a grant; existing keys keep their prior capabilities on upgrade.

## 20.0.1.0.0 — 2026-11-07

- First Odoo 20 Community release of ERPCloud MCP Center.
- End-user workspace, scoped connections, MCP Streamable HTTP and OAuth/PKCE.
- Sales follow-up briefing and human-reviewed quotation proposal workflow.
