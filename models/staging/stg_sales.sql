WITH source AS (
    SELECT * FROM {{ ref('sales') }}
),
renamed AS (
    SELECT
        CAST("Date" AS DATE) AS sales_date,
        "Revenue" AS revenue,
        "COGS" AS cogs
    FROM source
)
SELECT * FROM renamed