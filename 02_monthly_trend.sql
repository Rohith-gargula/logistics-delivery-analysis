-- Monthly on-time delivery rate and volume
SELECT
    strftime('%Y-%m', order_purchase_timestamp)                AS month,
    COUNT(*)                                                   AS orders,
    ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date <= order_estimated_delivery_date
                           THEN 1 ELSE 0 END) / COUNT(*), 2)   AS on_time_pct,
    ROUND(AVG(julianday(order_delivered_customer_date)
            - julianday(order_purchase_timestamp)), 2)         AS avg_delivery_days
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
GROUP BY month
HAVING COUNT(*) >= 100
ORDER BY month;
