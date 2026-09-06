import os
import random
import time
import mysql.connector
from datetime import datetime, timedelta

# Configuration from environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "app_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "app_password")
MYSQL_DB = os.getenv("MYSQL_DB", "app_db")
NUM_USERS = int(os.getenv("NUM_USERS", "3000"))
NUM_ORDERS = int(os.getenv("NUM_ORDERS", "9000"))

CITIES_CLEAN = ["Cairo", "North Sinai", "Giza", "Alexandria"]
CITY_NOISE_MAP = {
    "Cairo": ["Cario", "CAIRO", " Cairo", None],
    "North Sinai": ["Northsinai", "North  Sinai", "Sinai", None],
    "Giza": ["GIZA", "Gizaa", "GIIZA"],
    "Alexandria": ["Alex", "alexandria", "Alaxandria"]
}
ACQUISITION_CHANNELS = ["organic", "paid_search", "facebook_ads", "referral", "discount_code"]
PLATFORMS = ["ios", "android", "web"]
CATEGORIES = {
    "Burgers": ["Classic Cheeseburger", "Bacon Smash Burger", "Veggie Burger", "Fries"],
    "Sushi": ["Salmon Roll", "Tuna Sashimi", "Spicy Tempura Roll", "Edamame"],
    "Pizza": ["Margherita", "Pepperoni", "Garlic Knots", "Caesar Salad"]
}

def get_db_connection():
    while True:
        try:
            # First connect without database parameter to ensure database creation
            conn = mysql.connector.connect(
                host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB};")
            cursor.close()
            conn.close()

            # Connect directly to target database
            conn = mysql.connector.connect(
                host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Waiting for MySQL initialization... ({err})")
            time.sleep(3)

def init_schema(cursor):
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("DROP TABLE IF EXISTS experiment_exposures, experiment_assignments, order_items, orders, products, restaurants, users;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    cursor.execute("""
        CREATE TABLE users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            signup_date DATETIME NOT NULL,
            city VARCHAR(100),
            acquisition_channel VARCHAR(50)
        );
    """)
    cursor.execute("""
        CREATE TABLE restaurants (
            restaurant_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            city VARCHAR(100),
            category VARCHAR(50)
        );
    """)
    cursor.execute("""
        CREATE TABLE products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            restaurant_id INT,
            name VARCHAR(100),
            price DECIMAL(10, 2),
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            restaurant_id INT,
            order_timestamp DATETIME,
            status VARCHAR(20),
            total DECIMAL(10, 2),
            platform VARCHAR(20),
            basket_size INT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE order_items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT,
            product_id INT,
            quantity INT,
            price DECIMAL(10,2),
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE experiment_assignments (
            assignment_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            experiment_name VARCHAR(50),
            variant VARCHAR(20),
            assigned_at DATETIME NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE experiment_exposures (
            exposure_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            experiment_name VARCHAR(50),
            exposed_at DATETIME NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

def generate_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    init_schema(cursor)

    # 1. Generate Users
    user_ids = []
    user_cities = {}
    print(f"Generating {NUM_USERS} users...")
    start_date = datetime.now() - timedelta(days=90)
    for i in range(1, NUM_USERS + 1):
        clean_city = random.choice(CITIES_CLEAN)
        noisy_city = random.choice(CITY_NOISE_MAP[clean_city])
        signup_date = start_date + timedelta(seconds=random.randint(0, 30 * 86400))
        channel = random.choice(ACQUISITION_CHANNELS)
        cursor.execute(
            "INSERT INTO users (signup_date, city, acquisition_channel) VALUES (%s, %s, %s)",
            (signup_date, noisy_city, channel)
        )
        user_ids.append(i)
        user_cities[i] = clean_city

    # 2. Generate Restaurants & Products
    restaurant_products = {}
    print("Generating restaurants & products...")
    for category, prod_list in CATEGORIES.items():
        for city in CITIES_CLEAN:
            cursor.execute(
                "INSERT INTO restaurants (name, city, category) VALUES (%s, %s, %s)",
                (f"{city} {category} House", city, category)
            )
            rest_id = cursor.lastrowid
            restaurant_products[rest_id] = []
            for item in prod_list:
                price = round(random.uniform(4.0, 18.0), 2)
                cursor.execute(
                    "INSERT INTO products (restaurant_id, name, price) VALUES (%s, %s, %s)",
                    (rest_id, item, price)
                )
                restaurant_products[rest_id].append((cursor.lastrowid, price))

    # 3. Generate Experiment Assignments & Exposures
    print("Generating experiment data...")
    exposed_treatment_users = set()
    for uid in user_ids:
        variant = "treatment" if random.random() < 0.5 else "control"
        assigned_at = start_date + timedelta(days=5)
        cursor.execute(
            "INSERT INTO experiment_assignments (user_id, experiment_name, variant, assigned_at) VALUES (%s, %s, %s, %s)",
            (uid, "xsell_reco_v1", variant, assigned_at)
        )
        # 60% of assigned users get exposed to the carousel
        if random.random() < 0.60:
            exposed_at = assigned_at + timedelta(hours=random.randint(1, 48))
            cursor.execute(
                "INSERT INTO experiment_exposures (user_id, experiment_name, exposed_at) VALUES (%s, %s, %s)",
                (uid, "xsell_reco_v1", exposed_at)
            )
            if variant == "treatment":
                exposed_treatment_users.add(uid)

    # 4. Generate Orders & Order Items
    print(f"Generating {NUM_ORDERS} orders...")
    rest_ids_by_city = {}
    cursor.execute("SELECT restaurant_id, city FROM restaurants")
    for r_id, r_city in cursor.fetchall():
        rest_ids_by_city.setdefault(r_city, []).append(r_id)

    for _ in range(NUM_ORDERS):
        uid = random.choice(user_ids)
        u_city = user_cities[uid]
        rest_id = random.choice(rest_ids_by_city[u_city])
        available_products = restaurant_products[rest_id]

        order_time = start_date + timedelta(seconds=random.randint(35 * 86400, 90 * 86400))
        status = random.choices(["completed", "cancelled", "refunded"], weights=[0.88, 0.08, 0.04])[0]
        platform = random.choice(PLATFORMS)

        # Apply treatment effect: Exposed treatment users are significantly more likely to select 2+ items
        if uid in exposed_treatment_users and random.random() < 0.70:
            item_count = random.randint(2, 4)
        else:
            item_count = random.choices([1, 2, 3], weights=[0.65, 0.25, 0.10])[0]

        chosen_prods = random.sample(available_products, min(item_count, len(available_products)))
        
        cursor.execute(
            "INSERT INTO orders (user_id, restaurant_id, order_timestamp, status, total, platform, basket_size) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (uid, rest_id, order_time, status, 0.0, platform, len(chosen_prods))
        )
        order_id = cursor.lastrowid
        
        order_total = 0.0
        for p_id, p_price in chosen_prods:
            qty = random.randint(1, 2)
            item_total = p_price * qty
            order_total += item_total
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, p_id, qty, p_price)
            )

        cursor.execute("UPDATE orders SET total = %s WHERE order_id = %s", (round(order_total, 2), order_id))

    conn.commit()
    cursor.close()
    conn.close()
    print("Data generation complete!")

if __name__ == "__main__":
    generate_data()
