"""Input loading and documented, conservative OWID-compatible cleaning."""
from __future__ import annotations
from io import BytesIO
import pandas as pd
import requests
SOURCE_URL = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
REQUIRED = {"location", "date"}
NUMERIC = ["population","new_cases","total_cases","new_deaths","total_deaths","people_vaccinated","people_vaccinated_per_hundred","people_fully_vaccinated","people_fully_vaccinated_per_hundred","new_vaccinations"]

def load_csv(source, **kwargs):
    if hasattr(source, "read"):
        return pd.read_csv(source, **kwargs)
    return pd.read_csv(source, **kwargs)

def fetch_owid(timeout=30):
    response=requests.get(SOURCE_URL, timeout=timeout)
    response.raise_for_status()
    return pd.read_csv(BytesIO(response.content))

def clean_data(df):
    if df is None or not isinstance(df,pd.DataFrame): raise ValueError("Provide a CSV dataset as a pandas DataFrame.")
    if df.empty: raise ValueError("The uploaded dataset is empty.")
    df=df.copy()
    if "location" not in df.columns and "country" in df.columns:
        df=df.rename(columns={"country":"location"})
    missing=REQUIRED-set(df.columns)
    if missing: raise ValueError("Missing required column(s): " + ", ".join(sorted(missing)))
    out=df.copy()
    out["location"]=out["location"].astype("string").str.strip()
    out["date"]=pd.to_datetime(out["date"], errors="coerce", utc=True).dt.tz_localize(None)
    out=out.dropna(subset=["location","date"])
    out=out[out.location.ne("")]
    out=out.drop_duplicates(subset=["location","date"],keep="last")
    for col in NUMERIC:
        if col in out:
            out[col]=pd.to_numeric(out[col],errors="coerce")
            # Negative counts are invalid; preserve missingness rather than imputing zero.
            if col in ("new_cases","total_cases","new_deaths","total_deaths","people_vaccinated","new_vaccinations"):
                out.loc[out[col]<0,col]=float("nan")
            if col in ("population",): out.loc[out[col]<=0,col]=float("nan")
    if "people_vaccinated_per_hundred" in out:
        out.loc[~out.people_vaccinated_per_hundred.between(0,100),"people_vaccinated_per_hundred"]=float("nan")
    if "people_fully_vaccinated_per_hundred" in out:
        out.loc[~out.people_fully_vaccinated_per_hundred.between(0,100),"people_fully_vaccinated_per_hundred"]=float("nan")
    out=out.sort_values(["location","date"],kind="stable").reset_index(drop=True)
    return out

def filter_data(df, countries=None, start=None, end=None, continent=None):
    out=df.copy()
    if countries: out=out[out.location.isin(countries)]
    if start is not None: out=out[out.date>=pd.Timestamp(start)]
    if end is not None: out=out[out.date<=pd.Timestamp(end)]
    if continent and "continent" in out: out=out[out.continent.isin(continent)]
    return out
