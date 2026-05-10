WITH source AS (
    SELECT * FROM {{ ref('promotions') }}
),
renamed AS (
    SELECT
        promo_id,
        promo_name,
        promo_type,
        discount_value,
        CAST(start_date AS DATE) AS start_date,
        CAST(end_date AS DATE) AS end_date,
        applicable_category,
        promo_channel,
        stackable_flag,
        min_order_value
    FROM source
)
SELECT * FROM renamed