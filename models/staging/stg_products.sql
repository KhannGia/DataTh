WITH source AS (
    SELECT * FROM {{ ref('products') }}
),
renamed AS (
    SELECT
        product_id,
        product_name,
        category,
        segment,
        size,
        color,
        price,
        cogs
    FROM source
)
SELECT * FROM renamed