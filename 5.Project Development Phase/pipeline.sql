-- ============================================================
-- SQLite version of the project's SQL steps
-- (Run this via run_sql_pipeline.py — no MySQL install needed)
-- ============================================================

DROP TABLE IF EXISTS consumption_raw;
CREATE TABLE consumption_raw (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    State       TEXT NOT NULL,
    Region      TEXT NOT NULL,
    Latitude    REAL,
    Longitude   REAL,
    UsageDate   TEXT NOT NULL,   -- stored as 'YYYY-MM-DD'
    Usage_MU    REAL NOT NULL
);

-- (Data is loaded by the Python script, not LOAD DATA INFILE —
--  SQLite has no equivalent statement.)

-- ------------------------------------------------------------
-- Clean & deduplicate
-- ------------------------------------------------------------
DELETE FROM consumption_raw
WHERE id NOT IN (
    SELECT MIN(id) FROM consumption_raw GROUP BY State, UsageDate
);

DELETE FROM consumption_raw WHERE Usage_MU IS NULL OR Usage_MU <= 0;

-- ------------------------------------------------------------
-- Build the analysis-ready table with calculated fields
-- ------------------------------------------------------------
DROP TABLE IF EXISTS consumption_final;
CREATE TABLE consumption_final AS
SELECT
    id,
    State,
    Region,
    Latitude,
    Longitude,
    UsageDate,
    CAST(strftime('%Y', UsageDate) AS INTEGER) AS Yr,
    CAST(strftime('%m', UsageDate) AS INTEGER) AS MonthNum,
    CASE strftime('%m', UsageDate)
        WHEN '01' THEN 'January' WHEN '02' THEN 'February' WHEN '03' THEN 'March'
        WHEN '04' THEN 'April'   WHEN '05' THEN 'May'      WHEN '06' THEN 'June'
        WHEN '07' THEN 'July'    WHEN '08' THEN 'August'   WHEN '09' THEN 'September'
        WHEN '10' THEN 'October' WHEN '11' THEN 'November' WHEN '12' THEN 'December'
    END AS MonthName,
    'Q' || ((CAST(strftime('%m', UsageDate) AS INTEGER) + 2) / 3) AS Quarter,
    CASE WHEN UsageDate >= '2020-03-25'
         THEN 'After Lockdown' ELSE 'Before Lockdown' END AS LockdownPeriod,
    CASE WHEN State IN ('Delhi','Maharashtra','Tamil Nadu',
                         'West Bengal','Karnataka','Telangana')
         THEN 'Metro' ELSE 'Non-Metro' END AS CityType,
    Usage_MU
FROM consumption_raw;

CREATE INDEX idx_state  ON consumption_final (State);
CREATE INDEX idx_region ON consumption_final (Region);
CREATE INDEX idx_year   ON consumption_final (Yr);

-- ============================================================
-- Reference queries behind each dashboard view
-- ============================================================

-- 2019 State Consumption
SELECT State, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final WHERE Yr = 2019
GROUP BY State ORDER BY Total_Usage DESC;

-- 2020 State Consumption
SELECT State, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final WHERE Yr = 2020
GROUP BY State ORDER BY Total_Usage DESC;

-- Total Consumption (all years, by state)
SELECT State, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY State ORDER BY Total_Usage DESC;

-- Usage by Region
SELECT Region, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY Region ORDER BY Total_Usage DESC;

-- Total Region Consumption by Year
SELECT Region, Yr, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY Region, Yr ORDER BY Region, Yr;

-- Top 5 states
SELECT State, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY State ORDER BY Total_Usage DESC LIMIT 5;

-- Bottom 5 states
SELECT State, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY State ORDER BY Total_Usage ASC LIMIT 5;

-- 2019 vs 2020 Month-wise Consumption
SELECT MonthNum, MonthName, Yr, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY MonthNum, MonthName, Yr ORDER BY MonthNum, Yr;

-- Usage Before vs After Lockdown
SELECT LockdownPeriod, ROUND(SUM(Usage_MU),1) AS Total_Usage, ROUND(AVG(Usage_MU),2) AS Avg_Daily_Usage
FROM consumption_final GROUP BY LockdownPeriod;

-- Quarter-wise Usage
SELECT Quarter, Yr, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY Quarter, Yr ORDER BY Yr, Quarter;

-- Metro vs Non-Metro State Usage
SELECT CityType, State, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY CityType, State ORDER BY CityType, Total_Usage DESC;

-- Usage by Year (overall trend)
SELECT Yr, ROUND(SUM(Usage_MU),1) AS Total_Usage
FROM consumption_final GROUP BY Yr ORDER BY Yr;
