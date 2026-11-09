# Data notes — mapping cũ → mới

## Trạng thái dữ liệu: SAMPLE (chưa phải bộ dữ liệu chính thức)

`vn.address.mapping.csv` trong thư mục này chỉ là **mẫu minh hoạ** gồm 6 dòng
để module cài và chạy được ngay (bao phủ 4 loại phân loại và một ca tách
`divided` kèm cờ `is_default_new_ward`). Nó **không phải** bộ mapping 10.602
bản ghi cuối cùng.

Theo SRS mục 2 (Gate G0), việc **chọn MỘT nguồn cuối** và **chuỗi attribution
chính xác** phải được **Release xác nhận trước khi đóng gói dữ liệu chính thức**
vào module. Vì vậy dữ liệu chính thức bị treo lại cho Release; Agent A chỉ
DRAFT chuỗi ghi nguồn và đánh dấu rõ để Release chốt.

## Nguồn dữ liệu dự kiến (chưa chốt — để Release xác nhận)

| Vai trò | Nguồn | Giấy phép |
|---|---|---|
| Khuyến nghị | [`undertheseanlp/address`](https://huggingface.co/undertheseanlp/address) — `data/mapping.json` (10.602 bản ghi) | Đóng gói Apache-2.0; upstream [`vietnamadminunits`](https://pypi.org/project/vietnamadminunits/) MIT; dữ liệu nền là văn bản/quyết định nhà nước |
| Thay thế | [`dorabot-io/dia-chi`](https://github.com/dorabot-io/dia-chi) — `data/cu/*.json` + `data/moi.json` | Code MIT; dữ liệu CC BY 4.0 (ghi nguồn "Dorabot (dorabot.io/dia-chi/sap-nhap)") |

## DRAFT chuỗi attribution (CHỜ RELEASE CHỐT — chưa dùng chính thức)

> Địa chỉ hành chính cũ → mới sau 01/07/2025. Dữ liệu sinh từ
> `undertheseanlp/address` (Apache-2.0, Hugging Face) trên nền
> `vietnamadminunits` v1.0.4 (MIT, PyPI); nguồn pháp lý: Nghị quyết Quốc hội
> (hiệu lực 01/07/2025), Nghị quyết UBTVQH từng tỉnh và Quyết định 19/2025/QĐ-TTg
> (bảng mã). — **DRAFT, chưa xác nhận với Release.**

## Cấu trúc cột CSV

`id` (xmlid), `old_ward`, `old_code`, `new_ward`, `new_code`, `new_province`,
`new_province_code`, `classification` (`unchanged|renamed|merged|divided`),
`phan` (`full|partial`), `is_default_new_ward` (`True|False`),
`source_resolution`, `source_clause`, `source_effective_date`, `source_note`.

## Cách thay bằng bộ dữ liệu chính thức

1. Sinh CSV cùng cấu trúc cột ở trên từ nguồn đã được Release chốt.
2. Thay file `vn.address.mapping.csv` và cập nhật `source_note`/`README.md`
   bằng chuỗi attribution chính thức.
3. Cài lại/upgrade module; dữ liệu được nạp lại theo xmlid.
