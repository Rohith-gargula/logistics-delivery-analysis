-- Where does the time go? Average days per fulfilment stage,
-- split by on-time vs late orders.
SELECT
    CASE WHEN order_delivered_customer_date <= order_estimated_delivery_date
         THEN 'On time' ELSE 'Late' END                        AS delivery_status,
    COUNT(*)                                                   AS orders,
    ROUND(AVG(julianday(order_approved_at)
            - julianday(order_purchase_timestamp)), 2)         AS days_to_approval,
    ROUND(AVG(julianday(order_delivered_carrier_date)
            - julianday(order_approved_at)), 2)                AS days_to_carrier_handover,
    ROUND(AVG(julianday(order_delivered_customer_date)
            - julianday(order_delivered_carrier_date)), 2)     AS days_in_transit
FROM orders
WHERE order_status = 'delivered'
  AND order_approved_at IS NOT NULL
  AND order_delivered_carrier_date IS NOT NULL
  AND order_delivered_customer_date IS NOT NULL
GROUP BY delivery_status;
