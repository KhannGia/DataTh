WITH source AS (
    SELECT * FROM {{ ref('payments') }}
),
renamed AS (
    SELECT
        order_id,
        payment_method,
        payment_value,
        installments
    FROM source
)
SELECT * FROM renamed