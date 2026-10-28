"""Generates a small, synthetic web shop in DuckDB: orders, order lines, customers and products.

Stands in for the producer – the application or pipeline that writes the data.
"""
import duckdb

STATUSES = ["placed", "shipped", "delivered", "canceled"]

con = duckdb.connect("shop.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS sales")
con.execute("SELECT setseed(0.42)")
con.execute(f"""
CREATE OR REPLACE TABLE sales.orders AS
SELECT
    'O-' || lpad(i::VARCHAR, 6, '0')                                AS order_id,
    'C-' || lpad((1 + floor(random() * 800))::INT::VARCHAR, 5, '0') AS customer_id,
    now()::TIMESTAMP - INTERVAL (floor(random() * 30 * 24 * 60)::INT) MINUTE AS order_ts,
    ({STATUSES})[1 + floor(random() * {len(STATUSES)})::INT]        AS status,
    round(10 + random() * 490, 2)                                   AS total_chf
FROM range(1, 5001) t(i)
""")
con.execute("""
CREATE OR REPLACE TABLE sales.order_items AS
SELECT o.order_id, n AS line_no,
       'SKU-' || lpad((1 + floor(random() * 300))::INT::VARCHAR, 4, '0') AS sku,
       (1 + floor(random() * 4))::INT AS quantity
FROM sales.orders o, range(1, 2 + (hash(o.order_id) % 4)::INT) t(n)
""")
# Created after orders and order lines, so those stay the same rows as before.
con.execute("""
CREATE OR REPLACE TABLE sales.customers AS
SELECT
    'C-' || lpad(i::VARCHAR, 5, '0')                                AS customer_id,
    (['private', 'business'])[1 + floor(random() * 2)::INT]         AS segment,
    (['CH', 'DE', 'AT'])[1 + floor(random() * 3)::INT]              AS country,
    DATE '2020-01-01' + floor(random() * 2000)::INT                 AS customer_since
FROM range(1, 801) t(i)
""")
con.execute("""
CREATE OR REPLACE TABLE sales.products AS
SELECT
    'SKU-' || lpad(i::VARCHAR, 4, '0')                              AS sku,
    (['books', 'games', 'garden', 'kitchen', 'toys'])[1 + floor(random() * 5)::INT] AS category,
    round(5 + random() * 195, 2)                                    AS price_chf
FROM range(1, 301) t(i)
""")
orders, items, customers, products = con.execute(
    "SELECT (SELECT COUNT(*) FROM sales.orders), (SELECT COUNT(*) FROM sales.order_items), "
    "(SELECT COUNT(*) FROM sales.customers), (SELECT COUNT(*) FROM sales.products)"
).fetchone()
print(f"{orders} orders, {items} order lines, {customers} customers, {products} products")
