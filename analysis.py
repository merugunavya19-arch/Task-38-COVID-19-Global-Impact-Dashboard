"""Metrics and result-derived summaries; missing values are never blanket-filled."""
import numpy as np
import pandas as pd

def engineer_metrics(df):
    d=df.copy()
    for metric, numerator in [("cases_per_million","total_cases"),("deaths_per_million","total_deaths")]:
        if numerator in d and "population" in d:
            d[metric]=np.where(d.population>0,d[numerator]/d.population*1_000_000,np.nan)
    if "total_cases" in d and "total_deaths" in d:
        d["case_fatality_rate_pct"]=np.where(d.total_cases>0,d.total_deaths/d.total_cases*100,np.nan)
    for col in ("new_cases","new_deaths"):
        if col in d: d[col+"_7d_avg"]=d.groupby("location",dropna=False)[col].transform(lambda s:s.rolling(7,min_periods=7).mean())
    if "new_cases_7d_avg" not in d and "cases_7d_avg" in d:
        d["new_cases_7d_avg"]=d["cases_7d_avg"]
    # Doubling time only when positive counts are growing over an explicit 7-day interval.
    if "total_cases" in d:
        def doubling(group):
            x=group.sort_values("date").set_index("date")["total_cases"]
            past=x.reindex(x.index-pd.Timedelta(days=7)).to_numpy()
            now=x.to_numpy(); growth=np.log(np.divide(now,past,out=np.full(len(now),np.nan),where=(now>0)&(past>0)))
            days=np.where(growth>0,7*np.log(2)/growth,np.nan)
            return pd.Series(days,index=x.index)
        pieces=[]
        for _,g in d.groupby("location",sort=False):
            t=doubling(g); pieces.append(pd.DataFrame({"date":t.index,"location":g.location.iloc[0],"doubling_time_days":t.values}))
        if pieces:
            z=pd.concat(pieces); d=d.merge(z,on=["location","date"],how="left")
    return d

def country_summary(df):
    if df.empty:return pd.DataFrame()
    rows=[]
    for country,g in df.sort_values("date").groupby("location"):
        row={"location":country,"latest_date":g.date.max()}
        for col in ("total_cases","total_deaths","population","people_vaccinated_per_hundred","people_fully_vaccinated_per_hundred","cases_per_million","deaths_per_million","case_fatality_rate_pct"):
            if col in g and g[col].notna().any(): row[col]=g.loc[g[col].notna()].iloc[-1][col]
        rows.append(row)
    return pd.DataFrame(rows)

def generate_insights(df):
    insights=[]
    if df.empty:return ["No rows match the current filters; adjust filters or load another dataset."]
    if "new_cases" in df:
        peak=df.loc[df.new_cases.idxmax()] if df.new_cases.notna().any() else None
        if peak is not None: insights.append(f"Highest single-day reported cases in the filtered records: {peak.location} ({peak.new_cases:,.0f}) on {peak.date:%Y-%m-%d}.")
    if "new_deaths" in df:
        peak=df.loc[df.new_deaths.idxmax()] if df.new_deaths.notna().any() else None
        if peak is not None: insights.append(f"Highest single-day reported deaths in the filtered records: {peak.location} ({peak.new_deaths:,.0f}) on {peak.date:%Y-%m-%d}.")
    s=country_summary(df)
    if "deaths_per_million" in s and s.deaths_per_million.notna().any():
        r=s.loc[s.deaths_per_million.idxmax()]; insights.append(f"Among selected locations, {r.location} has the highest latest available reported deaths per million ({r.deaths_per_million:,.1f}).")
    vacc="people_vaccinated_per_hundred"
    if vacc in df and df[vacc].notna().any():
        g=df[df[vacc].notna()].sort_values("date"); a=g.iloc[0]; b=g.iloc[-1]
        insights.append(f"At-least-one-dose coverage ranges from {a[vacc]:.1f}% ({a.location}, {a.date:%Y-%m-%d}) to {b[vacc]:.1f}% ({b.location}, {b.date:%Y-%m-%d}) in filtered observations.")
    return insights[:5] or ["The selected dataset does not contain enough non-missing supported metrics to generate findings."]
