# Data notes — mapping cũ → mới

## Trạng thái dữ liệu: CHÍNH THỨC (10.602 bản ghi thật)

`vn.address.mapping.csv` là bộ mapping **chính thức** gồm **10.602 bản ghi**
(đã thay SAMPLE 6 dòng). Sinh từ nguồn cuối đã được Release chốt (mục dưới).

## Nguồn cuối đã chốt (Release xác nhận 2026-11-09)

| Vai trò | Nguồn | Giấy phép |
|---|---|---|
| Nền dữ liệu | `vietnamadminunits` v1.0.4 (PyPI, tác giả Hieu Tran) | MIT |
| Bộ mapping đóng gói | [`undertheseanlp/address`](https://huggingface.co/undertheseanlp/address) — `data/mapping.json` (10.602 bản ghi) | Apache-2.0 |
| Nguồn pháp lý | Nghị quyết Quốc hội (hiệu lực 01/07/2025) + nghị quyết UBTVQH từng tỉnh + Quyết định 19/2025/QĐ-TTg (bảng mã) | — |

Phân loại trong bộ mapping: `unchanged` 149, `renamed` 92, `merged` 9.328,
`divided` 1.033 (tổng 10.602).

## Chuỗi attribution (chính thức)

> Địa chỉ hành chính cũ → mới sau 01/07/2025. Dữ liệu sinh từ
> `undertheseanlp/address` (Apache-2.0, Hugging Face) trên nền
> `vietnamadminunits` v1.0.4 (MIT, PyPI); nguồn pháp lý: Nghị quyết Quốc hội
> (hiệu lực 01/07/2025), nghị quyết UBTVQH từng tỉnh và Quyết định
> 19/2025/QĐ-TTg (bảng mã).

## Cấu trúc cột CSV

`id` (xmlid), `old_ward`, `old_code`, `new_ward`, `new_code`, `new_province`,
`new_province_code`, `classification` (`unchanged|renamed|merged|divided`),
`phan` (`full|partial`), `is_default_new_ward` (`True|False`),
`source_resolution`, `source_clause`, `source_effective_date`, `source_note`.

## Giới hạn dữ liệu đã biết (QA đối chiếu trước Publish)

1. **90/10.602 bản ghi bị thiếu tên trong nguồn**: `undertheseanlp/address` bỏ
   trống `old_ward` (49 bản ghi) hoặc `new_ward` (43 bản ghi, trong đó 2 bản ghi
   trùng cả hai). Release đã thay bằng khóa chuẩn hoá
   (`old_ward_key`/`new_ward_key`; 5 bản ghi "đặc khu" không có cả khóa nên
   dùng `new_ward`) và gắn cờ `name key-derived (QA backfill)` trong cột
   `source_note`. QA cần đối chiếu 90 tên này với Quyết định 19/2025/QĐ-TTg
   trước khi đóng gói/publish.
2. **`source_resolution`/`source_clause` để trống**: nguồn được chọn không cung
   cấp số/khoản nghị quyết theo từng bản ghi; nguồn pháp lý được ghi ở mức bộ
   dữ liệu (README + cột `source_note`).
3. **`old_code`/`new_code` để trống**: nguồn không có mã số xã/phường; đối chiếu
   mã theo Quyết định 19/2025/QĐ-TTg nếu cần.

## Cách tái sinh

Từ `data/mapping.json` của `undertheseanlp/address` (repo nguồn, branch
`main`, commit `e6b7d02493457f8310bbd98038ff8d10b470484c`): ánh xạ
`ward_mapping[].mapping_type` → `classification`, `is_default` →
`is_default_new_ward`, `phan` = `partial` cho `divided` / `full` cho phần còn
lại, `new_province_code` lấy từ `province_names[].code`, `source_effective_date`
= `metadata.effective_date`.
