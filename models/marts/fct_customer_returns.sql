WITH returns_data AS (
    SELECT * FROM {{ ref('stg_returns') }}
),
orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),
products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

joined_returns AS (
    SELECT
        r.return_id,
        r.order_id,
        r.product_id,
        r.return_date,
        r.return_reason,
        r.return_quantity,
        r.refund_amount,
        
        o.order_date,
        o.order_source,
        
        c.customer_id,
        c.gender,
        c.age_group,
        
        p.product_name,
        p.category,
        p.segment,
        p.price,
        
        -- Tính số ngày từ lúc đặt hàng đến lúc trả hàng
        -- (Trong Postgres, trừ 2 cột DATE sẽ ra số nguyên là số ngày)
        (r.return_date - o.order_date) AS days_to_return
        
    FROM returns_data r
    JOIN orders o ON r.order_id = o.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN products p ON r.product_id = p.product_id
)

SELECT * FROM joined_returns