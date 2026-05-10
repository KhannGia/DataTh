SELECT
  c.customer_id,
  c.city,
  COUNT(DISTINCT o.order_id) AS total_orders,
  COALESCE(SUM(p.payment_value), 0) AS total_spent,
  MAX(o.order_date) AS last_order_date
FROM dbt_user.customers c
LEFT JOIN dbt_user.orders o
  ON o.customer_id = c.customer_id
LEFT JOIN dbt_user.payments p
  ON p.order_id = o.order_id
GROUP BY c.customer_id, c.city
ORDER BY total_spent DESC;


SELECT column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_schema = 'dbt_user'
  AND table_name = 'orders'
ORDER BY ordinal_position;