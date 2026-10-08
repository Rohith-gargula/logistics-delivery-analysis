-- Customer review score vs delivery outcome
WITH order_review AS (
    SELECT order_id, AVG(review_score) AS review_score
    FROM reviews
    GROUP BY order_id
)
SELECT
    CASE WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
         THEN 'On time' ELSE 'Late' END                        AS delivery_status,
    COUNT(*)                                                   AS orders,
    ROUND(AVG(r.review_score), 2)                              AS avg_review_score,
    ROUND(100.0 * SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_negative_reviews
FROM orders o
JOIN order_review r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY delivery_status;
