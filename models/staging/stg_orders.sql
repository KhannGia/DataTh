-- 1. Gọi dữ liệu thô từ seed lên
WITH source AS (
    SELECT * FROM {{ ref('orders') }} -- 'orders' là tên file orders.csv
),

-- 2. Đổi tên cột, làm sạch, ép kiểu (nếu cần)
renamed AS (
    SELECT 
        order_id,
        customer_id,
        zip,
        order_status,
        payment_method,
        device_type,
        order_source,
        -- Có thể ép kiểu thống nhất tại đây, ví dụ:
        CAST(order_date AS DATE) AS order_date
    FROM source
)

-- 3. Xuất kết quả
SELECT * FROM renamed