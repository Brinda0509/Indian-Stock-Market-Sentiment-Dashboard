"""
Indian Stock Market Sentiment Dashboard
Run: python -m streamlit run final.py
# v2-aligned
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import os, glob

st.set_page_config(page_title="Indian Stock Sentiment",
                   layout="wide", initial_sidebar_state="collapsed")

# ── Card helper ───────────────────────────────────────────────────────────────
CARD_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;}
body{background:transparent;font-family:'Inter',sans-serif;}
.card{background:linear-gradient(180deg,#0D1520 0%,#0B111A 100%);
      border:1px solid rgba(28,46,68,.95);border-radius:14px;
      padding:14px 16px 12px;box-shadow:0 10px 38px rgba(0,0,0,.65);
      height:100%;position:relative;overflow:hidden;
      transition:border-color .18s ease, box-shadow .18s ease, transform .18s ease;}
.card:hover{border-color:#2B4A6A;box-shadow:0 14px 46px rgba(0,0,0,.72);transform:translateY(-1px);}
.card:before{content:"";position:absolute;left:0;right:0;top:0;height:1px;
      background:linear-gradient(90deg,rgba(59,130,246,0),rgba(59,130,246,.55),rgba(59,130,246,0));}
.ch{display:flex;align-items:center;gap:8px;margin-bottom:10px;}
.cd{width:3px;height:18px;border-radius:2px;
    background:linear-gradient(180deg,#3B82F6,#1D4ED8);flex-shrink:0;}
.ct{font-size:12.5px;font-weight:600;color:#90B4D4;}
.ctag{margin-left:auto;font-size:10px;color:#2E4A66;background:#060C14;
      border:1px solid #1C2E44;border-radius:4px;padding:1px 6px;
      transition:border-color .18s ease, background .18s ease, color .18s ease;}
.card:hover .ctag{border-color:#2B4A6A;background:#081220;color:#3A5A7A;}
.cs{font-size:9.5px;color:#4B6B8B;line-height:1.65;
    border-top:1px solid #0A1218;padding-top:7px;margin-top:5px;}
.leg{font-size:9px;line-height:1.9;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
</style>"""

