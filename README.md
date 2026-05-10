# Ximi Datathon 2026

Repository cho bài toán Datathon 2026, kết hợp:
1. **dbt** để tổ chức mô hình dữ liệu theo tầng (staging/marts)  
2. **Streamlit** để trực quan hóa EDA và data storytelling

## 1. Tổng quan luồng dữ liệu

### 1.1 Luồng ETL/ELT trong dbt

```text
CSV seeds (seeds/*.csv)
    -> stg_* models (models/staging/*.sql): chuẩn hóa tên cột, kiểu dữ liệu, khóa quan hệ
    -> fct_* marts (models/marts/*.sql): tổng hợp business metrics cho EDA
    -> dbt tests (_stg_model.yml, _mart_model.yml): unique/not_null/relationships
    -> artifacts (target/manifest.json, run_results.json, docs)
```

### 1.2 Luồng trực quan hóa trong Streamlit

```text
seeds/*.csv
    -> streamlit_app.py (Pandas transforms)
    -> 3 data marts in-memory:
       - promo mart
       - returns mart
       - inventory mart
    -> dashboard tabs + KPI + charts + insight blocks
```

> Ghi chú: dashboard hiện tại đọc trực tiếp từ `seeds/` để chạy nhanh tại local.  
> Phần dbt marts vẫn được giữ đầy đủ để chuẩn hóa logic phân tích và test chất lượng dữ liệu.

## 2. Các lớp dữ liệu và ý nghĩa

### 2.1 Seed layer (`seeds/`)

Bao gồm dữ liệu đầu vào từ đề bài:
- **Master**: `products`, `customers`, `promotions`, `geography`
- **Transaction**: `orders`, `order_items`, `payments`, `shipments`, `returns`, `reviews`
- **Analytical**: `sales`
- **Operational**: `inventory`, `web_traffic`

### 2.2 Staging layer (`models/staging/`)

Các model `stg_*` dùng để:
1. Chuẩn hóa schema và kiểu dữ liệu (date, numeric, string)
2. Tách rõ business entity theo từng bảng nguồn
3. Thiết lập các ràng buộc dữ liệu (khóa chính/khóa ngoại) thông qua dbt tests

### 2.3 Mart layer (`models/marts/`)

Ba bảng mart chính phục vụ EDA:

| Model | Mục tiêu phân tích | Chỉ số chính |
|---|---|---|
| `fct_promo_performance` | Hiệu quả khuyến mãi và biên lợi nhuận | `gross_revenue`, `net_revenue`, `gross_profit`, `gross_margin_pct`, `promo_status` |
| `fct_customer_returns` | Hành vi trả hàng và tác động tài chính | `return_reason`, `refund_amount`, `days_to_return`, nhân khẩu học khách |
| `fct_inventory_stockouts` | Tồn kho, thiếu hàng, vốn đọng | `est_lost_revenue`, `overstock_capital_value`, `stockout_days`, `sell_through_rate` |

## 3. Cấu trúc dự án

```text
ximi/
├── seeds/                     # Dữ liệu nguồn CSV
├── models/
│   ├── staging/               # stg_* models + tests schema
│   │   ├── stg_*.sql
│   │   └── _stg_model.yml
│   └── marts/                 # fct_* marts cho EDA
│       ├── fct_*.sql
│       └── _mart_model.yml
├── analyses/                  # SQL phân tích ad-hoc (reserved)
├── macros/                    # dbt macros (reserved)
├── tests/                     # custom tests (reserved)
├── snapshots/                 # snapshot models (reserved)
├── target/                    # dbt artifacts sinh tự động
├── streamlit_app.py           # Dashboard Streamlit
├── dbt_project.yml            # Cấu hình dbt project
└── README.md
```

## 4. Luồng dashboard EDA

Dashboard trong `streamlit_app.py` gồm 3 tab:
1. **Hiệu quả khuyến mãi (Promo Performance)**
   - KPI: Net Revenue, Gross Profit, Gross Margin (+ delta)
   - Trend theo tháng và so sánh theo trạng thái promo
2. **Hành vi trả hàng (Customer Returns)**
   - KPI: số lượt trả, tổng hoàn tiền, median days-to-return
   - Phân tích lý do trả hàng, danh mục hoàn tiền cao
3. **Tồn kho & hết hàng (Inventory & Stockouts)**
   - KPI: estimated lost revenue, overstock capital, stockout rate
   - Trend theo tháng, top category thất thoát, scatter phân bố tồn kho

Mỗi tab có block:
- **Nhận xét chính**
- **Tác động kinh doanh**
- **Khuyến nghị hành động**

## 5. Cách chạy dự án

### 5.1 Chạy dbt pipeline

```bash
dbt seed
dbt run
dbt test
```

Tùy chọn sinh docs:

```bash
dbt docs generate
dbt docs serve
```

### 5.2 Chạy dashboard Streamlit

```bash
streamlit run streamlit_app.py
```

Theme dashboard được cấu hình tại:
- `.streamlit/config.toml`

## 6. Kiểm soát chất lượng dữ liệu

Các kiểm tra hiện có:
1. **`unique`** cho khóa định danh chính (vd: `product_id`, `order_id`, `return_id`)
2. **`not_null`** cho cột bắt buộc
3. **`relationships`** cho các khóa ngoại giữa bảng

Schema tests được khai báo tại:
- `models/staging/_stg_model.yml`
- `models/marts/_mart_model.yml`
