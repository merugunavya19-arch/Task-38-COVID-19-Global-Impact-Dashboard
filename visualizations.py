"""Interactive Plotly chart factories."""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
COLORS=px.colors.qualitative.Safe

def time_chart(df, metric, title, rolling=None):
    if metric not in df:return go.Figure().update_layout(title=title,annotations=[dict(text=f"'{metric}' is not present in this dataset.",showarrow=False)])
    fig=px.line(df.sort_values("date"),x="date",y=metric,color="location",title=title,color_discrete_sequence=COLORS,labels={"date":"Date","location":"Country / location"})
    if rolling and rolling in df:
        for country,g in df.groupby("location"):
            if g[rolling].notna().any(): fig.add_scatter(x=g.date,y=g[rolling],mode="lines",name=f"{country} · 7-day average",line=dict(dash="dot",width=2))
    fig.update_layout(legend_title_text="Location / series",hovermode="x unified",margin=dict(l=10,r=10,t=55,b=10))
    return fig

def compare_chart(summary, metric, title):
    if metric not in summary or summary.empty:return go.Figure().update_layout(title=title)
    d=summary.dropna(subset=[metric]).sort_values(metric,ascending=False)
    return px.bar(d,x="location",y=metric,color=metric,color_continuous_scale="Tealgrn",title=title,labels={"location":"Country / location"}).update_layout(margin=dict(l=10,r=10,t=55,b=10))

def map_chart(summary,metric):
    if metric not in summary or summary.empty:return go.Figure()
    d=summary.dropna(subset=[metric])
    return px.choropleth(d,locations="iso_code",color=metric,hover_name="location",color_continuous_scale="Reds",title="Latest reported deaths per million by country") if "iso_code" in d else go.Figure().update_layout(title="Map unavailable: iso_code is not present in uploaded data.")

def relationship_chart(df):
    x="people_vaccinated_per_hundred"; y="new_deaths_7d_avg"
    if not {x,y}.issubset(df):return go.Figure().update_layout(title="Vaccination / deaths relationship unavailable in this dataset")
    d=df.dropna(subset=[x,y])
    if d.empty:return go.Figure().update_layout(title="No overlapping non-missing vaccination and death observations")
    return px.scatter(d,x=x,y=y,color="location",hover_data=["date"],title="At-least-one-dose coverage vs 7-day average reported deaths",labels={x:"People with ≥1 dose (% population)",y:"Daily deaths · 7-day average"})
