# datacontract-ci-demo

A minimal example of a data contract in CI: an [ODCS](https://bitol-io.github.io/open-data-contract-standard/) contract
(`orders.odcs.yaml`) for a small, synthetic web shop in DuckDB – orders, order lines, customers and products – checked on every pull request with the
[datacontract CLI](https://github.com/datacontract/datacontract-cli):

1. **lint** – is the contract valid ODCS v3.2.0?
2. **breaking** – does the contract change break consumers (compared with the base branch)?
3. **test** – does the data that `make_data.py` produces keep the contract?

Written for the article
[Open Data Contract Standard: writing down what your data promises](https://medium.com/@stefanko-ch/open-data-contract-standard-writing-down-what-your-data-promises-c037fabe235a).
The two open pull requests are the two stories from the post: [#1](https://github.com/stefanko-ch/datacontract-ci-demo/pull/1) changes the data, [#2](https://github.com/stefanko-ch/datacontract-ci-demo/pull/2)
changes the contract – both turn CI red.

## What's in it

| File | What it is |
|---|---|
| `orders.odcs.yaml` | The data contract for `sales.orders`, `sales.order_items`, `sales.customers` and `sales.products`, with the relationships between them |
| `make_data.py` | Stands in for the producer: writes 5,000 synthetic orders, their order lines, 800 customers and 300 products into `shop.duckdb` |
| `explore.py` | A [marimo](https://marimo.io) notebook to look at the data |
| `.github/workflows/data-contract.yml` | lint, breaking and test on every pull request |
| `pyproject.toml`, `uv.lock` | The pinned dependencies, installed with uv |

All data is synthetic and generated on the fly. `shop.duckdb` is not part of the repository (`.gitignore`).

## Setup

You need [git](https://git-scm.com) and [uv](https://docs.astral.sh/uv/getting-started/installation/). uv brings the
right Python version (`.python-version`) and all dependencies:

```bash
git clone https://github.com/stefanko-ch/datacontract-ci-demo.git
cd datacontract-ci-demo
uv sync
```

## Run the checks

```bash
uv run python make_data.py                   # 5000 orders, 12537 order lines, 800 customers, 300 products
uv run datacontract lint orders.odcs.yaml    # is the contract valid ODCS?
uv run datacontract test orders.odcs.yaml    # does the data keep the contract?
```

Both end green; `test` reports `Data contract is valid. Ran 61 checks.`

## Replay the two pull requests locally

Fetch the pull requests as local branches; the commands below take single files from them, so you stay on `main`:

```bash
git fetch origin pull/1/head:pr-1 pull/2/head:pr-2
```

**#1 – the data changes.** The shop writes `cancelled` instead of `canceled`:

```bash
git checkout pr-1 -- make_data.py
uv run python make_data.py
uv run datacontract test orders.odcs.yaml    # red: invalid_count(status) was 1276, expected = 0
git checkout main -- make_data.py            # back to the original producer
uv run python make_data.py
```

**#2 – the contract changes.** Version 2.0.0 drops `customer_id`:

```bash
git show pr-2:orders.odcs.yaml > v2.odcs.yaml
uv run datacontract breaking orders.odcs.yaml v2.odcs.yaml    # red: Removed schema.orders.properties.customer_id
rm v2.odcs.yaml
```

## Look at the data with marimo

marimo is only needed for looking, so it's in its own dependency group:

```bash
uv run --group explore marimo edit explore.py
```

This starts marimo and opens the notebook in your browser (`http://localhost:2718`, the terminal shows the link with an
access token). The notebook shows the first orders and the orders per status. In the browser:

| Key (macOS / Windows, Linux) | What it does |
|---|---|
| `Cmd+Enter` / `Ctrl+Enter` | Run the current cell |
| `Shift+Enter` | Run the cell and add a new one below |
| `Cmd+Shift+R` / `Ctrl+Shift+R` | Run all stale cells |
| `Cmd+I` / `Ctrl+I` | Stop a running cell |
| `Cmd+.` / `Ctrl+.` | Switch between code and app view |
| `Cmd+K` / `Ctrl+K` | Command palette – every action, searchable |
| `Cmd+S` / `Ctrl+S` | Save the notebook |

marimo is reactive: change a SQL query and run the cell, and every cell that uses its result runs again by itself.
To try your own query, add a cell with `Shift+Enter` and write, for example:

```python
_df = mo.sql("SELECT status, round(sum(total_chf)) AS revenue FROM sales.orders GROUP BY status", engine=con)
```

Without the code, as a read-only page: `uv run --group explore marimo run explore.py`.

Stop marimo with `Ctrl+C` in the terminal. **Stop it before running `make_data.py` again** – the notebook holds a
read-only connection to `shop.duckdb`, and DuckDB won't let `make_data.py` open the file for writing meanwhile
(`Could not set lock on file "shop.duckdb": Conflicting lock is held …`).

## Edit the contract in the Data Contract Editor

The [Data Contract Editor](https://github.com/datacontract/datacontract-editor) shows the same contract as forms and a
diagram. The CLI brings it along; the `explore` group adds the `api` extra its local server needs:

```bash
uv run --group explore datacontract edit orders.odcs.yaml
```

It opens `http://localhost:4243` in your browser, works offline, and *Save* writes back to `orders.odcs.yaml`.

- **Form** – every section of the contract; click a property (e.g. `status`) to see its types and quality rules.
- **Diagram** – the tables; hover a column and drag its dot to a column of the other table to add a relationship,
  e.g. `order_items.order_id` → `orders.order_id`.
- **YAML** – the file itself, with a diff of your changes.
- **Validation** – the contract against the ODCS schema, as you type.
- **Tests** – *Run Test* runs the contract tests against the DuckDB file. Run `make_data.py` first.
- **Preview** – the contract as an HTML page.

Saving reformats the whole file (quotes, text blocks). To see what changed in the contract rather than in the text:

```bash
git show HEAD:orders.odcs.yaml > before.odcs.yaml
uv run datacontract changelog before.odcs.yaml orders.odcs.yaml
```

Without Python, the editor also runs as a container – standalone, with an example contract; open and save files
through the browser:

```bash
docker run -d -p 4173:4173 datacontract/editor
```

## In CI

`.github/workflows/data-contract.yml` installs uv with `astral-sh/setup-uv`, runs `uv sync --locked` – the exact
versions from `uv.lock` – and then lint, breaking (on pull requests only) and `datacontract ci`, which is `test` with
GitHub annotations for every failed check.

License: MIT
