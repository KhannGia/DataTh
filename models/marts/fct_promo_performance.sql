WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),
promotions AS (
    SELECT * FROM {{ ref('stg_promotions') }}
),
products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

joined_data AS (
    SELECT
        o.order_id,
        o.order_date,
        o.customer_id,
        p.product_id,
        p.category,
        p.segment,
        p.cogs,
        oi.quantity,
        oi.unit_price,
        oi.discount_amount,
        oi.promo_id,
        oi.promo_id_2,
        pr1.promo_type,
        pr1.stackable_flag,
        
        -- 1. Tính toán Doanh thu thô (Chưa trừ khuyến mãi)
        (oi.unit_price * oi.quantity) AS gross_revenue,
        
        -- 2. Tính toán Doanh thu thuần (Đã trừ khuyến mãi)
        ((oi.unit_price * oi.quantity) - oi.discount_amount) AS net_revenue,
        
        -- 3. Tính toán Tổng giá vốn
        (p.cogs * oi.quantity) AS total_cogs
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN promotions pr1 ON oi.promo_id = pr1.promo_id
)

SELECT
    *,
    -- Lợi nhuận gộp (Tiền mang về sau khi trừ vốn)
    (net_revenue - total_cogs) AS gross_profit,
    
    -- Tỷ suất lợi nhuận gộp (%)
    CASE
        WHEN net_revenue > 0 THEN (net_revenue - total_cogs) / net_revenue
        ELSE 0
    END AS gross_margin_pct,
    
    -- Gắn nhãn trạng thái khuyến mãi để dễ vẽ biểu đồ
    CASE
        WHEN promo_id IS NOT NULL AND promo_id_2 IS NOT NULL THEN 'Stacked (Cộng dồn)'
        WHEN promo_id IS NOT NULL THEN 'Single (Đơn lẻ)'
        ELSE 'No Promo (Nguyên giá)'
    END AS promo_status
FROM joined_data