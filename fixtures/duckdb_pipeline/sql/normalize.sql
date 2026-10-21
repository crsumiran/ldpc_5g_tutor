CREATE TABLE clean_orders AS
SELECT
    order_id,
    CAST(order_date AS TIMESTAMP) AS ts_utc,
    amount
FROM raw_orders
WHERE order_id IS NOT NULL;
