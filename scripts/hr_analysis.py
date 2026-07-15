"""
hr_analysis.py
--------------
HR Analytics Dashboard - Core analysis engine.

Performs:
  1. Data preprocessing (missing values, type fixes, outlier handling)
  2. Feature engineering (tenure buckets, salary bands, attrition risk score, age groups)
  3. Attrition pattern analysis
  4. Salary distribution analysis
  5. Workforce diversity analysis
  6. Department-wise performance metrics

Outputs cleaned data + summary CSVs to /outputs, ready for SQL loading
and for the Tableau / dashboard layer.
"""

import numpy as np
import pandas as pd

pd.set_option("display.width", 120)

RAW_PATH = "/home/claude/hr_project/data/hr_employee_data.csv"
CLEAN_PATH = "/home/claude/hr_project/outputs/hr_data_clean.csv"
OUT_DIR = "/home/claude/hr_project/outputs"


# ---------------------------------------------------------------------------
# 1. LOAD + PREPROCESS
# ---------------------------------------------------------------------------
def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["HireDate"])

    # --- Handle missing values ---
    df["MonthlyIncome"] = df["MonthlyIncome"].fillna(
        df.groupby("Department")["MonthlyIncome"].transform("median")
    )
    for col in ["JobSatisfaction", "EnvironmentSatisfaction"]:
        df[col] = df[col].fillna(df[col].median())

    # --- Type fixes ---
    int_cols = ["Age", "DistanceFromHome", "MonthlyIncome", "PercentSalaryHike",
                "TotalWorkingYears", "YearsAtCompany", "YearsInCurrentRole",
                "YearsSinceLastPromotion", "NumCompaniesWorked", "TrainingTimesLastYear",
                "JobSatisfaction", "EnvironmentSatisfaction", "WorkLifeBalance",
                "JobInvolvement", "PerformanceRating", "StockOptionLevel", "Education"]
    for col in int_cols:
        df[col] = df[col].round().astype(int)

    # --- Outlier capping (winsorize extreme monthly income at 1st/99th pct) ---
    lo, hi = df["MonthlyIncome"].quantile([0.01, 0.99])
    df["MonthlyIncome"] = df["MonthlyIncome"].clip(lo, hi)

    # --- Drop exact duplicate rows if any ---
    df = df.drop_duplicates(subset="EmployeeID")

    return df


# ---------------------------------------------------------------------------
# 2. FEATURE ENGINEERING
# ---------------------------------------------------------------------------
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Tenure buckets
    df["TenureBucket"] = pd.cut(
        df["YearsAtCompany"],
        bins=[-1, 1, 3, 5, 10, 100],
        labels=["0-1 yrs", "2-3 yrs", "4-5 yrs", "6-10 yrs", "10+ yrs"]
    )

    # Age groups
    df["AgeGroup"] = pd.cut(
        df["Age"],
        bins=[17, 24, 34, 44, 54, 100],
        labels=["18-24", "25-34", "35-44", "45-54", "55+"]
    )

    # Salary bands
    df["SalaryBand"] = pd.qcut(
        df["MonthlyIncome"], q=4, labels=["Low", "Mid-Low", "Mid-High", "High"]
    )

    # Binary attrition flag for numeric aggregation
    df["AttritionFlag"] = (df["Attrition"] == "Yes").astype(int)

    # Education level label
    edu_map = {1: "Below College", 2: "College", 3: "Bachelor", 4: "Master", 5: "Doctorate"}
    df["EducationLevel"] = df["Education"].map(edu_map)

    # Composite Attrition Risk Score (0-100), a weighted heuristic used for
    # prioritizing retention outreach — NOT a trained model, but a transparent,
    # explainable score built from known HR risk factors.
    risk = (
        (df["OverTime"] == "Yes").astype(int) * 25
        + (df["JobSatisfaction"] <= 2).astype(int) * 20
        + (df["WorkLifeBalance"] == 1).astype(int) * 15
        + (df["YearsAtCompany"] <= 1).astype(int) * 15
        + (df["DistanceFromHome"] > 20).astype(int) * 10
        + (df["MonthlyIncome"] < df["MonthlyIncome"].quantile(0.25)).astype(int) * 15
    )
    df["AttritionRiskScore"] = risk.clip(0, 100)
    df["RiskTier"] = pd.cut(
        df["AttritionRiskScore"], bins=[-1, 20, 45, 100],
        labels=["Low Risk", "Medium Risk", "High Risk"]
    )

    # Tenure in months as of a fixed "today" for reporting consistency
    today = pd.Timestamp("2024-12-31")
    df["TenureMonths"] = ((today - df["HireDate"]).dt.days / 30.44).round(1)

    return df


