{
    "name": "ERPCloud MCP Center",
    "summary": "Connect AI assistants to useful, governed Odoo workflows",
    "version": "20.0.1.1.0",
    "category": "Productivity",
    "author": "ERPCloud",
    "website": "https://erpcloud.vn",
    "maintainer": "ERPCloud",
    "support": "info@erpcloud.vn",
    "license": "LGPL-3",
    "images": [
        "static/description/cover.png",
        "static/description/screenshot_connect_en.png",
        "static/description/screenshot_approval_en.png",
        "static/description/screenshot_mobile_en.png",
    ],
    "depends": ["base", "web", "sale"],
    "data": [
        "security/security.xml",
        "security/ir.access.csv",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "erpcloud_mcp_center/static/src/center/center.js",
            "erpcloud_mcp_center/static/src/center/center.xml",
            "erpcloud_mcp_center/static/src/center/center.scss",
        ],
    },
    "application": True,
    "installable": True,
}
