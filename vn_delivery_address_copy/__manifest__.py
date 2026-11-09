{
    "name": "Vietnam Address Copy",
    "version": "20.0.1.0.1",
    "summary": "Copy a contact's delivery address as one line",
    "category": "Contacts",
    "author": "ERPCloud",
    "website": "https://erpcloud.vn",
    "support": "info@erpcloud.vn",
    "license": "LGPL-3",
    "depends": ["contacts"],
    "images": [
        "static/description/cover.png",
        "static/description/screenshot_contact_desktop.png",
        "static/description/screenshot_contact_mobile.png",
        "static/description/screenshot_no_address.png",
    ],
    "data": ["views/res_partner_views.xml"],
    "assets": {
        "web.assets_backend": [
            "vn_delivery_address_copy/static/src/scss/address_copy.scss",
        ],
    },
    "installable": True,
    "application": False,
}
