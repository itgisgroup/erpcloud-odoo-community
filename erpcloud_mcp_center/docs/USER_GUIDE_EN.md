# ERPCloud MCP Center user guide

Install on Odoo 20 Community, open the **MCP Center** root menu, and use **Connect AI** to copy your MCP URL. Remote clients need a public HTTPS Odoo URL. Choose a read-only key first, save it when it appears once, then select the client instructions. The local **Test connection now** button checks the MCP lifecycle and tool discovery. Revoke or rotate a key when needed.

The sales briefing reads draft and sent quotations within the owner's Odoo rights and company. Each result includes the source document number and URL. A manager may issue a quotation proposal key; a separate user with **MCP Center Approver** rights reviews the exact preview and approves creation of a draft quotation. The module never sends or confirms it automatically.

For support, send a trace ID from **Activity** to `info@erpcloud.vn`. Never send your key.

# Connection permissions

Before creating a key, select the Odoo models and workflows it may use: customer lookup, product lookup and sales quotation briefing. A Manager can also enable quotation proposals with the quote scope; an approver must still review every proposal. An unselected workflow is absent from the MCP tool list and rejected if called directly. To change a key's rights, revoke it and create a new key. The desktop menu can be collapsed and expanded with the button at the top left.
# Dynamic Odoo model access

In **Connect AI → Odoo model access**, search any installed persistent Odoo model by label or technical name. Read, Create, Update and Delete are always visible. The default scope permits Read only. An MCP Center manager can click **Enable write scope**, then select Create, Update or Delete separately for each model. An operation stays disabled if the Odoo user lacks that model right. A token never overrides the owner's Odoo access rights or record rules. Select only the operations a particular assistant needs; revoke and reissue a token to change its grants.

Generic MCP tools are `list_models`, `get_fields`, `search_records`, `get_record`, `create_record`, `update_record`, and `delete_record`. For writes, use a stable `request_key` so a client retry cannot duplicate the action. Deletion requires the exact confirmation text `DELETE <model> <id>` and is permanent. The generic tools do not call arbitrary model methods or accept SQL. Some fields (secrets, binary and collection relations) are deliberately unavailable. OAuth clients need explicit **write** consent for write tools. Use the Activity trace ID when asking for support.
