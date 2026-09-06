CREATE DATABASE IF NOT EXISTS marts;

-- User Dimension
CREATE TABLE IF NOT EXISTS marts.dim_users
(
    user_id Int32,
    signup_date DateTime,
    clean_city String,
    acquisition_channel String
)
ENGINE = ReplacingMergeTree()
ORDER BY user_id;

TRUNCATE TABLE IF EXISTS marts.dim_users;

INSERT INTO marts.dim_users
SELECT 
    user_id, 
    signup_date, 
    clean_city, 
    acquisition_channel
FROM `staging`.stg_users;

-- Fact Order Items One Big Table (OBT)
CREATE TABLE IF NOT EXISTS marts.fct_order_items
(
    item_id Int32,
    order_id Int32,
    product_id Int32,
    product_name String,
    restaurant_category String,
    user_id Int32,
    user_city String,
    acquisition_channel String,
    restaurant_id Int32,
    order_timestamp DateTime,
    status String,
    platform String,
    quantity Int32,
    unit_price Float64,
    item_revenue Float64,
    order_revenue Float64,
    exp_variant Nullable(String),
    assigned_at Nullable(DateTime),
    exposed_at Nullable(DateTime),
    is_exp_exposed UInt8
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(order_timestamp)
ORDER BY (status, order_timestamp, user_id, order_id);

TRUNCATE TABLE IF EXISTS `marts`.`fct_order_items`;

INSERT INTO `marts`.`fct_order_items`
SELECT
    `items`.`item_id` AS `item_id`,
    `items`.`order_id` AS `order_id`,
    `items`.`product_id` AS `product_id`,
    `products`.`name` AS `product_name`,
    `restaurants`.`category` AS `restaurant_category`,
    `orders`.`user_id` AS `user_id`,
    `users`.`clean_city` AS `user_city`,
    `users`.`acquisition_channel` AS `acquisition_channel`,
    `orders`.`restaurant_id` AS `restaurant_id`,
    `orders`.`order_timestamp` AS `order_timestamp`,
    `orders`.`status` AS `status`,
    `orders`.`platform` AS `platform`,
    `items`.`quantity` AS `quantity`,
    `items`.`price` AS `unit_price`,
    `items`.`item_revenue` AS `item_revenue`,
    `orders`.`order_revenue` AS `order_revenue`,
    `assignment`.`variant` AS `exp_variant`,
    `assignment`.`assigned_at` AS `assigned_at`,
    `exposure`.`exposed_at` AS `exposed_at`,
    if(`exposure`.`exposure_id` > 0 AND `exposure`.`exposed_at` IS NOT NULL AND `exposure`.`exposed_at` <= `orders`.`order_timestamp`, 1, 0) AS `is_exp_exposed`
FROM `staging`.`stg_order_items` AS `items`
INNER JOIN `staging`.`stg_orders` AS `orders`
    ON `items`.`order_id` = `orders`.`order_id`
LEFT JOIN `staging`.`stg_users` AS `users`
    ON `orders`.`user_id` = `users`.`user_id`
LEFT JOIN `raw`.`products` AS `products`
    ON `items`.`product_id` = `products`.`product_id`
LEFT JOIN `raw`.`restaurants` AS `restaurants`
    ON `orders`.`restaurant_id` = `restaurants`.`restaurant_id`
LEFT JOIN `raw`.`experiment_assignments` AS `assignment`
    ON `orders`.`user_id` = `assignment`.`user_id` 
    AND `assignment`.`experiment_name` = 'xsell_reco_v1'
LEFT JOIN `raw`.`experiment_exposures` AS `exposure`
    ON `orders`.`user_id` = `exposure`.`user_id` 
    AND `exposure`.`experiment_name` = 'xsell_reco_v1';
