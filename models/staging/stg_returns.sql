WITH source AS (
    SELECT * FROM {{ ref('returns') }}
),
renamed AS (
    SELECT
        return_id,
        order_id,
        product_id,
        CAST(return_date AS DATE) AS return_date,
        return_reason,
        return_quantity,
        refund_amount
    FROM source
)
SELECT * FROM renamed