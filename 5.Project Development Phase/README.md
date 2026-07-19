# Plugging into the Future — Electricity Consumption Project

Everything needed to run this project end-to-end is in this folder. The outputs
(cleaned data, dashboard, query results) have already been generated once —
you can open them right away, or re-run the two scripts yourself to rebuild
them from scratch.

## Folder guide

```
data/
  Consumption.csv              <- raw source data
  consumption_cleaned.csv      <- cleaned data with calculated fields (output)
  electricity_consumption.db   <- SQLite database (output)
sql/
  pipeline.sql                 <- all SQL: cleaning, calculated fields, dashboard queries
scripts/
  prepare_data.py              <- Step 1: cleans data, builds the dashboard
  run_sql_pipeline.py          <- Step 2: runs the SQL, saves query results
dashboard/
  index.html                   <- the finished interactive dashboard (OPEN THIS)
  index_template.html          <- template the script fills in (don't open directly)
output_tables/
  *.csv                        <- one CSV per dashboard view/query (output)
docs/
  Project_Documentation.docx   <- full write-up
  video_script.md              <- narration script for the demo video
```

## Quickest path: just look at the result

Double-click **`dashboard/index.html`** — it opens in your browser and needs
nothing else installed. (It loads one chart library from the internet the
first time, so you'll need a connection for that.)

## Running it yourself in VS Code

1. **Open the folder**: File → Open Folder → select this folder.
2. **Open a terminal**: Terminal → New Terminal (or `` Ctrl+` ``).
3. **Step 1 — clean the data & rebuild the dashboard:**
   ```
   pip install pandas
   python scripts/prepare_data.py
   ```
   This regenerates `data/consumption_cleaned.csv` and `dashboard/index.html`
   from the raw CSV. (Skip `pip install pandas` if you already have it.)

4. **Step 2 — run the SQL:**
   ```
   python scripts/run_sql_pipeline.py
   ```
   This builds `data/electricity_consumption.db` using Python's built-in
   SQLite (no database server to install) and writes every query result
   into `output_tables/`.

   If `python` doesn't work, try `python3` instead.

5. **View the result:** open `dashboard/index.html` in your browser, or open
   any file in `output_tables/` in Excel.

## Using a real SQL database instead (optional)

If your course specifically requires MySQL, `sql/pipeline.sql` is written in
SQLite syntax for easy local running. The original MySQL-flavored version
(`LOAD DATA INFILE`, `CREATE TABLE ... AS SELECT`, indexes) is the same
logic — ask if you'd like that version regenerated instead.

## Connecting to Tableau

Point Tableau Desktop at either:
- `data/consumption_cleaned.csv` (Data → Connect to File → Text File), or
- `data/electricity_consumption.db` if you have a SQLite connector installed,
  using the `consumption_final` table.

Both already contain the calculated fields (Year, Quarter, LockdownPeriod,
CityType) described in the documentation.
