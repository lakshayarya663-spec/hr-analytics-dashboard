"""
generate_data.py
-----------------
Generates a realistic synthetic HR dataset for the HR Analytics Dashboard project.
Modeled loosely on common HR analytics data structures (IBM HR Attrition-style),
but fully synthetic and randomly generated.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

N = 1500

departments = {
    "Sales": ["Sales Executive", "Sales Representative", "Manager"],
    "Research & Development": ["Research Scientist", "Laboratory Technician",
                                "Manufacturing Director", "Research Director"],
    "Human Resources": ["HR Executive", "HR Specialist", "Manager"],
    "Finance": ["Financial Analyst", "Accountant", "Finance Manager"],
    "IT": ["Software Engineer", "Data Analyst", "IT Support", "IT Manager"],
    "Marketing": ["Marketing Executive", "Marketing Analyst", "Manager"],
}

education_fields = ["Life Sciences", "Medical", "Marketing", "Technical Degree",
                     "Human Resources", "Business", "Other"]
education_levels = [1, 2, 3, 4, 5]  # 1=Below College ... 5=Doctorate
marital_status = ["Single", "Married", "Divorced"]
genders = ["Male", "Female"]

rows = []
for emp_id in range(1, N + 1):
    dept = np.random.choice(list(departments.keys()), p=[0.32, 0.30, 0.08, 0.12, 0.12, 0.06])
    role = np.random.choice(departments[dept])

    age = int(np.clip(np.random.normal(37, 9), 18, 60))
    gender = np.random.choice(genders, p=[0.60, 0.40])
    marital = np.random.choice(marital_status, p=[0.32, 0.48, 0.20])
    education = np.random.choice(education_levels, p=[0.05, 0.22, 0.38, 0.27, 0.08])
    edu_field = np.random.choice(education_fields)

    years_at_company = int(np.clip(np.random.exponential(5), 0, age - 18))
    years_in_role = int(np.clip(np.random.exponential(2.5), 0, years_at_company))
    years_since_promo = int(np.clip(np.random.exponential(1.5), 0, years_at_company))
    total_working_years = int(np.clip(years_at_company + np.random.exponential(3), 0, age - 18))

    # Base salary depends on department, role seniority (years) and education
    base_pay = {
        "Sales": 4800, "Research & Development": 5200, "Human Resources": 4200,
        "Finance": 5500, "IT": 5800, "Marketing": 4700
    }[dept]
    monthly_income = int(np.clip(
        base_pay + years_at_company * 180 + education * 250 + np.random.normal(0, 900),
        2400, 20000
    ))

    distance_from_home = int(np.clip(np.random.exponential(8), 1, 29))
    overtime = np.random.choice(["Yes", "No"], p=[0.30, 0.70])
    business_travel = np.random.choice(
        ["Non-Travel", "Travel_Rarely", "Travel_Frequently"], p=[0.20, 0.60, 0.20]
    )

    job_satisfaction = np.random.choice([1, 2, 3, 4], p=[0.15, 0.20, 0.30, 0.35])
    env_satisfaction = np.random.choice([1, 2, 3, 4], p=[0.15, 0.20, 0.30, 0.35])
    work_life_balance = np.random.choice([1, 2, 3, 4], p=[0.10, 0.25, 0.45, 0.20])
    job_involvement = np.random.choice([1, 2, 3, 4], p=[0.10, 0.25, 0.45, 0.20])
    performance_rating = np.random.choice([1, 2, 3, 4], p=[0.03, 0.12, 0.65, 0.20])
    training_times_last_year = int(np.random.choice(range(0, 7)))
    num_companies_worked = int(np.clip(np.random.poisson(2.5), 0, 9))
    percent_salary_hike = int(np.clip(np.random.normal(15, 4), 11, 25))
    stock_option_level = np.random.choice([0, 1, 2, 3], p=[0.45, 0.35, 0.15, 0.05])

    # Attrition probability driven by realistic factors
    attr_score = 0.06
    if overtime == "Yes":
        attr_score += 0.16
    if job_satisfaction <= 2:
        attr_score += 0.10
    if work_life_balance == 1:
        attr_score += 0.10
    if years_at_company <= 1:
        attr_score += 0.10
    if monthly_income < 3500:
        attr_score += 0.08
    if distance_from_home > 20:
        attr_score += 0.05
    if age < 25:
        attr_score += 0.06
    if marital == "Single":
        attr_score += 0.05
    attr_score = np.clip(attr_score, 0.02, 0.85)
    attrition = np.random.choice(["Yes", "No"], p=[attr_score, 1 - attr_score])

    hire_year = 2024 - years_at_company
    hire_month = np.random.randint(1, 13)
    hire_date = pd.Timestamp(year=int(np.clip(hire_year, 2005, 2024)), month=int(hire_month), day=1)

    rows.append({
        "EmployeeID": f"E{emp_id:05d}",
        "Age": age,
        "Gender": gender,
        "MaritalStatus": marital,
        "Department": dept,
        "JobRole": role,
        "Education": education,
        "EducationField": edu_field,
        "BusinessTravel": business_travel,
        "DistanceFromHome": distance_from_home,
        "MonthlyIncome": monthly_income,
        "PercentSalaryHike": percent_salary_hike,
        "StockOptionLevel": stock_option_level,
        "OverTime": overtime,
        "TotalWorkingYears": total_working_years,
        "YearsAtCompany": years_at_company,
        "YearsInCurrentRole": years_in_role,
        "YearsSinceLastPromotion": years_since_promo,
        "NumCompaniesWorked": num_companies_worked,
        "TrainingTimesLastYear": training_times_last_year,
        "JobSatisfaction": job_satisfaction,
        "EnvironmentSatisfaction": env_satisfaction,
        "WorkLifeBalance": work_life_balance,
        "JobInvolvement": job_involvement,
        "PerformanceRating": performance_rating,
        "HireDate": hire_date.strftime("%Y-%m-%d"),
        "Attrition": attrition,
    })

df = pd.DataFrame(rows)

# Introduce a small amount of realistic missingness for the preprocessing step to handle
for col in ["MonthlyIncome", "JobSatisfaction", "EnvironmentSatisfaction"]:
    mask = np.random.rand(len(df)) < 0.015
    df.loc[mask, col] = np.nan

out_path = "/home/claude/hr_project/data/hr_employee_data.csv"
df.to_csv(out_path, index=False)
print(f"Generated {len(df)} rows -> {out_path}")
print(df["Attrition"].value_counts(normalize=True))
