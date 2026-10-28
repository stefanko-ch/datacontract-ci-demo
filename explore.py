import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    import duckdb
    import marimo as mo

    con = duckdb.connect("shop.duckdb", read_only=True)
    return con, mo


@app.cell
def _(mo):
    mo.md("""## The synthetic web shop in DuckDB: `sales.orders`""")
    return


@app.cell
def _(con, mo):
    _orders = mo.sql(
        """
        SELECT order_id, customer_id, order_ts, status, total_chf
        FROM sales.orders
        ORDER BY order_id
        LIMIT 8
        """,
        engine=con,
    )
    return


@app.cell
def _(con, mo):
    _status = mo.sql(
        """
        SELECT status, count(*) AS orders
        FROM sales.orders
        GROUP BY status
        ORDER BY orders DESC
        """,
        engine=con,
    )
    return


if __name__ == "__main__":
    app.run()
