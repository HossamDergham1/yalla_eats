-- check 50/50 split across variants
SELECT
    `exp_variant`,
    count(DISTINCT user_id) AS `assigned_users`,
    round(`assigned_users` / sum(`assigned_users`) OVER (), 4) AS `assignment_share`
FROM `marts`.`fct_order_items`
WHERE `exp_variant` IS NOT NULL
GROUP BY `exp_variant`



-- check exposure rate

SELECT
    `exp_variant`,
    count(DISTINCT `user_id`) AS `total_assigned_users`,
    uniqExactIf(`user_id`, `is_exp_exposed` = 1) AS `exposed_users`,
    round(`exposed_users` / `total_assigned_users` * 100, 2) AS `exposure_rate_pct`
FROM `marts`.`fct_order_items`
WHERE `exp_variant` IS NOT NULL
GROUP BY `exp_variant`


--  evaluation of treatment effect on the exposed population

WITH `order_summary` AS (
    SELECT
        `order_id`,
        `user_id`,
        `exp_variant`,
        `is_exp_exposed`,
        count() AS `item_count`,                  -- counts distinct items in the order
        sum(quantity) AS `total_item_quantity`,   -- sums total units in the order
        any(order_revenue) AS `order_total_spend` -- deduplicates order_revenue per order
    FROM `marts`.`fct_order_items`
    WHERE status = 'completed' 
      AND `exp_variant` IS NOT NULL
    GROUP BY `order_id`, `user_id`, `exp_variant`, `is_exp_exposed`
),
`user_metrics` AS (
    SELECT
        `user_id`,
        `exp_variant`,
        `is_exp_exposed`,
        count(`order_id`) AS `completed_orders`,
        countIf(`item_count` >= 2) AS `multi_item_orders`,
        sum(`order_total_spend`) AS `total_spend`
    FROM `order_summary`
    GROUP BY `user_id`, `exp_variant`, `is_exp_exposed`
)
SELECT
    `exp_variant`,
    `is_exp_exposed`,
    count(`user_id`) AS `sample_size`,
    round(avg(`completed_orders`), 2) AS `avg_orders_per_user`,
    round(sum(`multi_item_orders`) / sum(`completed_orders`) * 100, 2) AS `cross_sell_order_pct`,
    round(avg(`total_spend`), 2) AS `avg_revenue_per_user`
FROM `user_metrics`
GROUP BY `exp_variant`, `is_exp_exposed`
ORDER BY `exp_variant`, `is_exp_exposed`