WITH source AS (
    SELECT * FROM {{ ref('shipments') }}
),
renamed AS (
    SELECT
        order_id,
        CAST(ship_date AS DATE) AS ship_date,
        CAST(delivery_date AS DATE) AS delivery_date,
        shipping_fee
    FROM source
)
SELECT * FROM renamed