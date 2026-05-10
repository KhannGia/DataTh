WITH source AS (
    SELECT * FROM {{ ref('order_items') }}
),
renamed AS (
    SELECT
        order_id,
        product_id,
        quantity,
        unit_price,
        discount_amount,
        promo_id,
        promo_id_2
    FROM source
)
SELECT * FROM renamed