# Vietnam Address Copy

Free addon for Odoo 20 Community. It adds a read-only, one-line delivery address to the Contacts form. The core Odoo `CopyClipboardChar` widget copies the displayed text when an address component exists.

## Install

Add this directory to an Odoo 20 addons path, update the Apps list, and install **Vietnam Address Copy**. The only direct dependency is `contacts`. Odoo Online cannot install third-party Python addons.

## Use

Open a contact in **Contacts**. The field **Địa chỉ giao hàng để sao chép** joins, in order, name, street, street2, city, state, ZIP, and country with `, `. Leading and trailing whitespace and empty values are omitted. If there is no address component, the field is empty and the form says **Chưa có thành phần địa chỉ để sao chép.**

The addon does not change source address fields, normalize Vietnamese administrative areas, or send data to an external service. Browser clipboard access requires a secure context, such as HTTPS or localhost.

## Screenshots and artwork

`static/description/screenshot_contact_desktop.png` and `screenshot_contact_mobile.png` show the actual Contacts form with a synthetic QA contact and a successful copy. `screenshot_no_address.png` shows the actual empty-address message. The square icon and cover are original illustrations; they are product artwork, not UI screenshots. The screenshots were captured from the disposable local Odoo 20 QA build and cropped to emphasize the relevant form. No customer data is used.

## License and support

Copyright ERPCloud. LGPL-3. Support: info@erpcloud.vn.
