import os, yaml
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from influxdb_client import InfluxDBClient
from sklearn.ensemble import IsolationForest
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=10000, key="datarefresh")

st.set_page_config(page_title="Air Quality Monitor", layout="wide")
st.title("Air Quality Monitoring Dashboard")

config_path = os.path.join(os.path.dirname(__file__), "../config/settings.yaml")
with open(config_path) as f:
    cfg = yaml.safe_load(f)["influxdb"]

BUCKET = cfg["bucket"]

@st.cache_resource
def get_client():
    return InfluxDBClient(url=cfg["url"], token=cfg["token"], org=cfg["org"])

def run_query(flux):
    try:
        tables = get_client().query_api().query_data_frame(flux)
        if isinstance(tables, list):
            return pd.concat(tables) if tables else pd.DataFrame()
        return tables
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

with st.sidebar:
    st.subheader("Live readings")
    try:
        live_df = run_query(f"""
            from(bucket: "{BUCKET}")
              |> range(start: -5m)
              |> filter(fn: (r) => r._field == "temperature" 
                  or r._field == "humidity" 
                  or r._field == "air_quality"
                  or r._field == "gas")
              |> last()
              |> pivot(rowKey:["_time"], 
                  columnKey:["_field"], valueColumn:"_value")
        """)
        if not live_df.empty:
            row = live_df.iloc[-1]
            st.metric("Temperature", 
                f"{float(row.get('temperature',0)):.1f} C")
            st.metric("Humidity",    
                f"{float(row.get('humidity',0)):.1f} %")
            st.metric("Air Quality", 
                f"{int(row.get('air_quality',0))}")
            st.metric("Gas",         
                f"{int(row.get('gas',0))}")
        else:
            st.info("Waiting for data...")
    except Exception as e:
        st.error(f"Error: {e}")
    time_range = st.selectbox(
        "Time range", ["1h","6h","24h"], index=2)

st.subheader("Visualization 1 — Sensor trends over time")
df1 = run_query(f"""
    from(bucket: "{BUCKET}")
      |> range(start: -{time_range})
      |> filter(fn: (r) => r._field == "temperature" or r._field == "humidity" or r._field == "air_quality")
      |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
""")
if not df1.empty:
    fig1 = go.Figure()
    if "temperature" in df1.columns:
        fig1.add_trace(go.Scatter(x=df1["_time"], y=df1["temperature"], name="Temp (C)", line=dict(color="#e05c5c")))
    if "humidity" in df1.columns:
        fig1.add_trace(go.Scatter(x=df1["_time"], y=df1["humidity"], name="Humidity (%)", line=dict(color="#5c8fe0")))
    if "air_quality" in df1.columns:
        fig1.add_trace(go.Scatter(x=df1["_time"], y=df1["air_quality"], name="Air Quality", line=dict(color="#5cb85c"), yaxis="y2"))
    fig1.update_layout(height=340, yaxis2=dict(overlaying="y", side="right"), legend=dict(orientation="h", y=1.08), margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("No trend data yet — run the simulator!")

st.subheader("Visualization 2 — Air quality vs gas scatter")
df2 = run_query(f"""
    from(bucket: "{BUCKET}")
      |> range(start: -{time_range})
      |> filter(fn: (r) => r._field == "air_quality" or r._field == "gas")
      |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
""")
if not df2.empty and "air_quality" in df2.columns and "gas" in df2.columns:
    fig2 = px.scatter(df2, x="air_quality", y="gas", opacity=0.5, color_discrete_sequence=["#5c8fe0"], labels={"air_quality":"Air Quality (MQ-135)","gas":"Gas (MQ-2)"})
    fig2.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Not enough data yet")

st.subheader("ML — IsolationForest anomaly detection")
df3 = run_query(f"""
    from(bucket: "{BUCKET}")
      |> range(start: -{time_range})
      |> filter(fn: (r) => r._field == "temperature" or r._field == "humidity" or r._field == "air_quality" or r._field == "gas")
      |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
""")
feats = ["temperature","humidity","air_quality","gas"]
if not df3.empty and all(c in df3.columns for c in feats):
    df3 = df3.dropna(subset=feats).copy()
    model = IsolationForest(contamination=0.05, random_state=42)
    df3["pred"] = model.fit_predict(df3[feats].values)
    df3["label"] = df3["pred"].map({1:"normal",-1:"anomaly"})
    fig3 = px.scatter(df3, x="_time", y="air_quality", color="label", color_discrete_map={"normal":"#5c8fe0","anomaly":"#e05c5c"}, labels={"air_quality":"Air Quality","_time":"Time"})
    fig3.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig3, use_container_width=True)
    n = (df3["pred"]==-1).sum()
    col1,col2,col3 = st.columns(3)
    col1.metric("Total readings", len(df3))
    col2.metric("Normal", len(df3)-n)
    col3.metric("Anomalies", n)
    st.info(f"Model: IsolationForest | Features: temp, humidity, aq, gas | Output: -1=anomaly, 1=normal | Anomalies flagged for alert or human review.")
else:
    st.info("Need more data for ML — let simulator run for 5+ minutes first")
