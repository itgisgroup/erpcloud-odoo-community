# Hướng dẫn ERPCloud MCP Center

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
