from datetime import date
import streamlit as st
import pandas as pd
from data_processing import clean_data,fetch_owid,filter_data
from analysis import engineer_metrics,country_summary,generate_insights
from visualizations import time_chart,compare_chart,map_chart,relationship_chart
from report_generator import create_pdf
from pathlib import Path

st.set_page_config(page_title="COVID-19 Global Impact Dashboard",page_icon="📊",layout="wide")
st.markdown("""<style>.block-container{padding-top:1.6rem;max-width:1500px}.hero{padding:1.25rem 1.5rem;border-radius:16px;background:linear-gradient(120deg,#123b48,#176b68);color:white;margin-bottom:1rem}.hero p{color:#dcebea;margin-bottom:0}.kpi{padding:1rem 1.1rem;border:1px solid #e4ebed;border-radius:14px;background:#fff;box-shadow:0 2px 10px #102b3a0b}.kpi small{color:#667985}.kpi strong{font-size:1.45rem;color:#153d4b}</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>COVID-19 Global Impact Dashboard</h1><p>Explore reported cases, deaths and vaccination rollout across countries and time.</p></div>',unsafe_allow_html=True)
with st.sidebar:
 st.header("Data & filters")
 upload=st.file_uploader("Upload compatible CSV",type=["csv"])
 if st.button("Refresh official OWID dataset",use_container_width=True):
  try: st.session_state["raw_data"]=fetch_owid(); st.session_state["data_source"]="Our World in Data"
  except Exception as e: st.error(f"Could not load OWID data: {e}. Upload a local CSV instead.")
if upload:
 try: raw=pd.read_csv(upload); st.session_state["raw_data"]=raw; st.session_state["data_source"]=f"Uploaded file: {upload.name}"
 except Exception as e: st.error(f"Could not read CSV: {e}"); st.stop()
if "raw_data" not in st.session_state and Path(__file__).parent.joinpath("data/covid_synthetic_clean.csv").exists():
 try:
  st.session_state["raw_data"]=pd.read_csv(Path(__file__).parent/"data/covid_synthetic_clean.csv"); st.session_state["data_source"]="User-provided synthetic demonstration dataset"
 except Exception as e: st.warning(f"Could not load bundled demo: {e}")
if "raw_data" not in st.session_state:
 with st.spinner("Attempting to load the official OWID dataset…"):
  try: st.session_state["raw_data"]=fetch_owid(); st.session_state["data_source"]="Our World in Data"
  except Exception as e:
   st.warning(f"Official dataset unavailable: {e}. Upload a CSV with at least location and date columns to begin.")
   st.caption("Source: Our World in Data · https://covid.ourworldindata.org/data/owid-covid-data.csv")
   st.stop()
try: cleaned=clean_data(st.session_state["raw_data"]); df=engineer_metrics(cleaned)
except Exception as e: st.error(f"Dataset validation failed: {e}"); st.stop()
if "synthetic" in st.session_state.get("data_source", "").lower():
 st.warning("Synthetic demonstration data supplied by the user — fictional country names and values. Do not interpret as actual COVID-19 statistics.")
st.caption(f"Source: {st.session_state.get('data_source','Dataset')} · Available dates: {cleaned.date.min():%Y-%m-%d} – {cleaned.date.max():%Y-%m-%d} · {cleaned.location.nunique():,} locations")
with st.sidebar:
 countries=sorted(cleaned.location.dropna().unique().tolist()); selected=st.multiselect("Countries / locations",countries,default=countries[:3])
 start0=cleaned.date.min().date(); end0=cleaned.date.max().date()
 dates=st.date_input("Date range",value=(start0,end0),min_value=start0,max_value=end0)
 continents=sorted(cleaned.continent.dropna().unique()) if "continent" in cleaned else []
 selected_cont=st.multiselect("Continent",continents,default=continents) if continents else None
 metric=st.selectbox("Comparison metric",[x for x in ["cases_per_million","deaths_per_million","total_cases","total_deaths"] if x in df],index=0 if "cases_per_million" in df else 0)
 if st.button("Clear country / continent filters"): selected=countries; selected_cont=continents or None
 if len(dates)==2: start,end=dates
 else: start=end=dates[0]
filtered=filter_data(df,selected,start,end,selected_cont)
if filtered.empty: st.info("No rows match the current filters.")
latest=filtered.sort_values("date").groupby("location").tail(1) if not filtered.empty else filtered
summary=country_summary(filtered)
def total_latest(col): return latest[col].sum(min_count=1) if col in latest else None
def rate_latest(col):
 if col not in latest:return None
 valid=latest.dropna(subset=[col,"population"] if "population" in latest else [col])
 return (valid[col].sum()/valid.population.sum()*1e6) if "population" in valid and valid.population.sum()>0 and col in ["total_cases","total_deaths"] else valid[col].mean() if len(valid) else None
cols=st.columns(5)
vals=[("Reported cases",total_latest("total_cases"),"latest cumulative · selected locations"),("Reported deaths",total_latest("total_deaths"),"latest cumulative · selected locations"),("Cases / million",rate_latest("total_cases"),"population-weighted · latest available"),("Deaths / million",rate_latest("total_deaths"),"population-weighted · latest available"),("At least one dose",latest.people_vaccinated_per_hundred.mean() if "people_vaccinated_per_hundred" in latest else None,"mean latest available · % population")]
for c,(label,value,desc) in zip(cols,vals):
 v="—" if value is None or pd.isna(value) else (f"{value:,.1f}" if "million" in label or "dose" in label else f"{value:,.0f}")
 c.markdown(f'<div class="kpi"><small>{label}</small><br><strong>{v}</strong><br><small>{desc}</small></div>',unsafe_allow_html=True)
st.subheader("Trends over time")
a,b=st.columns(2)
with a: st.plotly_chart(time_chart(filtered,"new_cases","Daily new cases and 7-day average","new_cases_7d_avg"),use_container_width=True)
with b: st.plotly_chart(time_chart(filtered,"new_deaths","Daily new deaths and 7-day average","new_deaths_7d_avg"),use_container_width=True)
a,b=st.columns(2)
with a: st.plotly_chart(time_chart(filtered,"total_cases","Cumulative reported cases"),use_container_width=True)
with b: st.plotly_chart(time_chart(filtered,"total_deaths","Cumulative reported deaths"),use_container_width=True)
st.subheader("Country comparison")
a,b=st.columns(2)
with a: st.plotly_chart(compare_chart(summary,"cases_per_million","Latest cases per million"),use_container_width=True)
with b: st.plotly_chart(compare_chart(summary,"deaths_per_million","Latest deaths per million"),use_container_width=True)
if "people_vaccinated_per_hundred" in filtered:
 st.plotly_chart(time_chart(filtered,"people_vaccinated_per_hundred","At least one dose · % of population"),use_container_width=True)
elif "people_vaccinated" in filtered:
 st.plotly_chart(time_chart(filtered,"people_vaccinated","People vaccinated (count; no denominator available)"),use_container_width=True)
st.caption("‘People vaccinated’ means received at least one dose; it is distinct from fully vaccinated coverage.")
st.subheader("Vaccination coverage and reported deaths")
st.plotly_chart(relationship_chart(filtered),use_container_width=True)
st.caption("Descriptive association only. Time lags, reporting, age structure, testing, variants and prior immunity confound comparisons; this chart does not imply causality.")
if "iso_code" in summary: st.plotly_chart(map_chart(summary,"deaths_per_million"),use_container_width=True)
st.subheader("Selected-country comparison")
st.dataframe(summary,use_container_width=True,hide_index=True)
st.subheader("Data-driven insights")
for insight in generate_insights(filtered): st.markdown(f"- {insight}")
st.caption("Interpret comparisons cautiously: differences in reporting, age distributions, testing rates, variants, prior immunity and time lags affect results.")
if "people_vaccinated_per_hundred" not in latest and "people_vaccinated" in latest:
 st.info("Vaccination counts are present, but population denominators are not; coverage percentages are therefore not calculated.")
st.subheader("Download outputs")
st.download_button("Cleaned dataset · CSV",cleaned.to_csv(index=False).encode(),"covid_cleaned.csv","text/csv")
st.download_button("Comparison summary · CSV",summary.to_csv(index=False).encode(),"country_comparison.csv","text/csv")
st.download_button("Filtered analysis · CSV",filtered.to_csv(index=False).encode(),"filtered_analysis.csv","text/csv")
st.download_button("Executive summary · PDF",create_pdf(filtered,st.session_state.get("data_source","Dataset")),"covid_executive_summary.pdf","application/pdf")