# ---------------------------------------------------------------------------
# 3-6. ANALYSIS BLOCKS
# ---------------------------------------------------------------------------
def attrition_analysis(df: pd.DataFrame) -> dict:
    out = {}
    out["overall_rate"] = df["AttritionFlag"].mean() * 100
    out["by_department"] = (
        df.groupby("Department")["AttritionFlag"].mean().mul(100).round(2)
        .sort_values(ascending=False).rename("AttritionRate%")
    )
    out["by_tenure_bucket"] = (
        df.groupby("TenureBucket", observed=True)["AttritionFlag"].mean().mul(100).round(2)
        .rename("AttritionRate%")
    )
    out["by_overtime"] = (
        df.groupby("OverTime")["AttritionFlag"].mean().mul(100).round(2)
        .rename("AttritionRate%")
    )
    out["by_risk_tier"] = (
        df.groupby("RiskTier", observed=True)["AttritionFlag"].mean().mul(100).round(2)
        .rename("AttritionRate%")
    )
    out["by_jobrole"] = (
        df.groupby("JobRole")["AttritionFlag"].mean().mul(100).round(2)
        .sort_values(ascending=False).rename("AttritionRate%")
    )
    return out


def salary_analysis(df: pd.DataFrame) -> dict:
    out = {}
    out["overall_stats"] = df["MonthlyIncome"].describe().round(1)
    out["by_department"] = (
        df.groupby("Department")["MonthlyIncome"].agg(["mean", "median", "std"]).round(1)
        .sort_values("mean", ascending=False)
    )
    out["by_gender"] = (
        df.groupby("Gender")["MonthlyIncome"].agg(["mean", "median", "count"]).round(1)
    )
    out["gender_pay_gap_pct"] = round(
        (1 - out["by_gender"].loc["Female", "mean"] / out["by_gender"].loc["Male", "mean"]) * 100, 2
    )
    out["by_jobrole"] = (
        df.groupby("JobRole")["MonthlyIncome"].mean().round(1).sort_values(ascending=False)
    )
    return out


def diversity_analysis(df: pd.DataFrame) -> dict:
    out = {}
    out["gender_mix"] = df["Gender"].value_counts(normalize=True).mul(100).round(2)
    out["gender_by_department"] = (
        pd.crosstab(df["Department"], df["Gender"], normalize="index").mul(100).round(2)
    )
    out["age_group_mix"] = df["AgeGroup"].value_counts(normalize=True).mul(100).round(2).sort_index()
    out["education_mix"] = df["EducationLevel"].value_counts(normalize=True).mul(100).round(2)
    out["marital_status_mix"] = df["MaritalStatus"].value_counts(normalize=True).mul(100).round(2)
    return out


def department_performance(df: pd.DataFrame) -> pd.DataFrame:
    perf = df.groupby("Department", observed=True).agg(
        Headcount=("EmployeeID", "count"),
        AvgPerformanceRating=("PerformanceRating", "mean"),
        AvgJobSatisfaction=("JobSatisfaction", "mean"),
        AvgEnvSatisfaction=("EnvironmentSatisfaction", "mean"),
        AvgWorkLifeBalance=("WorkLifeBalance", "mean"),
        AvgTenureYears=("YearsAtCompany", "mean"),
        AttritionRatePct=("AttritionFlag", lambda x: x.mean() * 100),
        AvgMonthlyIncome=("MonthlyIncome", "mean"),
    ).round(2).sort_values("AttritionRatePct", ascending=False)
    return perf


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    df = load_and_clean(RAW_PATH)
    df = engineer_features(df)
    df.to_csv(CLEAN_PATH, index=False)
    print(f"Clean + feature-engineered dataset saved -> {CLEAN_PATH}  ({len(df)} rows, {df.shape[1]} cols)")

    attr = attrition_analysis(df)
    sal = salary_analysis(df)
    div = diversity_analysis(df)
    perf = department_performance(df)

    print("\n=== ATTRITION ===")
    print(f"Overall attrition rate: {attr['overall_rate']:.2f}%")
    print("\nBy Department:\n", attr["by_department"])
    print("\nBy Tenure Bucket:\n", attr["by_tenure_bucket"])
    print("\nBy OverTime:\n", attr["by_overtime"])
    print("\nBy Risk Tier:\n", attr["by_risk_tier"])

    print("\n=== SALARY ===")
    print(sal["overall_stats"])
    print("\nBy Department:\n", sal["by_department"])
    print(f"\nGender pay gap (Female vs Male, mean): {sal['gender_pay_gap_pct']}%")

    print("\n=== DIVERSITY ===")
    print("Gender mix (%):\n", div["gender_mix"])
    print("\nAge group mix (%):\n", div["age_group_mix"])
    print("\nEducation mix (%):\n", div["education_mix"])

    print("\n=== DEPARTMENT PERFORMANCE ===")
    print(perf)

    # Persist summary tables for the SQL layer / dashboard / reporting
    attr["by_department"].to_csv(f"{OUT_DIR}/attrition_by_department.csv")
    attr["by_tenure_bucket"].to_csv(f"{OUT_DIR}/attrition_by_tenure.csv")
    attr["by_jobrole"].to_csv(f"{OUT_DIR}/attrition_by_jobrole.csv")
    sal["by_department"].to_csv(f"{OUT_DIR}/salary_by_department.csv")
    div["gender_by_department"].to_csv(f"{OUT_DIR}/gender_by_department.csv")
    perf.to_csv(f"{OUT_DIR}/department_performance.csv")
    print(f"\nSummary tables written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
