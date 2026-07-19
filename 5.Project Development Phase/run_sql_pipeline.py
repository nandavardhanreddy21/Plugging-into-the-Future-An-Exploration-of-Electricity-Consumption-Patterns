"""
Step 2 of the pipeline: runs the SQL (via SQLite - no server to install).

HOW TO RUN (in VS Code terminal, from the project folder):
    python scripts/run_sql_pipeline.py

WHAT IT DOES:
  - Reads data/Consumption.csv
  - Creates a local database file: data/electricity_consumption.db
  - Runs every step in sql/pipeline.sql: cleaning, calculated fields,
    and the reference query behind each dashboard view
  - Prints each query's results in the terminal
  - Saves each query's results as its own CSV in output_tables/
"""

import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
CSV_PATH = ROOT / "data" / "Consumption.csv"
SQL_PATH = ROOT / "sql" / "pipeline.sql"
DB_PATH = ROOT / "data" / "electricity_consumption.db"
OUT_DIR = ROOT / "output_tables"


def load_csv_into_sqlite(conn):
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            day, month, year = r["Dates"].split("/")
            iso_date = f"{year}-{month}-{day}"
            rows.append((
                r["States"], r["Regions"],
                float(r["latitude"]), float(r["longitude"]),
                iso_date, float(r["Usage"]),
            ))
    conn.executemany(
        "INSERT INTO consumption_raw (State, Region, Latitude, Longitude, UsageDate, Usage_MU) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    print(f"Loaded {len(rows)} rows from {CSV_PATH.name}")


def split_sql_statements(sql_text):
    statements = []
    current_label = None
    buffer = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            comment = stripped.lstrip("-").strip()
            if comment and not comment.startswith("="):
                current_label = comment
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(buffer).strip()
            if stmt:
                statements.append((current_label, stmt))
            buffer = []
            current_label = None
    return statements


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: Couldn't find {CSV_PATH}. Make sure data/Consumption.csv exists.")
        return

    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    OUT_DIR.mkdir(exist_ok=True)

    sql_text = SQL_PATH.read_text(encoding="utf-8")
    statements = split_sql_statements(sql_text)

    query_count = 0
    for label, stmt in statements:
        stmt_upper = stmt.upper().strip()

        if stmt_upper.startswith("CREATE TABLE CONSUMPTION_RAW"):
            conn.execute(stmt)
            load_csv_into_sqlite(conn)
            conn.commit()
            continue

        if stmt_upper.startswith("SELECT"):
            query_count += 1
            cur = conn.execute(stmt)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()

            title = label or f"Query {query_count}"
            print(f"\n=== {title} ===")
            print(", ".join(cols))
            for row in rows[:15]:
                print(row)
            if len(rows) > 15:
                print(f"... ({len(rows)} rows total, showing first 15)")

            safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()
            out_path = OUT_DIR / f"{safe_name}.csv"
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                writer.writerows(rows)
        else:
            conn.execute(stmt)
            conn.commit()

    conn.close()
    print(f"\nDone. Database saved to {DB_PATH.relative_to(ROOT)}")
    print(f"{query_count} query results saved as CSVs in {OUT_DIR.name}/")


if __name__ == "__main__":
    main()
