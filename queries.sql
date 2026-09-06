-- Query 1: Daily completed orders, revenue, and AOV
SELECT
    toDate(order_timestamp) AS order_date,
    count(DISTINCT order_id) AS completed_orders,
    round(sum(item_revenue), 2) AS total_revenue,
    round(total_revenue / completed_orders, 2) AS avg_order_value
FROM marts.fct_order_items
WHERE status = 'completed'
GROUP BY order_date
ORDER BY order_date;

-- Query 2: Top 10 products by revenue & system-wide cross-sell rate
SELECT
    product_id,
    product_name,
    round(sum(item_revenue), 2) AS total_revenue
FROM marts.fct_order_items
WHERE status = 'completed'
GROUP BY product_id, product_name
ORDER BY total_revenue DESC
LIMIT 10;

WITH order_product_counts AS (
    SELECT
        order_id,
        count(DISTINCT product_id) AS distinct_products
    FROM marts.fct_order_items
    WHERE status = 'completed'
    GROUP BY order_id
)
SELECT
    round(countIf(distinct_products >= 2) / count() * 100, 2) AS cross_sell_rate_pct
FROM order_product_counts;

-- Query 3: User-level summary
SELECT
    user_id,
    count(DISTINCT order_id) AS completed_orders,
    count(DISTINCT product_id) AS distinct_products_purchased
FROM marts.fct_order_items
WHERE status = 'completed'
GROUP BY user_id;
