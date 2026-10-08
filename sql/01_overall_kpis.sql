-- Overall delivery KPIs (delivered orders only)
SELECT
    COUNT(*)                                                   AS delivered_orders,
    ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date <= order_estimated_delivery_date
                           THEN 1 ELSE 0 END) / COUNT(*), 2)   AS on_time_pct,
    ROUND(AVG(julianday(order_delivered_customer_date)
            - julianday(order_purchase_timestamp)), 2)         AS avg_delivery_days,
    ROUND(AVG(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date
                   THEN julianday(order_delivered_customer_date)
                      - julianday(order_estimated_delivery_date) END), 2) AS avg_days_late_when_late
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;
