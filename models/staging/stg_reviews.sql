WITH source AS (
    SELECT * FROM {{ ref('reviews') }}
),
renamed AS (
    SELECT
        review_id,
        order_id,
        product_id,
        customer_id,
        CAST(review_date AS DATE) AS review_date,
        rating,
        review_title
    FROM source
)
SELECT * FROM renamed