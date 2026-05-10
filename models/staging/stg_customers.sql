WITH source AS (
    SELECT * FROM {{ ref('customers') }}
),
renamed AS (
    SELECT
        customer_id,
        zip,
        city,
        CAST(signup_date AS DATE) AS signup_date,
        gender,
        age_group,
        acquisition_channel
    FROM source
)
SELECT * FROM renamed