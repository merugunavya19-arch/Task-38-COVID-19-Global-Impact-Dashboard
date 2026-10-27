"""One-page executive summary PDF generation."""
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from analysis import country_summary,generate_insights

def create_pdf(df=None, source="User-provided dataset"):
    buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=letter,rightMargin=0.55*inch,leftMargin=0.55*inch,topMargin=0.48*inch,bottomMargin=0.45*inch)
    styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name="Sub",parent=styles["Normal"],textColor=colors.HexColor("#536477"),fontSize=8.5,leading=11)); styles.add(ParagraphStyle(name="Body2",parent=styles["BodyText"],fontSize=8.4,leading=11,spaceAfter=4))
    story=[Paragraph("COVID-19 Global Impact Dashboard",styles["Title"]),Paragraph("EXECUTIVE SUMMARY · DATA-DRIVEN REPORT",styles["Sub"]),Spacer(1,8),Paragraph("<b>Objective.</b> Compare reported cases, deaths and vaccination coverage across locations and dates using the Our World in Data schema or a compatible uploaded dataset.",styles["Body2"])]
    if df is not None and not df.empty:
        ss=country_summary(df); dates=f"{df.date.min():%Y-%m-%d} to {df.date.max():%Y-%m-%d}"; findings=generate_insights(df)
        story.append(Paragraph(f"<b>Source / coverage.</b> {source}; {dates}. {len(df):,} cleaned observations across {df.location.nunique():,} locations.",styles["Body2"]))
        kpis=[]
        for col,label in [("total_cases","Latest reported cases"),("total_deaths","Latest reported deaths"),("deaths_per_million","Latest deaths / million"),("people_vaccinated_per_hundred","At least one dose (%)")]:
            if col in ss and ss[col].notna().any(): kpis.append([label,f"{ss[col].sum():,.0f}" if col.startswith("total_") else f"{ss[col].mean():,.1f}"])
        if kpis:
            t=Table(kpis,colWidths=[2.4*inch,2.2*inch]); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#eef5f4")),("GRID",(0,0),(-1,-1),.3,colors.HexColor("#d5e1df")),("FONTSIZE",(0,0),(-1,-1),8),("PADDING",(0,0),(-1,-1),5)])); story += [Paragraph("<b>Key indicators</b> (latest observation per location; rates averaged across locations)",styles["Body2"]),t,Spacer(1,6)]
    else:
        findings=["No dataset was available when this PDF was generated. Load the official OWID CSV or upload a compatible dataset to produce factual KPIs and findings."]
        story.append(Paragraph("<b>Source / coverage.</b> OWID CSV is configured as the live source. Network access was unavailable during project packaging; no substitute statistics are presented.",styles["Body2"]))
    story.append(Paragraph("<b>Findings</b>",styles["Body2"]))
    for item in findings: story.append(Paragraph("• "+item,styles["Body2"]))
    story += [Spacer(1,5),Paragraph("<b>Cleaning and assumptions.</b> Invalid dates and blank locations are excluded; duplicate location-date rows keep the last record. Negative reported counts and non-positive populations are treated as missing, not zero. Missing values are not imputed. Rates use valid population denominators. Vaccination fields distinguish at-least-one-dose from fully vaccinated coverage.",styles["Body2"]),Paragraph("<b>Limitations / conclusion.</b> Reported outcomes depend on testing, reporting practices, age structure, variants, prior immunity and time lags. Coverage and deaths may be associated without establishing causation; cross-country comparisons are descriptive. Interpret results with these caveats.",styles["Body2"])]
    doc.build(story); return buf.getvalue()
