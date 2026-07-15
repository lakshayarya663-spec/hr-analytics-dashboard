-- ============================================================
-- HR Analytics Dashboard - Turnover & Workforce Optimization Reports
-- ============================================================

-- ------------------------------------------------------------
-- 1. Overall attrition (turnover) rate
-- ------------------------------------------------------------
SELECT
    COUNT(*)                                              AS total_employees,
    SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END)    AS attrited_employees,
    ROUND(100.0 * SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS attrition_rate_pct
FROM employees;


-- ------------------------------------------------------------
-- 2. Turnover rate by department, ranked highest to lowest
-- ------------------------------------------------------------
SELECT
    department,
    COUNT(*)                                              AS headcount,
    SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END)    AS attrited,
    ROUND(100.0 * SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS attrition_rate_pct
FROM employees
GROUP BY department
ORDER BY attrition_rate_pct DESC;


-- ------------------------------------------------------------
-- 3. Turnover rate by job role (top attrition-risk roles)
-- ------------------------------------------------------------
SELECT
    job_role,
    department,
    COUNT(*)                                              AS headcount,
    ROUND(100.0 * SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS attrition_rate_pct
FROM employees
GROUP BY job_role, department
HAVING COUNT(*) >= 10
ORDER BY attrition_rate_pct DESC
LIMIT 10;


-- ------------------------------------------------------------
-- 4. Turnover by tenure bucket (new-hire flight risk check)
-- ------------------------------------------------------------
SELECT
    CASE
        WHEN years_at_company <= 1 THEN '0-1 yrs'
        WHEN years_at_company <= 3 THEN '2-3 yrs'
        WHEN years_at_company <= 5 THEN '4-5 yrs'
        WHEN years_at_company <= 10 THEN '6-10 yrs'
        ELSE '10+ yrs'
    END AS tenure_bucket,
    COUNT(*) AS headcount,
    ROUND(100.0 * SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS attrition_rate_pct
FROM employees
GROUP BY tenure_bucket
ORDER BY MIN(years_at_company);


-- ------------------------------------------------------------
-- 5. Overtime vs attrition (workload risk factor)
-- ------------------------------------------------------------
SELECT
    over_time,
    COUNT(*) AS headcount,
    ROUND(100.0 * SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS attrition_rate_pct,
    ROUND(AVG(job_satisfaction), 2) AS avg_job_satisfaction,
    ROUND(AVG(work_life_balance), 2) AS avg_work_life_balance
FROM employees
GROUP BY over_time;


-- ------------------------------------------------------------
-- 6. Salary band vs attrition (compensation risk factor)
-- ------------------------------------------------------------
WITH salary_quartiles AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY monthly_income) AS salary_quartile
    FROM employees
)
SELECT
    CASE salary_quartile
        WHEN 1 THEN 'Q1 - Low'
        WHEN 2 THEN 'Q2 - Mid-Low'
        WHEN 3 THEN 'Q3 - Mid-High'
        WHEN 4 THEN 'Q4 - High'
    END AS salary_band,
    COUNT(*) AS headcount,
    ROUND(AVG(monthly_income), 0) AS avg_income,
    ROUND(100.0 * SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS attrition_rate_pct
FROM salary_quartiles
GROUP BY salary_quartile
ORDER BY salary_quartile;


-- ------------------------------------------------------------
-- 7. Workforce optimization: headcount vs. avg performance vs.
--    attrition risk, by department (spot over/under-staffed,
--    under-performing, or high-risk departments)
-- ------------------------------------------------------------
SELECT
    department,
    COUNT(*)                                                       AS headcount,
    ROUND(AVG(performance_rating), 2)                              AS avg_performance_rating,
    ROUND(AVG(job_satisfaction), 2)                                AS avg_job_satisfaction,
    ROUND(AVG(monthly_income), 0)                                  AS avg_monthly_income,
    ROUND(100.0 * SUM(CASE WHEN attrition='Yes' THEN 1 ELSE 0 END)/COUNT(*), 2) AS attrition_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN over_time='Yes' THEN 1 ELSE 0 END)/COUNT(*), 2) AS pct_on_overtime
FROM employees
GROUP BY department
ORDER BY attrition_rate_pct DESC;


-- ------------------------------------------------------------
-- 8. High-risk employee watchlist (still active, multiple risk
--    factors present) — feeds a retention-outreach report
-- ------------------------------------------------------------
SELECT
    employee_id,
    department,
    job_role,
    years_at_company,
    monthly_income,
    job_satisfaction,
    work_life_balance,
    over_time,
    distance_from_home
FROM employees
WHERE attrition = 'No'
  AND over_time = 'Yes'
  AND job_satisfaction <= 2
  AND years_at_company <= 3
ORDER BY years_at_company ASC, job_satisfaction ASC;


-- ------------------------------------------------------------
-- 9. Hiring vs attrition trend by year (workforce growth check)
-- ------------------------------------------------------------
SELECT
    CAST(strftime('%Y', hire_date) AS INTEGER)                      AS hire_year,   -- SQLite date fn
    -- PostgreSQL equivalent: EXTRACT(YEAR FROM hire_date) AS hire_year
    COUNT(*)                                                        AS hires,
    SUM(CASE WHEN attrition = 'Yes' THEN 1 ELSE 0 END)              AS subsequent_attritions
FROM employees
GROUP BY hire_year
ORDER BY hire_year;


-- ------------------------------------------------------------
-- 10. Gender pay gap check by department
-- ------------------------------------------------------------
SELECT
    department,
    ROUND(AVG(CASE WHEN gender = 'Male' THEN monthly_income END), 0)   AS avg_male_income,
    ROUND(AVG(CASE WHEN gender = 'Female' THEN monthly_income END), 0) AS avg_female_income,
    ROUND(
        100.0 * (
            AVG(CASE WHEN gender = 'Male' THEN monthly_income END) -
            AVG(CASE WHEN gender = 'Female' THEN monthly_income END)
        ) / AVG(CASE WHEN gender = 'Male' THEN monthly_income END), 2
    ) AS pay_gap_pct
FROM employees
GROUP BY department
ORDER BY pay_gap_pct DESC;
