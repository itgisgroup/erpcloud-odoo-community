# Hướng dẫn sử dụng — Sổ hoa hồng bán hàng

Phiên bản 20.0.1.0.1 · Odoo 20 Community · Miễn phí · LGPL-3.

## 1. Cài đặt

1. Dùng Odoo 20 Community cài theo requirements chuẩn (có Python `XlsxWriter`). Chép thư mục `erpcloud_sales_commission` vào addons path, khởi động lại Odoo, cập nhật danh sách Apps và cài **Sales Commission Ledger**. Odoo tự cài `sale` và `account` nếu thiếu.
2. Tại Settings → Users, gán vai trò **Commission Salesperson**, **Commission Manager**, **Commission Finance** phù hợp. Quản lý không nên là chính người nhận hoa hồng trong kỳ cần duyệt.
3. Vào **Commissions → Configuration → Plans & Rates**, tạo một plan cho từng nhân viên và công ty. Chọn ngày bắt đầu/kết thúc, chọn `Posted invoice` hoặc `Fully paid invoice`, thêm một tỷ lệ `Default`; tùy chọn thêm sản phẩm/nhóm sản phẩm. Bấm **Activate**. Không tạo hai plan active trùng kỳ cho cùng người/công ty.

Module cài thường **không nạp dữ liệu mẫu**. Ảnh chợ dùng DB demo riêng.

## 2. Từ bán hàng đến phát sinh

1. Trong Sales lõi, tạo đơn bán có một nhân viên phụ trách, xác nhận đơn và tạo hóa đơn khách hàng. Ghi sổ hóa đơn.
2. Mở **Commissions → Earnings**. Mỗi dòng tính theo `price_subtotal` hóa đơn sau chiết khấu, trước thuế. Quy tắc ưu tiên: sản phẩm → nhóm sản phẩm → mặc định. Số công ty được quy đổi theo tỷ giá ngày hóa đơn.
3. Với chính sách `Fully paid invoice`, chỉ khi thanh toán đủ theo trạng thái Odoo thì phát sinh mới xuất hiện; thanh toán một phần không chia tỷ lệ hoa hồng.
4. Credit note tạo bằng luồng đảo/hủy của hóa đơn gốc tạo dòng âm theo tỷ lệ gốc. Khi nguồn không rõ, vào **Configuration → Exceptions** để xem lý do; ghi chú cách xử lý trước khi đóng ngoại lệ.

Ví dụ: hóa đơn sau giảm giá 900 ở tỷ lệ 5% → +45. Hoàn lại 200 → −10. Bảng kê kỳ có 35.

## 3. Chốt kỳ và chi trả

1. Quản lý tạo **Statements** cho một người, một công ty và kỳ ngày. Bấm **Collect earnings**, xem từng dòng. Kỳ cùng người/công ty không được chồng lấn.
2. Nếu cần trả lại bản nháp, nhập `Rejection Reason`, bấm **Reject**; sau xử lý bấm **Reopen**. Quản lý không thể duyệt bảng kê của chính mình.
3. Khi các ngoại lệ đã xử lý, bấm **Approve**. Số và nguồn của ledger không thể sửa trực tiếp; điều chỉnh có lý do nằm ở **Configuration → Adjustments**.
4. Dùng **Preview** để xem bản HTML, **Print PDF** để in, hoặc **Excel** để mở hộp xem trước và tải XLSX (`Summary`, `Details`). Bảng xem trước hiển thị tối đa 100 dòng đầu; tổng là của toàn bộ bộ lọc, Excel chứa toàn bộ dòng.
5. Kế toán vào **Payouts**, chọn statement đã duyệt, nhập ngày/số tiền/số tham chiếu. Chi một phần để lại số dư. Không được chi vượt số đã duyệt. Đây là ghi nhận nghiệp vụ, **không tự chuyển tiền hay tạo bút toán kế toán/lương**.

## 4. Quyền và giới hạn

- Nhân viên bán hàng xem phát sinh và bảng kê của chính mình trong công ty được phép, không cấu hình tỷ lệ.
- Quản lý tạo plan, xử lý ngoại lệ, bảng kê và điều chỉnh; không duyệt khoản của chính mình.
- Finance xem toàn công ty, xuất báo cáo và ghi nhận payout; không sửa ledger.
- Công ty khác bị chặn bằng quyền dữ liệu. Odoo Online không hỗ trợ addon Python này.
- Nhiều người hưởng cùng một dòng, POS, Subscriptions, commission theo bậc doanh số và thanh toán tự động ngoài phạm vi bản này.

## 5. Xử lý nhanh khi chưa thấy hoa hồng

Kiểm tra plan Active đúng công ty/người/ngày; có rule mặc định; hóa đơn là customer invoice đã posted; dòng hóa đơn liên kết đơn bán có đúng một salesperson; với `Fully paid`, hóa đơn đã được Odoo đánh dấu Paid. Nếu vẫn thiếu, xem **Exceptions** và gửi version, log, bước tái hiện đã ẩn dữ liệu nhạy cảm đến **info@erpcloud.vn**.
