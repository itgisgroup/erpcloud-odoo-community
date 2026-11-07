# Hướng dẫn ERPCloud MCP Center

## Đăng nhập OAuth đơn giản

Với trợ lý hỗ trợ OAuth, nhập URL công khai `https://ten-mien-odoo/mcp`. Trợ lý mở màn đăng nhập Odoo. Sau khi đăng nhập, kiểm tra tên ứng dụng xin quyền, tài khoản, công ty và địa chỉ ứng dụng sẽ nhận kết quả. Nhấn **Sign in and allow** để tạo kết nối chỉ đọc tự động, không cần sao chép token. Ô **Allow changes** mặc định bỏ chọn; muốn bật phải chọn kết nối đã được quản lý MCP Center cấp đúng thao tác cho từng model. Quyền Odoo và quy tắc công ty vẫn áp dụng. Kết nối OAuth cũ cần đăng nhập lại sau khi nâng cấp 20.0.1.3.0 vì token mới được ràng buộc với URL máy chủ MCP.

## Cài đặt

Sao chép thư mục `erpcloud_mcp_center` vào addons path của Odoo 20 Community, cập nhật danh sách Apps rồi cài **ERPCloud MCP Center**. Module phụ thuộc `base`, `web`, `sale` chuẩn của Odoo. Mở menu **MCP Center** để bắt đầu.

Để trợ lý trên Internet kết nối, cấu hình `web.base.url` bằng tên miền HTTPS công khai của Odoo. `localhost` hoặc `127.0.0.1` chỉ dùng kiểm thử trên cùng máy.

## Kết nối an toàn

Vào **Kết nối AI**, sao chép URL MCP. Tạo khóa cá nhân với phạm vi **Chỉ xem dữ liệu** và thời hạn phù hợp. Khóa hiện đúng một lần; sao chép vào nơi lưu bí mật của ứng dụng AI. Bấm **Kiểm tra kết nối ngay** để thử giao thức và danh sách công cụ tại máy chủ này. Nếu nghi ngờ khóa bị lộ, bấm **Đổi khóa** hoặc **Ngắt**.

Claude và ChatGPT dùng luồng OAuth khi thêm máy chủ MCP từ giao diện của họ. Gói đăng ký và quyền workspace của từng hãng có thể khác nhau. Codex/Cursor có thể dùng Bearer key nếu phiên bản máy khách hỗ trợ. Xem hướng dẫn theo ứng dụng ngay trong tab Kết nối AI.

## Nghiệp vụ

- **Tóm tắt báo giá cần theo dõi:** AI có thể đọc báo giá nháp/đã gửi trong 1–90 ngày, giới hạn theo quyền Odoo và công ty của chủ kết nối. Kết quả có mã chứng từ và URL để mở kiểm tra.
- **Tìm khách và sản phẩm:** AI tra cứu theo tên hoặc email/SKU trong phạm vi quyền Odoo, lấy đúng ID bản ghi để chuẩn bị báo giá.
- **Đề xuất báo giá:** Quản trị viên cấp khóa phạm vi đề xuất. AI gửi khách, sản phẩm và số lượng; MCP Center tính giá/thuế và hiện bản xem trước trong **Cần duyệt**. Người có nhóm **MCP Center Approver** duyệt để tạo báo giá **nháp**, hoặc từ chối. Giá/thuế thay đổi trước lúc duyệt thì yêu cầu xem trước lại.

Không có thao tác gửi báo giá hoặc xác nhận đơn tự động.

## Phân quyền và xử lý lỗi

Người dùng cần quyền Odoo chuẩn để xem/tạo báo giá. Nhóm **MCP Center Manager** cấp khóa đề xuất; nhóm **MCP Center Approver** duyệt. Trong tab **Hoạt động**, sao chép mã truy vết khi liên hệ `info@erpcloud.vn`. Không gửi khóa cá nhân qua email hoặc chat hỗ trợ.
# Quyền theo model

Trước khi tạo khóa, chọn dữ liệu Odoo và tiện ích được phép dùng: tra cứu khách hàng, tra cứu sản phẩm, xem tóm tắt báo giá. Quản trị viên có thể cấp thêm quyền đề xuất báo giá trong phạm vi báo giá; mỗi đề xuất vẫn cần người phụ trách duyệt. Tiện ích không được chọn sẽ không xuất hiện trong danh sách MCP và bị từ chối nếu gọi trực tiếp. Muốn đổi quyền của khóa cũ, hãy ngắt khóa đó rồi tạo khóa mới. Nút góc trên trái đóng hoặc mở sidebar trên desktop.
# Cấp quyền động theo model Odoo

Trong **Kết nối AI → Model Odoo được cấp quyền**, tìm model đã cài bằng tên hoặc mã kỹ thuật. Bốn thao tác **Xem**, **Thêm**, **Sửa**, **Xóa** luôn hiện. Mặc định chỉ có Xem để tránh cấp quyền ghi ngoài ý muốn. Người quản lý MCP Center bấm **Bật quyền ghi**, rồi đánh dấu riêng những thao tác thật sự cần cho từng model. Nếu một thao tác vẫn mờ, tài khoản Odoo hiện tại chưa có quyền đó trên model. Token không vượt qua ACL hay record rule của người sở hữu trong Odoo. Muốn đổi quyền của khóa đã tạo, ngắt khóa cũ và tạo khóa mới.

Các công cụ MCP tổng quát gồm `list_models`, `get_fields`, `search_records`, `get_record`, `create_record`, `update_record`, `delete_record`. Khi ghi dữ liệu, dùng `request_key` ổn định để thử lại không tạo thao tác trùng. Xóa cần xác nhận đúng chuỗi `DELETE <model> <id>` và là thao tác vĩnh viễn. Công cụ không cho gọi phương thức model tùy ý hoặc SQL; trường bí mật, nhị phân và quan hệ danh sách không được mở. Client OAuth phải được duyệt phạm vi **write** cho công cụ ghi. Khi cần hỗ trợ, gửi mã truy vết trong Hoạt động.
