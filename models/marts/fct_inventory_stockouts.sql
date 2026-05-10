WITH inventory AS (
    SELECT * FROM {{ ref('stg_inventory') }}
),
products AS (
    SELECT * FROM {{ ref('stg_products') }}
),
inventory_enriched AS (
    SELECT
        i.snapshot_date,
        i.product_id,
        i.product_name,
        i.category,
        i.segment,
        i.stock_on_hand,
        i.units_sold,
        i.stockout_days,
        i.overstock_flag,
        i.sell_through_rate,
        p.price,
        p.cogs,
        
        -- 1. Tính toán Doanh thu trung bình mỗi ngày (khi còn hàng)
        -- Công thức: Số lượng bán / (Số ngày trong tháng - Số ngày hết hàng)
        CASE 
            WHEN (30 - i.stockout_days) > 0 
            THEN (i.units_sold * 1.0) / (30 - i.stockout_days)
            ELSE 0 
        END AS avg_daily_sales_volume,

        -- 2. Ước tính Doanh thu bị mất (Estimated Lost Revenue) do hết hàng
        -- Công thức: Doanh số ngày * Số ngày hết hàng * Giá bán
        (CASE 
            WHEN (30 - i.stockout_days) > 0 
            THEN (i.units_sold * 1.0) / (30 - i.stockout_days)
            ELSE 0 
        END) * i.stockout_days * p.price AS est_lost_revenue,

        -- 3. Giá trị vốn ứ đọng (Overstock Value)
        -- Công thức: Số lượng tồn kho * Giá vốn
        CASE 
            WHEN i.overstock_flag = TRUE THEN i.stock_on_hand * p.cogs
            ELSE 0 
        END AS overstock_capital_value

    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
)

SELECT * FROM inventory_enriched