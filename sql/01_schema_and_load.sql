-- ============================================================
-- HR Analytics Dashboard - Schema & Load
-- Compatible with SQLite / PostgreSQL (minor type tweaks noted)
-- ============================================================

DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    employee_id             TEXT PRIMARY KEY,
    age                     INTEGER,
    gender                  TEXT,
    marital_status          TEXT,
    department              TEXT,
    job_role                TEXT,
    education                INTEGER,           -- 1=Below College ... 5=Doctorate
    education_field         TEXT,
    business_travel         TEXT,
    distance_from_home      INTEGER,
    monthly_income          NUMERIC,
    percent_salary_hike     INTEGER,
    stock_option_level      INTEGER,
    over_time               TEXT,               -- 'Yes'/'No'
    total_working_years     INTEGER,
    years_at_company        INTEGER,
    years_in_current_role   INTEGER,
    years_since_last_promo  INTEGER,
    num_companies_worked    INTEGER,
    training_times_last_yr  INTEGER,
    job_satisfaction        INTEGER,            -- 1-4
    environment_satisfaction INTEGER,           -- 1-4
    work_life_balance       INTEGER,            -- 1-4
    job_involvement         INTEGER,            -- 1-4
    performance_rating      INTEGER,            -- 1-4
    hire_date                DATE,
    attrition               TEXT                -- 'Yes'/'No'
);

-- SQLite: load via the .import CSV utility, e.g.
--   sqlite3 hr.db
--   .mode csv
--   .import --skip 1 data/hr_employee_data.csv employees
--
-- PostgreSQL:
--   \copy employees FROM 'data/hr_employee_data.csv' WITH (FORMAT csv, HEADER true);
-- (Column order in the source CSV matches the CREATE TABLE column order above.)
