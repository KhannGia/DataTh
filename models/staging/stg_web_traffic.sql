WITH source AS (
    SELECT * FROM {{ ref('web_traffic') }}
),
renamed AS (
    SELECT
        CAST(date AS DATE) AS traffic_date,
        sessions,
        unique_visitors,
        page_views,
        bounce_rate,
        avg_session_duration_sec,
        traffic_source
    FROM source
)
SELECT * FROM renamed