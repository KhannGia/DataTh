WITH source AS (
    SELECT * FROM {{ ref('geography') }}
),
renamed AS (
    SELECT
        zip,
        city,
        region,
        district
    FROM source
)
SELECT * FROM renamed