def card_html(title, fig, summary, height=215, tag="", legend_html=""):
    fh = pio.to_html(fig, full_html=False, include_plotlyjs="cdn",
                     config={"displayModeBar": False, "responsive": True})
    th = f'<span class="ctag">{tag}</span>' if tag else ""
    lh = f'<div class="leg">{legend_html}</div>' if legend_html else ""
    return f"""{CARD_CSS}<div class="card">
  <div class="ch"><div class="cd"></div><span class="ct">{title}</span>{th}</div>
  <div style="width:100%;height:{height}px;">{fh}</div>{lh}
  <div class="cs">{summary}</div></div>"""

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body{margin:0;padding:0;}
.stApp{
  background:
    radial-gradient(1100px 520px at 12% -8%, rgba(59,130,246,.14), rgba(0,0,0,0) 55%),
    radial-gradient(900px 520px at 92% -12%, rgba(99,102,241,.10), rgba(0,0,0,0) 52%),
    radial-gradient(1000px 600px at 55% 105%, rgba(16,185,129,.07), rgba(0,0,0,0) 55%),
    #000 !important;
}
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
[data-testid="stHeader"],[data-testid="stDecoration"],
[data-testid="stToolbar"],[data-testid="collapsedControl"],
[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none !important;}
.stDeployButton{display:none;}
[data-testid="stAppViewBlockContainer"],[data-testid="stMainBlockContainer"]{padding-top:0 !important;}
.main .block-container{padding:0 1rem .5rem 1rem !important;max-width:100% !important;}
.block-container{padding-top:0 !important;} section.main > div{padding-top:0 !important;}
div[data-testid="stVerticalBlock"] > div{gap:0 !important;}
div[data-testid="stHorizontalBlock"]{gap:8px !important;align-items:flex-start !important;}
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]){margin-bottom:-12px !important;}
div[data-testid="stPlotlyChart"]{margin:0 !important;padding:0 !important;}
.stTabs [data-baseweb="tab-list"]{gap:3px !important;background:#0A1628 !important;
  border-radius:8px !important;padding:3px !important;margin-bottom:10px !important;
  border:1px solid #1C2E44 !important;box-shadow:0 10px 26px rgba(0,0,0,.35) !important;}
.stTabs [data-baseweb="tab"]{height:26px !important;padding:0 16px !important;
  font-size:.7rem !important;font-weight:500 !important;border-radius:6px !important;
  color:#3D5A78 !important;background:transparent !important;
  transition:background .15s ease, color .15s ease, box-shadow .15s ease !important;}
.stTabs [data-baseweb="tab"]:hover{background:#0D1520 !important;color:#90B4D4 !important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#1A3560,#1E4080) !important;
  color:#60A5FA !important;font-weight:600 !important;}
.stTabs [data-baseweb="tab-panel"]{padding:8px 0 0 0 !important;}
.stSelectbox > div > div{background:#0D1520 !important;border-color:#1C2E44 !important;
  font-size:.75rem !important;min-height:30px !important;border-radius:6px !important;color:#90B4D4 !important;
  transition:border-color .15s ease, box-shadow .15s ease !important;}
.stSelectbox > div > div:hover{border-color:#2B4A6A !important;}
.stSelectbox > div > div:focus-within{border-color:#3B82F6 !important;box-shadow:0 0 0 2px rgba(59,130,246,.22) !important;}
.stDateInput > div > div > input{background:#0D1520 !important;border-color:#1C2E44 !important;
  font-size:.72rem !important;color:#90B4D4 !important;
  transition:border-color .15s ease, box-shadow .15s ease !important;}
.stDateInput > div > div > input:focus{border-color:#3B82F6 !important;box-shadow:0 0 0 2px rgba(59,130,246,.22) !important;}
div[data-testid="stDateInput"],div[data-testid="stSelectbox"]{margin-top:0 !important;}
::-webkit-scrollbar{width:10px;height:10px;}
::-webkit-scrollbar-track{background:#04070B;}
::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#0D1520,#081220);border:1px solid #1C2E44;border-radius:10px;}
::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#102033,#0B1730);}
</style>""", unsafe_allow_html=True)

components.html("<script>(function(){document.body.style.zoom='0.85';})();</script>", height=0)

# ── Paths & defaults ──────────────────────────────────────────────────────────
BASE = r"output"
PATHS = {
    "merged": os.path.join(BASE, "merged"),
    "signals": os.path.join(BASE, "signals"),
    "summary": os.path.join(BASE, "summary"),
    "scored": os.path.join(BASE, "scored")
}
AXIS = dict(gridcolor='#0D1520', linecolor='#0D1520',
            tickfont=dict(size=7, color='#4B6B8B'), showgrid=True)
PLOT = dict(paper_bgcolor='#0D1520', plot_bgcolor='#0D1520',
            font=dict(family='Inter', color='#4B6B8B', size=8),
            hoverlabel=dict(bgcolor="#0B111A", bordercolor="#1C2E44",
                            font=dict(color="#E2E8F0", size=10)),
            margin=dict(l=36, r=8, t=8, b=20))

@st.cache_data
def load_data():
    md, sd = {}, {}
    for f in glob.glob(os.path.join(PATHS["merged"], "*_merged.csv")):
        t = os.path.basename(f).replace("_merged.csv","")
        df = pd.read_csv(f); df["Date"] = pd.to_datetime(df["Date"], errors="coerce"); md[t] = df
    for f in glob.glob(os.path.join(PATHS["signals"], "*_signals.csv")):
        t = os.path.basename(f).replace("_signals.csv","")
        df = pd.read_csv(f); df["Date"] = pd.to_datetime(df["Date"], errors="coerce"); sd[t] = df
    cp = os.path.join(PATHS["summary"], "CORRELATION_SUMMARY.csv")
    cd = pd.read_csv(cp) if os.path.exists(cp) else pd.DataFrame()
    sp = os.path.join(PATHS["scored"], "ALL_SCORED.csv")
    sc = pd.read_csv(sp) if os.path.exists(sp) else None
    return md, sd, cd, sc

merged_dfs, signal_dfs, corr_df, scored_df = load_data()
tickers = sorted(merged_dfs.keys())

def disp_ticker(t):
    return "ADANINET" if t == "ADANI" else t

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""<div style="text-align:center;padding:8px 0 5px;
  border-bottom:1px solid #0F1E2E;margin-bottom:6px;box-shadow:0 1px 0 rgba(59,130,246,.18);">
  <div style="font-size:.95rem;font-weight:700;color:#D6E9FF;letter-spacing:2px;
              text-transform:uppercase;">Indian Stock Market Sentiment Dashboard</div>
  <div style="font-size:.5rem;color:#2E4A66;letter-spacing:.12em;
              text-transform:uppercase;margin-top:2px;">
    Sentiment Intelligence · Nifty 50 · 2023–2025</div>
</div>""", unsafe_allow_html=True)

# ── Controls row ──────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1.2, 2.2, 0.8])
with c1:
    selected = st.selectbox("Company", tickers, index=0, label_visibility="collapsed",
                            format_func=disp_ticker)

selected_disp = disp_ticker(selected)

df_m = merged_dfs.get(selected, pd.DataFrame()).copy()
df_s = signal_dfs.get(selected, pd.DataFrame()).copy()

with c2:
    dr = None
    if len(df_m) > 0:
        mn, mx = df_m["Date"].min().date(), df_m["Date"].max().date()
        dr = st.date_input("Date", value=(mn, mx), min_value=mn, max_value=mx,
                           label_visibility="collapsed")

with c3:
    hc = 0
    if scored_df is not None and "Is_Hindi" in scored_df.columns and "Ticker" in scored_df.columns:
        hc = int(scored_df[scored_df["Ticker"] == selected]["Is_Hindi"].sum())
    hbg = "linear-gradient(135deg,#2E1065,#3B1B8A);color:#C4B5FD;border:1px solid #4C1D95;box-shadow:0 10px 22px rgba(0,0,0,.35)" if hc > 0 else "linear-gradient(180deg,#0D1520,#0B111A);color:#3A5A7A;border:1px solid #1C2E44;box-shadow:0 10px 22px rgba(0,0,0,.32)"
    st.markdown(f'<div style="padding:4px 10px;font-size:.68rem;font-weight:600;'
                f'border-radius:6px;display:inline-block;background:{hbg};">'
                f'{"Hindi: "+str(hc) if hc>0 else "Hindi: pending"}</div>',
                unsafe_allow_html=True)

if dr and len(dr) == 2 and len(df_m) > 0:
    s, e = pd.Timestamp(dr[0]), pd.Timestamp(dr[1])
    df_m = df_m[(df_m["Date"] >= s) & (df_m["Date"] <= e)]
    if len(df_s) > 0:
        df_s = df_s[(df_s["Date"] >= s) & (df_s["Date"] <= e)]

# ── KPI computation ───────────────────────────────────────────────────────────
avg_s = avg_r = n_news = out_d = lead_r = 0.0
best = "N/A"; sc_cl = rc_cl = ic_cl = "neu"; sl = "Neutral"; nwks = 0

if len(df_m) > 0 and "Avg_VADER_Score" in df_m.columns:
    avg_s  = df_m["Avg_VADER_Score"].mean()
    avg_r  = df_m["Daily_Return_%"].mean() if "Daily_Return_%" in df_m.columns else 0
    n_news = int(df_m["News_Count"].sum()) if "News_Count" in df_m.columns else 0
    out_d  = int((df_s["Broker_Panic_Score"] > 0).sum()) if "Broker_Panic_Score" in df_s.columns else 0
    nwks   = len(df_m)
    t_row  = corr_df[corr_df["Ticker"] == selected] if len(corr_df) > 0 else pd.DataFrame()
    best   = t_row["Best_Indicator"].values[0] if len(t_row) > 0 else "N/A"
    lead_r = t_row["Corr_Lead_1Day"].values[0] if len(t_row) > 0 else 0
    sc_cl  = "pos" if avg_s > 0.05 else ("neg" if avg_s < -0.05 else "neu")
    rc_cl  = "pos" if avg_r > 0 else "neg"
    ic_cl  = "pos" if "Lead" in str(best) else ("neg" if "Lag" in str(best) else "amber")
    sl     = "Positive" if avg_s > 0.05 else ("Negative" if avg_s < -0.05 else "Neutral")

_C = {"pos":"#34D399","neg":"#F87171","neu":"#94A3B8","amber":"#FBBF24"}
sc_color = _C[sc_cl]; rc_color = _C[rc_cl]; ic_color = _C[ic_cl]

# ── KPI card style (inline — works everywhere) ────────────────────────────────
_kc = ("background:linear-gradient(180deg,#0E1A2B 0%,#0B111A 100%);"
       "border:1px solid rgba(28,46,68,.95);border-radius:10px;"
       "padding:9px 11px;margin-bottom:6px;box-shadow:0 12px 30px rgba(0,0,0,.58);")
_kl = "font-size:8.5px;color:#486781;text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-bottom:3px;"
_ks = "font-size:8px;color:#2E4A66;margin-top:2px;"

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT  — left col: KPI cards  |  right col: tabs + charts
# ═══════════════════════════════════════════════════════════════════════════════
left_col, right_col = st.columns([0.22, 0.78], gap="small")

# ── LEFT COLUMN — KPI cards stacked vertically ────────────────────────────────
with left_col:
    # Spacer to align KPI section with tab content (tab bar = ~34px)
    st.markdown('<div style="height:0px;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:9px;color:#1E3048;text-transform:uppercase;'
        'letter-spacing:.1em;font-weight:600;margin-bottom:6px;">'
        'Key Metrics</div>', unsafe_allow_html=True)

    st.markdown(f"""
<div style="{_kc}">
  <div style="{_kl}">Avg Sentiment</div>
  <div style="font-size:1.05rem;font-weight:700;color:{sc_color};line-height:1.2;">{avg_s:+.3f}</div>
  <div style="{_ks}">{sl}</div>
</div>
<div style="{_kc}">
  <div style="{_kl}">Weekly Return</div>
  <div style="font-size:1.05rem;font-weight:700;color:{rc_color};line-height:1.2;">{avg_r:+.2f}%</div>
  <div style="{_ks}">{nwks} weeks</div>
</div>
<div style="{_kc}">
  <div style="{_kl}">Total Headlines</div>
  <div style="font-size:1.05rem;font-weight:700;color:#60A5FA;line-height:1.2;">{n_news:,}</div>
  <div style="{_ks}">2023–2025</div>
</div>
<div style="{_kc}">
  <div style="{_kl}">Signal Type</div>
  <div style="font-size:.82rem;font-weight:700;color:{ic_color};line-height:1.3;">{best}</div>
  <div style="{_ks}">r = {lead_r:+.3f}</div>
</div>
<div style="{_kc}">
  <div style="{_kl}">Outage Periods</div>
  <div style="font-size:1.05rem;font-weight:700;color:#F87171;line-height:1.2;">{int(out_d)}</div>
  <div style="{_ks}">Broker disruptions</div>
</div>
<div style="margin-top:10px;padding-top:8px;border-top:1px solid #1C2E44;">
  <div style="font-size:8.5px;color:#1E3048;">Nifty 50 · 2023–2025</div>
</div>
""", unsafe_allow_html=True)

# ── RIGHT COLUMN — tabs + charts ──────────────────────────────────────────────
with right_col:
    tab1, tab2 = st.tabs(["Market Movement", "Sentiment Insights"])

    # ── TAB 1 ─────────────────────────────────────────────────────────────────
    with tab1:
        col_p, col_b = st.columns([1.6, 1], gap="small")

        with col_p:
            if len(df_m) > 0 and "Close" in df_m.columns:
                df_plot = (df_m.dropna(subset=["Date","Close"])
                               .drop_duplicates(subset=["Date"])
                               .sort_values("Date").reset_index(drop=True))
                df_plot["Close"] = pd.to_numeric(df_plot["Close"], errors="coerce")
                df_plot = df_plot.dropna(subset=["Close"])
                fig_p = go.Figure()
                fig_p.add_trace(go.Scatter(
                    x=df_plot["Date"], y=df_plot["Close"], name="Price", mode="lines",
                    line=dict(color="#3B82F6", width=2),
                    fill="tozeroy", fillcolor="rgba(59,130,246,0.07)"))
                if len(df_s) > 0 and "Broker_Panic_Score" in df_s.columns:
                    op = df_plot[df_plot["Date"].isin(
                        df_s[df_s["Broker_Panic_Score"] >= 0.5]["Date"])][["Date","Close"]]
                    if len(op) > 0:
                        fig_p.add_trace(go.Scatter(
                            x=op["Date"], y=op["Close"], name="Outage", mode="markers",
                            marker=dict(color="#EF4444", size=7, symbol="x", line=dict(width=2))))
                fig_p.update_layout(
                    **PLOT, height=210, showlegend=True,
                    legend=dict(orientation="h", y=1.1, x=0,
                                bgcolor="rgba(0,0,0,0)", font=dict(size=7, color="#3A5A7A")),
                    xaxis=AXIS,
                    yaxis=dict(**AXIS, title=dict(text="Price (INR)",
                               font=dict(size=7, color="#2E4A66"))))
                components.html(
                    card_html("Close Price Analysis", fig_p,
                              "Stock closing price over time with broker outage markers. "
                              "Identify whether price fluctuations coincide with "
                              "panic-triggering disruptions.",
                              height=210, tag=selected_disp),
                    height=355)
            else:
                st.info("No price data available.")

        with col_b:
            if len(df_s) > 0 and "Broker_Panic_Score" in df_s.columns:
                fig_b = go.Figure()
                pv = df_s["Broker_Panic_Score"].fillna(0)
                oe = df_s[df_s["Broker_Panic_Score"] >= 0.5].copy()
                fig_b.add_trace(go.Bar(
                    x=df_s["Date"], y=pv,
                    marker_color=["#EF4444" if v >= 0.8 else "#F97316" if v >= 0.5
                                  else "#FBBF24" if v > 0 else "#0A1520" for v in pv],
                    hovertemplate="%{x|%d %b %Y}<br>Score: %{y:.2f}<extra></extra>"))
                if len(oe) > 0:
                    for subset, name, clr, bclr in [
                        (oe[oe["Broker_Panic_Score"] >= 0.8], "Critical", "#EF4444", "#FF0000"),
                        (oe[(oe["Broker_Panic_Score"] >= 0.5) & (oe["Broker_Panic_Score"] < 0.8)],
                         "High", "#F97316", "#FBBF24")]:
                        if len(subset) > 0:
                            note = "Zerodha outage" if name == "Critical" else "Major Broker Outage Cluster"
                            fig_b.add_trace(go.Scatter(
                                x=subset["Date"], y=subset["Broker_Panic_Score"] + 0.07,
                                mode="markers", name=name,
                                marker=dict(color=clr, size=7, symbol="circle",
                                            line=dict(color=bclr, width=1)),
                                customdata=list(zip([name]*len(subset),
                                                    subset["Date"].dt.strftime("%d %b %Y"),
                                                    subset["Broker_Panic_Score"].round(2),
                                                    [note]*len(subset))),
                                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                                              "%{customdata[3]}<br>Score: %{customdata[2]}<extra></extra>"))
                fig_b.add_hline(y=0.5, line_dash="dash", line_color="#EF4444", line_width=1,
                                annotation_text="threshold", annotation_position="top right",
                                annotation_font=dict(color="#EF4444", size=7))
                fig_b.update_layout(
                    **PLOT, height=210, showlegend=True,
                    legend=dict(orientation="h", y=1.1, x=0,
                                bgcolor="rgba(0,0,0,0)", font=dict(size=7, color="#3A5A7A")),
                    xaxis=AXIS,
                    yaxis=dict(**AXIS, range=[0, 1.2],
                               title=dict(text="Panic Score", font=dict(size=7, color="#2E4A66"))))
                components.html(
                    card_html("Broker Outage Panic", fig_b,
                              "Panic intensity over time. Red = critical, orange = high events "
                              "that may influence retail trading behavior.",
                              height=210),
                    height=355)
            else:
                st.info("No broker signal data.")

    # ── TAB 2 ─────────────────────────────────────────────────────────────────
    with tab2:
        col_h, col_f = st.columns([1.4, 1], gap="small")

        with col_h:
            if len(corr_df) > 0:
                cols_ht = [c for c in ["Corr_Same_Day","Corr_Lead_1Day",
                                        "Corr_Lead_2Day","Corr_Lag_1Day"]
                           if c in corr_df.columns]
                if cols_ht:
                    ht = corr_df.set_index("Ticker")[cols_ht].fillna(0)
                    xlbl = {"Corr_Same_Day":"Same Wk","Corr_Lead_1Day":"Lead +1W",
                            "Corr_Lead_2Day":"Lead +2W","Corr_Lag_1Day":"Lag -1W"}
                    fig_ht = go.Figure(go.Heatmap(
                        z=ht.values, x=[xlbl.get(c, c) for c in cols_ht],
                        y=[disp_ticker(t) for t in ht.index.tolist()],
                        colorscale=[[0,"#3B0A0A"],[0.35,"#7F1D1D"],[0.5,"#0F1E2E"],
                                    [0.65,"#064E3B"],[1,"#022C22"]],
                        zmid=0, zmin=-0.5, zmax=0.5,
                        text=ht.values.round(3), texttemplate="%{text}",
                        textfont=dict(size=8, color="white"), showscale=True,
                        colorbar=dict(tickfont=dict(color="#2E4A66", size=7),
                                      thickness=7, len=0.8)))
                    fig_ht.update_layout(
                        **PLOT, height=228,
                        xaxis=dict(**AXIS, side="bottom"), yaxis=AXIS)
                    components.html(
                        card_html("Sentiment vs Return Correlation", fig_ht,
                                  "Sentiment correlated with future returns across time lags. "
                                  "Green = positive predictive signal, "
                                  "red = inverse or weak relationship.",
                                  height=228),
                        height=378)
            else:
                st.info("Run pipeline.py first.")

        with col_f:
            if len(corr_df) > 0 and "Best_Indicator" in corr_df.columns \
                    and "Corr_Lead_1Day" in corr_df.columns:
                tickers_c_raw = corr_df["Ticker"].tolist()
                tickers_c = [disp_ticker(t) for t in tickers_c_raw]
                lead_vals = corr_df["Corr_Lead_1Day"].fillna(0).tolist()
                best_vals = corr_df["Best_Indicator"].astype(str).tolist()
                bar_colors    = ["#34D399" if "Lead" in b else
                                 "#F87171" if "Lag"  in b else "#FBBF24" for b in best_vals]
                border_colors = ["#FFFFFF" if tk == selected else "rgba(0,0,0,0)"
                                 for tk in tickers_c_raw]
                border_widths = [2 if tk == selected else 0 for tk in tickers_c_raw]
                fig_fc = go.Figure()
                fig_fc.add_trace(go.Bar(
                    x=tickers_c, y=lead_vals,
                    marker=dict(color=bar_colors,
                                line=dict(color=border_colors, width=border_widths)),
                    text=[f"{v:+.3f}" for v in lead_vals],
                    textposition="outside",
                    textfont=dict(size=7, color="#3A5A7A"),
                    cliponaxis=False))
                fig_fc.add_hline(y=0, line_color="#1C2E44", line_width=1)
                fig_fc.update_layout(
                    **PLOT, height=228, showlegend=False,
                    xaxis=dict(**AXIS, tickangle=-40),
                    yaxis=dict(**AXIS, range=[-0.65, 0.75],
                               title=dict(text="Correlation r",
                                          font=dict(size=7, color="#2E4A66"))),
                    bargap=0.25)
                leads = [tk for tk, b in zip(tickers_c, best_vals) if "Lead" in b]
                lags  = [tk for tk, b in zip(tickers_c, best_vals) if "Lag"  in b]
                same  = [tk for tk, b in zip(tickers_c, best_vals)
                         if "Lead" not in b and "Lag" not in b]
                parts = []
                if leads: parts.append(f'<span style="color:#34D399;">Leads:</span> '
                                       f'<span style="color:#3A5A7A;">{", ".join(leads)}</span>')
                if lags:  parts.append(f'<span style="color:#F87171;">Lags:</span> '
                                       f'<span style="color:#3A5A7A;">{", ".join(lags)}</span>')
                if same:  parts.append(f'<span style="color:#FBBF24;">Same-wk:</span> '
                                       f'<span style="color:#3A5A7A;">{", ".join(same)}</span>')
                components.html(
                    card_html("Finding per Stock", fig_fc,
                              "Whether sentiment leads, lags, or moves simultaneously "
                              "with price. White border = selected company.",
                              height=228,
                              legend_html="&nbsp;&nbsp;".join(parts)),
                    height=378)
            else:
                st.info("Run pipeline.py first.")
