# Release Record: ERPCloud Blog & News

- Module: `erpcloud_blog`
- Series: Odoo 20.0
- Target version: 20.0.1.2.0
- License: LGPL-3
- Price: Free
- Publisher repo: `itgisgroup/erpcloud-odoo-community` branch `20.0`
- Maintainer: ERPCloud (info@erpcloud.vn)
- QA: clean install passed 4/4 module tests on disposable Odoo 20 CE database; see `../reports/erpcloud_blog-test.log`.
- Browser: real Odoo 20 screenshots in `static/description/`; combined-page results in `../reports/content_media_browser_qa.json`.
- Public flows: `../reports/content_media_public_flow_qa.json` (Blog API, Video API, moderated visitor comment).
- Media: new icon and cover in `static/description/`; social square and bilingual captions in `../media/erpcloud_blog/`.
- Limitation: No automatic scheduled publication or Open Graph/Schema.org injection.
- Publication: pending publisher repo sync, Odoo Apps Scan and anonymous listing verification.
- Dependencies: `website`, `mail`, `portal`
