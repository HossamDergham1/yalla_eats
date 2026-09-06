CREATE DATABASE IF NOT EXISTS `staging`;

CREATE VIEW IF NOT EXISTS `staging`.`stg_users` AS
SELECT
    `user_id`,
    `signup_date`,
    CASE 
        WHEN lower(trim(city)) IN ('cario', 'cairo') THEN 'Cairo'
        WHEN lower(trim(city)) IN ('northsinai', 'north  sinai', 'sinai') THEN 'North Sinai'
        WHEN lower(trim(city)) IN ('giza', 'gizaa', 'giiza') THEN 'Giza'
        WHEN lower(trim(city)) IN ('alex', 'alexandria', 'alaxandria') THEN 'Alexandria'
        ELSE 'Unknown'
    END AS `clean_city`,
    `acquisition_channel`
FROM `raw`.`users`;

CREATE VIEW IF NOT EXISTS `staging`.`stg_orders` AS
SELECT
    `order_id`,
    `user_id`,
    `restaurant_id`,
    `order_timestamp`,
    `status`,
    `total` AS `order_revenue`,
    `platform`,
    `basket_size`
FROM `raw`.`orders`;

CREATE VIEW IF NOT EXISTS `staging`.`stg_order_items` AS
SELECT
    `item_id`,
    `order_id`,
    `product_id`,
    `quantity`,
    `price`,
    (`quantity` * `price`) AS `item_revenue`
FROM `raw`.`order_items`;
