# COVID-19 Global Impact Dashboard

A portfolio-ready Streamlit app for exploring confirmed COVID-19 cases, deaths and vaccination coverage using the Our World in Data (OWID) schema. It includes cleaning, metric engineering, interactive visualizations, data-derived findings, exports, tests, an EDA notebook and PDF executive-summary generation.

> **Data integrity:** The bundled `data/covid_synthetic_clean.csv` was supplied by the user and is explicitly synthetic (fictional locations and generated values). It is used as a demonstration dataset only and must not be cited as actual COVID-19 statistics. The dashboard labels it prominently. The app also supports uploaded CSVs and an explicit live OWID refresh; if no data is available it does not invent findings. The included PDF is generated from this synthetic demonstration input and carries the same caveat.

## Data source

OWID COVID-19 dataset: <https://covid.ourworldindata.org/data/owid-covid-data.csv>. The data source is maintained by Our World in Data; access and availability may change. A compatible upload must have `location` and `date`, or `country` and `date` (the latter is normalized). Metrics are shown only when their source fields exist. The user-provided synthetic file lacks population denominators and vaccination percentage fields, so per-million rates and vaccination coverage percentages are correctly unavailable.

## Features

- Conservative data validation, date coercion, duplicate removal and invalid-value handling; no blanket zero imputation.
- Per-million metrics, case-fatality rate, country-specific seven-day averages, and guarded doubling-time estimates.
- Country/date/continent filters; KPIs based on latest selected observations rather than summed cumulative values.
- Plotly daily and cumulative trends, rate comparisons, vaccination trends, an exploratory vaccination/death scatterplot, and a world map when `iso_code` is present.
- Computed insights with explicit limitations; CSV exports and one-page ReportLab PDF.
- Notebook workflow and automated pytest coverage.

## Architecture

- `app.py` — Streamlit UI, filters, KPIs, visualizations, insights and downloads.
- `data_processing.py` — source loading, input validation, cleaning and filters.
- `analysis.py` — derived metrics, country summary and result-based insights.
- `visualizations.py` — Plotly chart factories.
- `report_generator.py` — PDF executive summary.
- `notebooks/eda_workflow.ipynb` — reproducible EDA walkthrough.
- `tests/` — unit tests for cleaning, metrics and filtering.

## Install and run

Python 3.10+ recommended.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows Command Prompt
.venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run app.py
```

The bundled synthetic demonstration CSV loads automatically for an immediate offline demo. To use real data, click **Refresh official OWID dataset** when online, or upload a trusted real-data CSV using **Upload compatible CSV**. Required fields are `location` and `date`; common optional fields include `population`, `new_cases`, `total_cases`, `new_deaths`, `total_deaths`, `people_vaccinated`, `people_vaccinated_per_hundred`, `people_fully_vaccinated` and `people_fully_vaccinated_per_hundred`.

## Using the dashboard

Use the sidebar to choose multiple locations, date range, continent and comparison metric. Charts and outputs respond to the selected rows. A single date value is accepted where Streamlit's date range picker returns one endpoint. Population-normalized rates use population-weighted aggregation for KPI cards; comparison tables display each selected location's last non-missing value in the filtered interval.

Download cleaned rows, country summaries and filtered analysis as CSV, or generate a one-page PDF for the current view. Plotly charts are interactive in the app; static chart PNG export is not provided because it requires the optional Kaleido backend. Use Plotly's image controls after installing `kaleido` if needed.

## Cleaning and metric notes

Rows without a parseable date or non-empty location are removed. Duplicate `(location,date)` records keep the last input row (source row order is retained). Invalid numeric strings become missing. Negative reported counts and non-positive populations are set missing; percentages outside 0–100 are set missing. Other missing cells remain missing. Seven-day rolling averages require seven valid records; missing days are not implicitly treated as zero. Doubling time uses `7 × ln(2) / ln(current / value 7 calendar days earlier)` and is reported only for positive observations with growth. This is descriptive and sensitive to revisions and reporting noise.

Vaccinated (`people_vaccinated`) refers to at least one dose; fully vaccinated columns refer to a separate status. Comparisons are descriptive; correlation is not causal evidence. Reporting differences, testing, age, variants, prior immunity and time delays limit interpretation.

## Tests and notebook

```bash
pytest -q
jupyter notebook notebooks/eda_workflow.ipynb
```

Tests use small purpose-built fixtures solely to validate software behavior; they are not epidemiological estimates. They are **not** epidemiological estimates and are not shipped as an example COVID dataset.
