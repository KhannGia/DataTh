WITH source AS (
    SELECT * FROM {{ ref('inventory') }}
),
renamed AS (
    SELECT
        CAST(snapshot_date AS DATE) AS snapshot_date,
        product_id,
        stock_on_hand,
        units_received,
        units_sold,
        stockout_days,
        days_of_supply,
        fill_rate,
        stockout_flag,
        overstock_flag,
        reorder_flag,
        sell_through_rate,
        product_name,
        category,
        segment,
        year,
        month
    FROM source
)
SELECT * FROM renamed