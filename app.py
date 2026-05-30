"""
ActuarialFleet v2.0 — Streamlit App
Piattaforma attuariale RCA flotte auto
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
from datetime import datetime, date

from database import (
    get_flotte, add_flotta, delete_flotta, import_flotte,
    get_sinistri, add_sinistro, delete_sinistro, import_sinistri,
)
from actuarial import (
    PROVINCE, CIL_MAP, USO_MAP, BM_MAP,
    calcola_premio, glm_parametrico, credibilita,
    chain_ladder, DEFAULT_TRIANGLE, get_prov,
)
from pdf_report import genera_report

# ── CONFIG PAGINA ──
st.set_page_config(
    page_title="ActuarialFleet",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS CUSTOM ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* HEADER */
.main-header {
    background: linear-gradient(135deg, #0D0F14 0%, #13161D 100%);
    border: 1px solid #2A2E3D;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.main-header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(90deg, #4F8EF7, #7C5CFC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.main-header p { color: #9BA3BC; font-size: 13px; margin: 0; }

/* METRIC CARDS */
.metric-card {
    background: #13161D;
    border: 1px solid #2A2E3D;
    border-radius: 12px;
    padding: 16px 20px;
    border-top: 2px solid var(--accent, #4F8EF7);
}
.metric-card .label {
    font-size: 11px;
    color: #5A6280;
    text-transform: uppercase;
    letter-spacing: .06em;
    font-weight: 500;
    margin-bottom: 4px;
}
.metric-card .value {
    font-family: 'Syne', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: var(--accent, #4F8EF7);
    margin: 0;
}
.metric-card .delta { font-size: 11px; color: #5A6280; margin-top: 3px; }

/* RESULT BOXES */
.result-green { background: rgba(34,197,94,.08); border: 1px solid rgba(34,197,94,.2); border-radius: 10px; padding: 14px 18px; }
.result-amber { background: rgba(245,158,11,.08); border: 1px solid rgba(245,158,11,.2); border-radius: 10px; padding: 14px 18px; }
.result-red   { background: rgba(239,68,68,.08);  border: 1px solid rgba(239,68,68,.2);  border-radius: 10px; padding: 14px 18px; }
.result-blue  { background: rgba(79,142,247,.08); border: 1px solid rgba(79,142,247,.2); border-radius: 10px; padding: 14px 18px; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #13161D !important;
    border-right: 1px solid #2A2E3D;
}
[data-testid="stSidebar"] .css-1d391kg { padding: 1rem; }

/* CARDS */
.info-card {
    background: #1A1E28;
    border: 1px solid #2A2E3D;
    border-left: 3px solid #4F8EF7;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 12px;
    color: #9BA3BC;
    margin: 8px 0;
    line-height: 1.6;
}

/* TABLES */
.styled-table { font-size: 12px; }

/* BADGE */
.badge-z1 { background: rgba(239,68,68,.12); color: #EF4444; border: 1px solid rgba(239,68,68,.2); padding: 2px 10px; border-radius: 50px; font-size: 11px; font-weight: 500; }
.badge-z2 { background: rgba(245,158,11,.12); color: #F59E0B; border: 1px solid rgba(245,158,11,.2); padding: 2px 10px; border-radius: 50px; font-size: 11px; font-weight: 500; }
.badge-z3 { background: rgba(34,197,94,.12); color: #22C55E; border: 1px solid rgba(34,197,94,.2); padding: 2px 10px; border-radius: 50px; font-size: 11px; font-weight: 500; }
.badge-z4 { background: rgba(79,142,247,.12); color: #4F8EF7; border: 1px solid rgba(79,142,247,.2); padding: 2px 10px; border-radius: 50px; font-size: 11px; font-weight: 500; }

/* PLOTLY CHART FIX */
.js-plotly-plot { border-radius: 12px; }

/* STREAMLIT OVERRIDES */
div[data-testid="metric-container"] {
    background: #13161D;
    border: 1px solid #2A2E3D;
    border-radius: 12px;
    padding: 14px 18px;
}
div[data-testid="metric-container"] label { color: #9BA3BC !important; font-size: 11px !important; }
div[data-testid="metric-container"] div[data-testid="metric-value"] { font-family: 'Syne', sans-serif; font-size: 22px !important; }

.stSelectbox label, .stNumberInput label, .stSlider label, .stCheckbox label,
.stDateInput label, .stTextInput label, .stTextArea label {
    font-size: 12px !important; color: #9BA3BC !important;
}
div[data-testid="stForm"] { background: #13161D; border: 1px solid #2A2E3D; border-radius: 12px; padding: 20px; }
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7C5CFC, #4F8EF7) !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(79,142,247,.3) !important;
}

hr { border-color: #2A2E3D !important; }
</style>
""", unsafe_allow_html=True)

# ── PLOTLY TEMPLATE ──
PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="#13161D",
        plot_bgcolor="#13161D",
        font=dict(family="DM Sans", color="#9BA3BC", size=11),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="#2A2E3D", tickcolor="#2A2E3D"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", linecolor="#2A2E3D", tickcolor="#2A2E3D"),
        legend=dict(bgcolor="#1A1E28", bordercolor="#2A2E3D", borderwidth=1),
        colorway=["#4F8EF7","#7C5CFC","#2EC4B6","#F7874F","#22C55E","#F59E0B","#EF4444","#EC4899"],
        margin=dict(l=40, r=20, t=40, b=40),
    )
)

def fmt_e(v): return f"€ {v:,.0f}".replace(",", ".")
def fmt_pct(v): return f"{v:.1f}%"

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px'>
      <div style='font-family:Syne;font-size:20px;font-weight:700;
        background:linear-gradient(90deg,#4F8EF7,#7C5CFC);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent'>
        🛡️ ActuarialFleet
      </div>
      <div style='font-size:11px;color:#5A6280;margin-top:4px'>v2.0 · Piattaforma RCA Flotte</div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    PAGE = st.radio("", [
        "📊 Dashboard",
        "🚛 Flotte",
        "⚠️ Sinistri",
        "📤 Importazione",
        "🧮 Calcolo Premi",
        "📈 Modello GLM",
        "🔺 Triangoli IBNR",
        "⭐ Credibilità",
        "📉 Grafici",
        "📄 Report",
    ], label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)
    flotte_df = get_flotte()
    st.markdown(f"""
    <div style='font-size:11px;color:#5A6280;padding:8px 0'>
      <div>🚛 <b style='color:#9BA3BC'>{len(flotte_df)}</b> flotte</div>
      <div>🚗 <b style='color:#9BA3BC'>{int(flotte_df['nveic'].sum()) if not flotte_df.empty else 0}</b> veicoli</div>
      <div style='margin-top:8px;font-size:10px'>Dati salvati in SQLite locale</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════
if PAGE == "📊 Dashboard":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>📊</div>
      <div>
        <h1>Dashboard portafoglio</h1>
        <p>Panoramica flotte, premi e sinistrosità attesa</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    flotte_df = get_flotte()
    sinistri_df = get_sinistri()

    if flotte_df.empty:
        st.info("Nessuna flotta ancora. Vai in **🚛 Flotte** per aggiungerne una.")
    else:
        calcoli = []
        for _, r in flotte_df.iterrows():
            c = calcola_premio(
                r["provincia"], int(r["nveic"]),
                CIL_MAP.get(r["cilindrata"], 1.0),
            )
            calcoli.append(c)

        tot_veic  = int(flotte_df["nveic"].sum())
        tot_prem  = sum(c["lordo_fleet"] for c in calcoli)
        tot_sin   = sum(c["sin_attesi"] for c in calcoli)
        tot_ris   = float(sinistri_df["riserva"].sum()) if not sinistri_df.empty else 0
        sin_aper  = len(sinistri_df[sinistri_df["stato"] == "aperto"]) if not sinistri_df.empty else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🚛 Flotte attive",    len(flotte_df))
        c2.metric("🚗 Veicoli totali",   f"{tot_veic:,}")
        c3.metric("💶 Premio RCA lordo", fmt_e(round(tot_prem)))
        c4.metric("📋 Sin. att./anno",   f"{tot_sin:.1f}")
        c5.metric("🔴 Sinistri aperti",  sin_aper)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 Flotte attive")
            oggi = date.today()
            rows = []
            for i, (_, r) in enumerate(flotte_df.iterrows()):
                c = calcoli[i]
                p = c["prov"]
                zona_badge = {1: "🔴 Z1", 2: "🟡 Z2", 3: "🟢 Z3", 4: "🔵 Z4"}
                stato = "✅ Attiva"
                if r.get("scadenza"):
                    try:
                        scad = datetime.strptime(str(r["scadenza"]), "%Y-%m-%d").date()
                        diff = (scad - oggi).days
                        if diff < 0: stato = "🔴 Scaduta"
                        elif diff <= 30: stato = "🟡 In scadenza"
                    except: pass
                rows.append({
                    "Nome": r["nome"],
                    "Prov.": r["provincia"],
                    "Zona": zona_badge.get(p["zona"], ""),
                    "Veicoli": int(r["nveic"]),
                    "Premio/veic.": fmt_e(round(c["lordo_rca"])),
                    "Stato": stato,
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        with col2:
            st.subheader("📊 Premio per provincia")
            prov_data = {}
            for i, (_, r) in enumerate(flotte_df.iterrows()):
                nome_p = calcoli[i]["prov"]["nome"]
                prov_data[nome_p] = prov_data.get(nome_p, 0) + calcoli[i]["lordo_fleet"]
            prov_df = pd.DataFrame(list(prov_data.items()), columns=["Provincia", "Premio"]).sort_values("Premio", ascending=True)
            fig = go.Figure(go.Bar(
                x=prov_df["Premio"], y=prov_df["Provincia"],
                orientation="h",
                marker_color=["#4F8EF7","#7C5CFC","#2EC4B6","#F7874F","#22C55E","#F59E0B"][:len(prov_df)],
                text=[fmt_e(v) for v in prov_df["Premio"]],
                textposition="outside",
            ))
            fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=280,
                              xaxis_title="Premio lordo (€)", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

        # Scadenze
        st.subheader("🔔 Scadenze nei prossimi 90 giorni")
        scad_rows = []
        for _, r in flotte_df.iterrows():
            if r.get("scadenza"):
                try:
                    scad = datetime.strptime(str(r["scadenza"]), "%Y-%m-%d").date()
                    diff = (scad - oggi).days
                    if 0 < diff <= 90:
                        scad_rows.append({"Flotta": r["nome"], "Provincia": r["provincia"],
                                          "Veicoli": int(r["nveic"]), "Scadenza": str(r["scadenza"]),
                                          "Giorni": diff})
                except: pass
        if scad_rows:
            st.dataframe(pd.DataFrame(scad_rows).sort_values("Giorni"), hide_index=True, use_container_width=True)
        else:
            st.info("Nessuna scadenza nei prossimi 90 giorni.")


# ══════════════════════════════════════════════
# FLOTTE
# ══════════════════════════════════════════════
elif PAGE == "🚛 Flotte":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>🚛</div>
      <div><h1>Anagrafica flotte</h1>
      <p>Gestione veicoli, contratti e profili di rischio</p></div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("➕ Aggiungi nuova flotta", expanded=False):
        with st.form("form_flotta"):
            c1, c2, c3 = st.columns(3)
            nome = c1.text_input("Nome / Ragione sociale *")
            prov_opts = {f"{v['nome']} ({k})": k for k, v in PROVINCE.items()}
            prov_sel  = c2.selectbox("Provincia *", list(prov_opts.keys()))
            nveic     = c3.number_input("Numero veicoli", 1, 10000, 50)

            c4, c5, c6 = st.columns(3)
            cil   = c4.selectbox("Cilindrata prevalente", ["bassa", "media", "alta", "sportiva"], index=1)
            uso   = c5.selectbox("Uso prevalente", ["svago", "promiscuo", "lavoro"], index=1)
            scad  = c6.date_input("Scadenza polizza", value=None)

            c7, c8 = st.columns(2)
            ref  = c7.text_input("Referente")
            note = c8.text_input("Note")

            if st.form_submit_button("✅ Salva flotta", type="primary"):
                if not nome:
                    st.error("Il nome è obbligatorio.")
                else:
                    add_flotta({"nome": nome, "provincia": prov_opts[prov_sel],
                                "nveic": int(nveic), "cilindrata": cil, "uso": uso,
                                "scadenza": str(scad) if scad else "",
                                "referente": ref, "note": note})
                    st.success(f"✅ Flotta '{nome}' aggiunta!")
                    st.rerun()

    st.markdown("---")
    flotte_df = get_flotte()
    if flotte_df.empty:
        st.info("Nessuna flotta. Aggiungine una dal form qui sopra.")
    else:
        oggi = date.today()
        for _, r in flotte_df.iterrows():
            p = get_prov(r["provincia"])
            c = calcola_premio(r["provincia"], int(r["nveic"]), CIL_MAP.get(r["cilindrata"], 1.0))
            zona_c = {1:"🔴", 2:"🟡", 3:"🟢", 4:"🔵"}.get(p["zona"], "⚪")
            stato  = "✅ Attiva"
            if r.get("scadenza"):
                try:
                    diff = (datetime.strptime(str(r["scadenza"]), "%Y-%m-%d").date() - oggi).days
                    if diff < 0: stato = "🔴 Scaduta"
                    elif diff <= 30: stato = f"🟡 Scade in {diff}g"
                except: pass
            sins = get_sinistri(flotta_id=int(r["id"]))

            with st.expander(f"{zona_c} **{r['nome']}** — {p['nome']} · {int(r['nveic'])} veicoli · {stato}"):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Premio lordo RCA/veic.", fmt_e(round(c["lordo_rca"])))
                col2.metric("Premio fleet totale",   fmt_e(round(c["lordo_fleet"])))
                col3.metric("Sinistri att./anno",    f"{c['sin_attesi']:.1f}")
                col4.metric("Sinistri registrati",   len(sins))

                col5, col6 = st.columns([3, 1])
                with col5:
                    st.markdown(f"""
                    | Campo | Valore |
                    |---|---|
                    | Cilindrata | {r['cilindrata']} |
                    | Uso | {r['uso']} |
                    | Scadenza | {r.get('scadenza') or '—'} |
                    | Referente | {r.get('referente') or '—'} |
                    | Imp. provinciale | {p['imp']*100:.1f}% |
                    | Frequenza collettiva | {p['freq']:.3f} sin./veic.-anno |
                    """)
                with col6:
                    if st.button("🗑️ Elimina", key=f"del_{r['id']}", type="secondary"):
                        delete_flotta(int(r["id"]))
                        st.success("Eliminata.")
                        st.rerun()


# ══════════════════════════════════════════════
# SINISTRI
# ══════════════════════════════════════════════
elif PAGE == "⚠️ Sinistri":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>⚠️</div>
      <div><h1>Gestione sinistri</h1>
      <p>Sinistri per singolo veicolo · Apertura, stato e liquidazione</p></div>
    </div>
    """, unsafe_allow_html=True)

    flotte_df = get_sinistri.__module__ and get_flotte()

    with st.expander("➕ Registra nuovo sinistro", expanded=False):
        with st.form("form_sinistro"):
            flotte_df2 = get_flotte()
            flotte_opts = {r["nome"]: int(r["id"]) for _, r in flotte_df2.iterrows()} if not flotte_df2.empty else {}
            c1, c2, c3 = st.columns(3)
            fleet_sel = c1.selectbox("Flotta *", list(flotte_opts.keys()) if flotte_opts else ["—"])
            targa     = c2.text_input("Targa veicolo *").upper()
            data_sin  = c3.date_input("Data sinistro", value=date.today())
            c4, c5, c6 = st.columns(3)
            tipo   = c4.selectbox("Tipo", ["RCA", "Furto", "Incendio", "Kasko", "Infortuni"])
            stato  = c5.selectbox("Stato", ["aperto", "riserva", "chiuso"])
            c7, c8 = st.columns(2)
            riserva = c7.number_input("Riserva (€)", 0.0, step=100.0)
            pagato  = c8.number_input("Importo pagato (€)", 0.0, step=100.0)
            desc = st.text_input("Descrizione")
            if st.form_submit_button("✅ Salva sinistro", type="primary"):
                if not targa or not flotte_opts:
                    st.error("Targa e flotta obbligatori.")
                else:
                    add_sinistro({"flotta_id": flotte_opts.get(fleet_sel),
                                  "targa": targa, "data_sinistro": str(data_sin),
                                  "tipo": tipo, "riserva": riserva,
                                  "pagato": pagato, "stato": stato, "descrizione": desc})
                    st.success("✅ Sinistro registrato!")
                    st.rerun()

    st.markdown("---")
    # Filtri
    col_f1, col_f2, col_f3 = st.columns(3)
    flt_fleet = col_f1.selectbox("Filtra per flotta", ["Tutte"] + list(get_flotte()["nome"].tolist() if not get_flotte().empty else []))
    flt_stato = col_f2.selectbox("Filtra per stato", ["Tutti", "aperto", "riserva", "chiuso"])
    flt_tipo  = col_f3.selectbox("Filtra per tipo",  ["Tutti", "RCA", "Furto", "Incendio", "Kasko", "Infortuni"])

    sins_df = get_sinistri()
    if flt_fleet != "Tutte":
        fl_row = get_flotte()
        fl_row = fl_row[fl_row["nome"] == flt_fleet]
        if not fl_row.empty:
            sins_df = get_sinistri(flotta_id=int(fl_row.iloc[0]["id"]))
    if flt_stato != "Tutti":
        sins_df = sins_df[sins_df["stato"] == flt_stato]
    if flt_tipo != "Tutti":
        sins_df = sins_df[sins_df["tipo"] == flt_tipo]

    if not sins_df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sinistri", len(sins_df))
        c2.metric("Riserva totale", fmt_e(round(sins_df["riserva"].sum())))
        c3.metric("Pagato totale",  fmt_e(round(sins_df["pagato"].sum())))
        c4.metric("Loss incurred",  fmt_e(round((sins_df["riserva"] + sins_df["pagato"]).sum())))
        st.markdown("---")

        stato_icon = {"aperto": "🔴", "riserva": "🟡", "chiuso": "🟢"}
        tipo_icon  = {"RCA": "🚗", "Furto": "🔓", "Incendio": "🔥", "Kasko": "🛡️", "Infortuni": "🧑‍⚕️"}
        for _, r in sins_df.iterrows():
            icon = tipo_icon.get(str(r.get("tipo", "")), "⚠️")
            st.markdown(f"""
            <div style='background:#1A1E28;border:1px solid #2A2E3D;border-radius:10px;
              padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;gap:14px'>
              <div style='font-size:24px'>{icon}</div>
              <div style='flex:1'>
                <div style='display:flex;align-items:center;gap:10px;margin-bottom:4px'>
                  <strong style='font-size:14px;color:#E8EAF0'>{r.get('targa','')}</strong>
                  <span style='font-size:11px;color:#9BA3BC;background:#222636;padding:2px 8px;border-radius:50px'>{r.get('tipo','')}</span>
                  <span style='font-size:11px'>{stato_icon.get(str(r.get('stato','')),'⚪')} {r.get('stato','')}</span>
                  <span style='font-size:11px;color:#5A6280'>{r.get('flotta_nome','')}</span>
                </div>
                <div style='font-size:12px;color:#5A6280'>{r.get('descrizione','') or 'Nessuna descrizione'}</div>
                <div style='font-size:12px;color:#9BA3BC;margin-top:4px;display:flex;gap:16px'>
                  <span>📅 {r.get('data_sinistro','') or '—'}</span>
                  <span>💰 Riserva: {fmt_e(r.get('riserva',0))}</span>
                  <span>✅ Pagato: {fmt_e(r.get('pagato',0))}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️", key=f"dsin_{r['id']}", help="Elimina sinistro"):
                delete_sinistro(int(r["id"]))
                st.rerun()
    else:
        st.info("Nessun sinistro trovato con i filtri selezionati.")


# ══════════════════════════════════════════════
# IMPORTAZIONE
# ══════════════════════════════════════════════
elif PAGE == "📤 Importazione":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>📤</div>
      <div><h1>Importazione dati</h1>
      <p>Carica dati da Excel (.xlsx) o CSV · Scarica template</p></div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🚛 Anagrafica flotte", "⚠️ Sinistri", "📥 Template Excel"])

    with tab1:
        st.subheader("Carica anagrafica flotte")
        st.markdown("""<div class='info-card'>
        <b>Colonne attese (case-insensitive):</b> Nome, Provincia, Veicoli, Cilindrata (bassa/media/alta/sportiva),
        Uso (svago/promiscuo/lavoro), Scadenza (YYYY-MM-DD), Referente, Note
        </div>""", unsafe_allow_html=True)
        file_fl = st.file_uploader("Trascina o seleziona il file", type=["xlsx", "xls", "csv"], key="fl_up")
        if file_fl:
            try:
                if file_fl.name.endswith(".csv"):
                    df = pd.read_csv(file_fl, sep=None, engine="python")
                else:
                    df = pd.read_excel(file_fl)
                st.dataframe(df.head(10), use_container_width=True)
                if st.button("✅ Importa flotte", type="primary"):
                    n = import_flotte(df)
                    st.success(f"✅ {n} flotte importate!")
                    st.rerun()
            except Exception as e:
                st.error(f"Errore lettura file: {e}")

    with tab2:
        st.subheader("Carica sinistri")
        st.markdown("""<div class='info-card'>
        <b>Colonne attese:</b> Targa, Flotta (nome), Data sinistro, Tipo (RCA/Furto/Incendio/Kasko/Infortuni),
        Riserva, Pagato, Stato (aperto/riserva/chiuso), Descrizione
        </div>""", unsafe_allow_html=True)
        file_sin = st.file_uploader("Trascina o seleziona il file sinistri", type=["xlsx", "xls", "csv"], key="sin_up")
        if file_sin:
            try:
                if file_sin.name.endswith(".csv"):
                    df_s = pd.read_csv(file_sin, sep=None, engine="python")
                else:
                    df_s = pd.read_excel(file_sin)
                st.dataframe(df_s.head(10), use_container_width=True)
                flotte_df3 = get_flotte()
                if st.button("✅ Importa sinistri", type="primary"):
                    n = import_sinistri(df_s, flotte_df3)
                    st.success(f"✅ {n} sinistri importati!")
                    st.rerun()
            except Exception as e:
                st.error(f"Errore lettura file: {e}")

    with tab3:
        st.subheader("Scarica template Excel")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Template flotte**")
            df_tmpl = pd.DataFrame([
                {"Nome": "Esempio Srl", "Provincia": "MI", "Veicoli": 100, "Cilindrata": "media",
                 "Uso": "promiscuo", "Scadenza": "2025-12-31", "Referente": "Mario Rossi", "Note": ""},
                {"Nome": "Test Spa",    "Provincia": "CE", "Veicoli": 50,  "Cilindrata": "alta",
                 "Uso": "lavoro",    "Scadenza": "2026-06-30", "Referente": "Lucia Bianchi","Note": ""},
            ])
            buf = io.BytesIO()
            df_tmpl.to_excel(buf, index=False)
            st.download_button("📥 Scarica template flotte", buf.getvalue(),
                               "template_flotte.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c2:
            st.markdown("**Template sinistri**")
            df_tmpl2 = pd.DataFrame([
                {"Targa": "AB123CD", "Flotta": "Esempio Srl", "Data sinistro": "2025-03-15",
                 "Tipo": "RCA", "Riserva": 5000, "Pagato": 0, "Stato": "aperto", "Descrizione": "Tamponamento"},
                {"Targa": "EF456GH", "Flotta": "Esempio Srl", "Data sinistro": "2025-01-22",
                 "Tipo": "Furto", "Riserva": 0, "Pagato": 18000, "Stato": "chiuso", "Descrizione": "Furto totale"},
            ])
            buf2 = io.BytesIO()
            df_tmpl2.to_excel(buf2, index=False)
            st.download_button("📥 Scarica template sinistri", buf2.getvalue(),
                               "template_sinistri.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ══════════════════════════════════════════════
# CALCOLO PREMI
# ══════════════════════════════════════════════
elif PAGE == "🧮 Calcolo Premi":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>🧮</div>
      <div><h1>Calcolo premi</h1>
      <p>RCA + F&I + Kasko · Franchigie, scoperti, massimali · Tassazione L.B. 2026</p></div>
    </div>
    """, unsafe_allow_html=True)

    flotte_df4 = get_flotte()
    if not flotte_df4.empty:
        fleet_sel = st.selectbox("Carica da flotta (opzionale)",
            ["— Inserisci manualmente —"] + flotte_df4["nome"].tolist())
        if fleet_sel != "— Inserisci manualmente —":
            fr = flotte_df4[flotte_df4["nome"] == fleet_sel].iloc[0]
    else:
        fleet_sel = "— Inserisci manualmente —"

    prov_opts2 = {f"{v['nome']} ({k})": k for k, v in PROVINCE.items()}

    col_sx, col_dx = st.columns([1, 1])

    with col_sx:
        st.subheader("⚙️ Parametri tariffari")
        prov_default = 0
        if fleet_sel != "— Inserisci manualmente —":
            prov_key = fr["provincia"]
            prov_names = list(prov_opts2.keys())
            matches = [i for i, k in enumerate(prov_names) if prov_opts2[k] == prov_key]
            if matches: prov_default = matches[0]
        prov_sel2 = st.selectbox("Provincia", list(prov_opts2.keys()), index=prov_default)
        prov_code = prov_opts2[prov_sel2]
        nveic2 = st.number_input("Numero veicoli", 1, 10000,
            int(fr["nveic"]) if fleet_sel != "— Inserisci manualmente —" else 200)
        cil_sel  = st.selectbox("Cilindrata", list(CIL_MAP.keys()), index=1)
        bm_sel   = st.selectbox("Classe BM media", list(BM_MAP.keys()), index=2)
        uso_sel  = st.selectbox("Uso veicolo", list(USO_MAP.keys()), index=1)
        sconto   = st.slider("Sconto fleet (%)", 0, 20, 8) / 100

        st.markdown("---")
        st.subheader("🛡️ Franchigia & Scoperto RCA")
        rca_tipo = st.selectbox("Tipo clausola", ["Nessuna", "Franchigia assoluta", "Scoperto %", "Franchigia + Scoperto"])
        rca_franc = rca_scop_pct = rca_scop_min = 0.0; rca_scop_max = np.inf
        if "Franchigia" in rca_tipo:
            rca_franc = st.select_slider("Franchigia RCA (€)", [0,250,500,750,1000,1500,2000], value=500)
        if "Scoperto" in rca_tipo:
            rca_scop_pct = st.select_slider("Scoperto RCA (%)", [5,10,15,20,25], value=10) / 100
            rca_scop_min = st.select_slider("Minimo scoperto (€)", [200,250,500,750,1000], value=500)
            rca_scop_max_val = st.select_slider("Massimo scoperto (€)", [0,2000,3000,5000,10000], value=3000)
            rca_scop_max = rca_scop_max_val if rca_scop_max_val > 0 else np.inf

        st.markdown("---")
        st.subheader("📐 Massimali RCA")
        mass_pers = st.select_slider("Massimale persone (€)", [6_070_000,10_000_000,15_000_000,25_000_000,50_000_000], value=10_000_000)

        st.markdown("---")
        st.subheader("🔥 Garanzie F&I")
        valore    = st.number_input("Valore assicurato (€)", 1000, 500000, 18000, 1000)
        sval_pct  = st.select_slider("Svalutazione annua (%)", [0,10,15,20,25], value=15) / 100
        anni_vet  = st.slider("Anni di vetustà", 0, 15, 3)
        furto     = st.checkbox("Furto", True)
        if furto:
            c_f1, c_f2 = st.columns(2)
            franc_f = c_f1.select_slider("Franchigia furto (€)", [0,500,1000,1500,2000,3000], value=500)
            scop_f  = c_f2.select_slider("Scoperto furto (%)", [0,10,15,20,25,30], value=15) / 100
            scop_f_min = st.select_slider("Min. scoperto furto (€)", [0,250,400,500,750,1000], value=400)
            gps = st.checkbox("GPS/antifurto certificato (−15%)", True)
        else:
            franc_f = scop_f = scop_f_min = 0; gps = False
        incendio = st.checkbox("Incendio", True)
        if incendio:
            c_i1, c_i2 = st.columns(2)
            franc_i = c_i1.select_slider("Franchigia incendio (€)", [0,250,500,1000], value=500)
            scop_i  = c_i2.select_slider("Scoperto incendio (%)", [0,10,15,20,25], value=15) / 100
        else:
            franc_i = scop_i = 0
        kasko = st.checkbox("Kasko danni propri", False)
        if kasko:
            c_k1, c_k2 = st.columns(2)
            scop_k     = c_k1.select_slider("Scoperto kasko (%)", [10,15,20,25], value=10) / 100
            scop_k_min = c_k2.select_slider("Min. scoperto kasko (€)", [500,750,1000,1500], value=500)
            mass_k     = st.select_slider("Massimale kasko (€)", [15000,20000,30000,50000], value=20000)
        else:
            scop_k = scop_k_min = 0; mass_k = 20000
        infortuni = st.checkbox("Infortuni conducente", False)
        prem_infort = st.number_input("Premio infortuni (€/veic.)", 0.0, 200.0, 20.0) if infortuni else 0

    # Calcolo
    ris = calcola_premio(
        prov_code, int(nveic2),
        CIL_MAP[cil_sel], BM_MAP[bm_sel], USO_MAP[uso_sel], sconto,
        rca_franc, rca_scop_pct, rca_scop_min, rca_scop_max, float(mass_pers),
        valore, sval_pct, anni_vet,
        furto, franc_f if furto else 0, scop_f if furto else 0, scop_f_min if furto else 0, gps,
        incendio, franc_i if incendio else 0, scop_i if incendio else 0,
        kasko, scop_k if kasko else 0, scop_k_min if kasko else 0, mass_k if kasko else 20000,
        infortuni, prem_infort,
    )

    with col_dx:
        st.subheader("📋 Riepilogo tariffario")
        p = ris["prov"]
        zona_c = {1:"🔴", 2:"🟡", 3:"🟢", 4:"🔵"}.get(p["zona"], "⚪")

        st.markdown(f"""
        <div style='background:#1A1E28;border:1px solid #2A2E3D;border-radius:12px;padding:16px;margin-bottom:12px'>
          <div style='font-size:13px;color:#9BA3BC;margin-bottom:10px'>
            {zona_c} <b style='color:#E8EAF0'>{p['nome']}</b> &nbsp;·&nbsp;
            Zona {p['zona']} &nbsp;·&nbsp; Imp. prov. {p['imp']*100:.1f}%
          </div>
          <table style='width:100%;font-size:12px;color:#9BA3BC;border-collapse:collapse'>
            <tr><td>Premio puro base</td><td style='text-align:right;font-family:monospace'>{fmt_e(ris['pp_base'])}</td></tr>
            <tr><td style='color:#22C55E'>– Riduzione franchigia/scoperto</td><td style='text-align:right;font-family:monospace;color:#22C55E'>– {fmt_e(ris['risp_franc'])}</td></tr>
            <tr><td>× Adj. massimale</td><td style='text-align:right;font-family:monospace'>{ris['mass_adj']:.4f}×</td></tr>
            <tr><td>Premio puro adj.</td><td style='text-align:right;font-family:monospace'>{fmt_e(ris['pp_adj'])}</td></tr>
            <tr><td style='border-top:1px solid #2A2E3D'>Premio netto RCA/veic.</td><td style='text-align:right;font-family:monospace;border-top:1px solid #2A2E3D'>{fmt_e(ris['netto'])}</td></tr>
            <tr><td>+ SSN 10,5%</td><td style='text-align:right;font-family:monospace'>{fmt_e(ris['ssn'])}</td></tr>
            <tr><td>+ Imp. prov. {p['imp']*100:.1f}%</td><td style='text-align:right;font-family:monospace'>{fmt_e(ris['imp_prov'])}</td></tr>
            <tr style='background:rgba(34,197,94,.06)'><td><b style='color:#22C55E'>Lordo RCA/veic.</b></td><td style='text-align:right;font-family:monospace;font-weight:700;color:#22C55E'>{fmt_e(ris['lordo_rca'])}</td></tr>
            {"<tr><td>+ Furto" + (" (GPS)" if gps else "") + " lordo</td><td style='text-align:right;font-family:monospace'>" + fmt_e(ris['lordo_furto']) + "</td></tr>" if furto else ""}
            {"<tr><td>+ Incendio lordo</td><td style='text-align:right;font-family:monospace'>" + fmt_e(ris['lordo_inc']) + "</td></tr>" if incendio else ""}
            {"<tr><td>+ Kasko lordo</td><td style='text-align:right;font-family:monospace'>" + fmt_e(ris['lordo_kasko']) + "</td></tr>" if kasko else ""}
            {"<tr><td>+ Infortuni lordo</td><td style='text-align:right;font-family:monospace'>" + fmt_e(ris['lordo_infort']) + "</td></tr>" if infortuni else ""}
          </table>
        </div>
        """, unsafe_allow_html=True)

        c_r1, c_r2 = st.columns(2)
        c_r1.metric("💶 Premio lordo/veicolo", fmt_e(round(ris["lordo_tot"])))
        c_r2.metric("💼 Premio totale fleet",  fmt_e(round(ris["lordo_fleet"])))

        if rca_tipo != "Nessuna":
            st.info(f"📊 **Quota franchigia/scoperto a carico flotta:** {fmt_e(round(ris['quota_flotta']))}/anno  "
                    f"(per sinistro: {fmt_e(round(ris['quota_flotta']/max(ris['sin_attesi'],0.1)))})")

        # Grafico composizione
        labels = ["Premio puro", "LAE+Spese", "Margini", "SSN", "Imp.prov."]
        values = [
            ris["pp_adj"],
            ris["pp_adj"] * 0.26,
            ris["pp_adj"] * 0.05 + 12.5,
            ris["ssn"],
            ris["imp_prov"],
        ]
        fig_c = go.Figure(go.Pie(labels=labels, values=[round(v,2) for v in values],
            hole=0.6, marker_colors=["#4F8EF7","#7C5CFC","#2EC4B6","#F7874F","#22C55E"],
            textinfo="label+percent"))
        fig_c.update_layout(**PLOTLY_TEMPLATE["layout"], height=250,
                            showlegend=False, title="Composizione premio lordo RCA")
        st.plotly_chart(fig_c, use_container_width=True)


# ══════════════════════════════════════════════
# GLM
# ══════════════════════════════════════════════
elif PAGE == "📈 Modello GLM":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>📈</div>
      <div><h1>Modello GLM</h1>
      <p>Frequenza (Poisson/NB) · Severità (Gamma/Lognormale) · Premio puro</p></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Parametri frequenza")
        freq = st.slider("Frequenza base λ", 0.02, 0.25, 0.085, 0.005)
        kappa = st.slider("Dispersione κ (NB)", 1, 30, 8)
        dist_f = st.selectbox("Distribuzione frequenza", ["Poisson", "Negative Binomial"])
        st.subheader("Parametri severità")
        sev   = st.slider("Severità media μ (€)", 500, 8000, 2650, 50)
        cov   = st.slider("CoV severità (%)", 30, 150, 72) / 100
        dist_s = st.selectbox("Distribuzione severità", ["Gamma", "Lognormale", "Tweedie"])

    res = glm_parametrico(freq, kappa, sev, cov, dist_f == "Negative Binomial")

    with col2:
        st.subheader("Risultati GLM")
        c1, c2 = st.columns(2)
        c1.metric("Premio puro",  fmt_e(round(res["pp"])))
        c2.metric("Std. dev.",    fmt_e(round(res["sd"])))
        c1.metric("VaR 95%",      fmt_e(round(res["var_95"])))
        c2.metric("VaR 99,5%",    fmt_e(round(res["var_99_5"])))
        st.metric("Shape α (Gamma)",  f"{res['alpha']:.2f}")
        od_label = "→ usa Negative Binomial ✓" if res["od"] > 1.3 else "→ Poisson ok"
        st.metric("Overdispersion Var/Media", f"{res['od']:.3f}  {od_label}")
        st.metric("CoV sinistri composti", f"{res['cov_comp']:.1f}%")
        st.info(f"**Modello:** {dist_f} (freq.) × {dist_s} (sev.) · Link: log · Offset: log(esposizione)")

    st.subheader("Relativities tariffarie")
    rels = pd.DataFrame([
        {"Fattore": "Zona", "Categoria": "Zona 1 (metropoli)",     "Relativity": 1.90},
        {"Fattore": "Zona", "Categoria": "Zona 2 (capoluogo)",      "Relativity": 1.50},
        {"Fattore": "Zona", "Categoria": "Zona 3 (media — base)",   "Relativity": 1.00},
        {"Fattore": "Zona", "Categoria": "Zona 4 (rurale)",         "Relativity": 0.65},
        {"Fattore": "Età",  "Categoria": "18–25 anni",              "Relativity": 2.10},
        {"Fattore": "Età",  "Categoria": "26–35 anni",              "Relativity": 1.40},
        {"Fattore": "Età",  "Categoria": "36–55 (base)",            "Relativity": 1.00},
        {"Fattore": "Età",  "Categoria": "> 65 anni",               "Relativity": 1.30},
        {"Fattore": "BM",   "Categoria": "Classe BM 1",             "Relativity": 0.50},
        {"Fattore": "BM",   "Categoria": "Classe BM 7 (base)",      "Relativity": 1.00},
        {"Fattore": "BM",   "Categoria": "Classe BM 18",            "Relativity": 1.80},
    ])
    fig_r = px.bar(rels, x="Relativity", y="Categoria", color="Fattore", orientation="h",
                   color_discrete_map={"Zona":"#4F8EF7","Età":"#7C5CFC","BM":"#2EC4B6"},
                   title="Relativities tariffarie (base = 1.00)")
    fig_r.add_vline(x=1.0, line_dash="dash", line_color="#9BA3BC", opacity=0.6)
    fig_r.update_layout(**PLOTLY_TEMPLATE["layout"], height=380)
    st.plotly_chart(fig_r, use_container_width=True)


# ══════════════════════════════════════════════
# TRIANGOLI IBNR
# ══════════════════════════════════════════════
elif PAGE == "🔺 Triangoli IBNR":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>🔺</div>
      <div><h1>Triangoli IBNR — Chain Ladder</h1>
      <p>Sviluppo sinistri · Fattori LDF · Stima riserve</p></div>
    </div>
    """, unsafe_allow_html=True)

    if "triangle" not in st.session_state:
        st.session_state.triangle = [list(r) for r in DEFAULT_TRIANGLE]

    st.subheader("Inserisci i dati del triangolo (€000)")
    st.info("Lascia vuote le celle future. Il metodo Chain Ladder le stima automaticamente.")

    years = [2019, 2020, 2021, 2022, 2023]
    cols_hdr = st.columns([1] + [1] * 5)
    cols_hdr[0].markdown("**Anno**")
    for i in range(5):
        cols_hdr[i+1].markdown(f"**Sv. {i+1}**")

    tri = st.session_state.triangle
    for y, yr in enumerate(years):
        row_cols = st.columns([1] + [1] * 5)
        row_cols[0].markdown(f"**{yr}**")
        for d in range(5):
            val = tri[y][d]
            new_val = row_cols[d+1].number_input("",
                value=float(val) if val is not None else 0.0,
                min_value=0.0, step=10.0,
                key=f"tri_{y}_{d}",
                label_visibility="collapsed",
                disabled=(val is None))
            if val is not None:
                tri[y][d] = new_val

    cl = chain_ladder(tri)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("LDF — Fattori di sviluppo")
        ldf_df = pd.DataFrame([
            {"Periodo": f"{i+1}→{i+2}", "LDF": f"{l:.4f}", "CDF-to-ult.": f"{cl['cdfs'][i]:.4f}"}
            for i, l in enumerate(cl["ldfs"])
        ] + [{"Periodo": "Tail", "LDF": "1.0000", "CDF-to-ult.": "1.0000"}])
        st.dataframe(ldf_df, hide_index=True, use_container_width=True)

    with col2:
        st.subheader("Riserva IBNR stimata")
        ibnr_df = pd.DataFrame(cl["ibnr_rows"])
        ibnr_df.columns = ["Anno", "Ultimate (€000)", "Pagato (€000)", "IBNR (€000)"]
        st.dataframe(ibnr_df, hide_index=True, use_container_width=True)
        st.metric("📊 IBNR totale stimato", f"{cl['total_ibnr']:,.0f} K")

    # Grafico sviluppo
    fig_tri = go.Figure()
    colors_tri = ["#4F8EF7","#7C5CFC","#2EC4B6","#F7874F","#22C55E"]
    for y, yr in enumerate(years):
        y_vals = [cl["full"][y][d] for d in range(5) if cl["full"][y][d] is not None]
        x_vals = list(range(1, len(y_vals)+1))
        fig_tri.add_trace(go.Scatter(x=x_vals, y=y_vals, name=str(yr),
            line=dict(color=colors_tri[y], width=2),
            mode="lines+markers"))
    fig_tri.update_layout(**PLOTLY_TEMPLATE["layout"], height=300,
                          title="Sviluppo cumulato per anno di accadimento",
                          xaxis_title="Anno di sviluppo", yaxis_title="Pagato cumulato (€000)")
    st.plotly_chart(fig_tri, use_container_width=True)


# ══════════════════════════════════════════════
# CREDIBILITÀ
# ══════════════════════════════════════════════
elif PAGE == "⭐ Credibilità":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>⭐</div>
      <div><h1>Credibilità Bühlmann-Straub</h1>
      <p>Experience rating · Tariffazione per singola flotta</p></div>
    </div>
    """, unsafe_allow_html=True)

    flotte_df5 = get_flotte()
    if not flotte_df5.empty:
        fleet_cred = st.selectbox("Carica parametri da flotta",
            ["— Manuale —"] + flotte_df5["nome"].tolist())
    else:
        fleet_cred = "— Manuale —"

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Parametri")
        lcoll_default = 0.085
        exp_default   = 200
        if fleet_cred != "— Manuale —":
            fr5 = flotte_df5[flotte_df5["nome"] == fleet_cred].iloc[0]
            p5  = get_prov(fr5["provincia"])
            lcoll_default = p5["freq"]
            exp_default   = int(fr5["nveic"])
        lcoll = st.slider("λ collettiva", 0.02, 0.20, lcoll_default, 0.005)
        exp_v = st.slider("Veicoli/anno", 20, 2000, exp_default, 10)
        anni  = st.slider("Anni di osservazione", 1, 7, 3)
        lobs  = st.slider("λ osservata fleet", 0.01, 0.30, 0.07, 0.005)
        var_b = st.slider("σ²_between", 0.0001, 0.005, 0.0008, 0.0001, format="%.4f")
        mu_f  = st.slider("Severità media fleet (€)", 500, 8000, 2531, 100)

    res_c = credibilita(lcoll, exp_v, anni, lobs, var_b, mu_f)

    with col2:
        st.subheader("Risultati")
        c1, c2 = st.columns(2)
        c1.metric("k = σ²_w/σ²_b",   f"{res_c['k']:.2f}")
        c2.metric("n = veic × anni",  f"{res_c['n']:,.0f}")
        c1.metric("Credibilità Z",    f"{res_c['Z']*100:.1f}%")
        c2.metric("λ* credibilizzata",f"{res_c['lstar']:.4f}")
        c1.metric("μ* severità",      fmt_e(round(res_c["mu_star"])))
        c2.metric("Premio puro cred.",fmt_e(round(res_c["pp_star"])))

        delta_str = f"{res_c['delta']:+.1f}%"
        if res_c["delta"] <= 0:
            st.success(f"✅ Sconto: λ* = {res_c['lstar']:.4f} ({delta_str} vs collettivo)")
        else:
            st.warning(f"⚠️ Malus: λ* = {res_c['lstar']:.4f} ({delta_str} vs collettivo)")

    # Storico
    st.subheader("Storico sinistri fleet")
    if "cred_rows" not in st.session_state:
        st.session_state.cred_rows = pd.DataFrame([
            {"Anno": 2022, "Veic.-anno": 200, "Sinistri": 14, "Freq. obs.": 0.070},
            {"Anno": 2023, "Veic.-anno": 200, "Sinistri": 12, "Freq. obs.": 0.060},
            {"Anno": 2024, "Veic.-anno": 200, "Sinistri": 16, "Freq. obs.": 0.080},
        ])
    edited = st.data_editor(st.session_state.cred_rows, num_rows="dynamic",
                            use_container_width=True, hide_index=True)
    st.session_state.cred_rows = edited

    # Grafico sensibilità Z
    exp_range = np.arange(20, 2020, 20)
    fig_z = go.Figure()
    for an, col in [(1,"#4F8EF7"),(3,"#7C5CFC"),(5,"#2EC4B6"),(7,"#F7874F")]:
        k = lcoll / var_b
        z_vals = exp_range * an / (exp_range * an + k) * 100
        fig_z.add_trace(go.Scatter(x=exp_range, y=z_vals, name=f"{an} anni",
            line=dict(color=col, width=2), mode="lines"))
    fig_z.update_layout(**PLOTLY_TEMPLATE["layout"], height=280,
                        title="Sensibilità Z all'esposizione",
                        xaxis_title="Veicoli-anno", yaxis_title="Z (%)")
    st.plotly_chart(fig_z, use_container_width=True)


# ══════════════════════════════════════════════
# GRAFICI
# ══════════════════════════════════════════════
elif PAGE == "📉 Grafici":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>📉</div>
      <div><h1>Grafici analitici</h1>
      <p>Portafoglio · Sinistri · Premi · Loss ratio</p></div>
    </div>
    """, unsafe_allow_html=True)

    flotte_df6 = get_flotte()
    sinistri_df6 = get_sinistri()

    if flotte_df6.empty:
        st.info("Aggiungi flotte per vedere i grafici.")
    else:
        calcoli6 = [calcola_premio(r["provincia"], int(r["nveic"]), CIL_MAP.get(r["cilindrata"],1.0))
                    for _, r in flotte_df6.iterrows()]

        col1, col2 = st.columns(2)

        with col1:
            # Donut portafoglio
            fig1 = go.Figure(go.Pie(
                labels=flotte_df6["nome"].tolist(),
                values=flotte_df6["nveic"].tolist(),
                hole=0.6,
                marker_colors=["#4F8EF7","#7C5CFC","#2EC4B6","#F7874F","#22C55E","#F59E0B","#EF4444"],
            ))
            fig1.update_layout(**PLOTLY_TEMPLATE["layout"], height=300,
                               title="Composizione portafoglio (veicoli)")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Premio per provincia
            pm = {}
            for i, (_, r) in enumerate(flotte_df6.iterrows()):
                nm = calcoli6[i]["prov"]["nome"]
                pm[nm] = pm.get(nm, 0) + calcoli6[i]["lordo_fleet"]
            pm_df = pd.DataFrame(list(pm.items()), columns=["Provincia","Premio"]).sort_values("Premio")
            fig2 = go.Figure(go.Bar(
                x=pm_df["Premio"], y=pm_df["Provincia"], orientation="h",
                marker_color="#4F8EF7",
                text=[fmt_e(v) for v in pm_df["Premio"]], textposition="outside",
            ))
            fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=300,
                               title="Premio lordo RCA per provincia", xaxis_title="€")
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            # Frequenza per zona
            freq_df = pd.DataFrame([{
                "Flotta": r["nome"],
                "Freq.": calcoli6[i]["prov"]["freq"],
                "Zona": f"Zona {calcoli6[i]['prov']['zona']}",
            } for i, (_, r) in enumerate(flotte_df6.iterrows())])
            color_map = {"Zona 1":"#EF4444","Zona 2":"#F59E0B","Zona 3":"#22C55E","Zona 4":"#4F8EF7"}
            fig3 = px.bar(freq_df, x="Flotta", y="Freq.", color="Zona",
                          color_discrete_map=color_map, title="Frequenza sinistri per flotta")
            fig3.update_layout(**PLOTLY_TEMPLATE["layout"], height=300)
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            if not sinistri_df6.empty:
                tipi6 = sinistri_df6.groupby("tipo").agg(
                    Riserva=("riserva","sum"), Pagato=("pagato","sum")).reset_index()
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(name="Riserva", x=tipi6["tipo"], y=tipi6["Riserva"],
                    marker_color="#F59E0B"))
                fig4.add_trace(go.Bar(name="Pagato", x=tipi6["tipo"], y=tipi6["Pagato"],
                    marker_color="#22C55E"))
                fig4.update_layout(**PLOTLY_TEMPLATE["layout"], height=300,
                                   barmode="group", title="Sinistri: importo per tipo")
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Registra sinistri per vedere questo grafico.")

        # Loss ratio
        st.subheader("📊 Loss ratio per flotta (premi vs sinistri)")
        premi6  = [round(c["lordo_fleet"]) for c in calcoli6]
        sin_tot = [float(sinistri_df6[sinistri_df6["flotta_id"] == int(r["id"])]["riserva"].sum())
                   for _, r in flotte_df6.iterrows()] if not sinistri_df6.empty else [0]*len(flotte_df6)
        lr6     = [round(s/p*100,1) if p>0 else 0 for s,p in zip(sin_tot,premi6)]
        nomi6   = flotte_df6["nome"].tolist()

        fig5 = make_subplots(specs=[[{"secondary_y": True}]])
        fig5.add_trace(go.Bar(x=nomi6, y=premi6, name="Premio lordo",
            marker_color="rgba(79,142,247,0.5)"), secondary_y=False)
        fig5.add_trace(go.Scatter(x=nomi6, y=lr6, name="Loss ratio %",
            line=dict(color="#EF4444", width=2), mode="lines+markers",
            marker=dict(size=8)), secondary_y=True)
        fig5.add_hline(y=70, line_dash="dash", line_color="#F59E0B",
                       annotation_text="Target 70%", secondary_y=True)
        fig5.update_layout(**PLOTLY_TEMPLATE["layout"], height=320)
        fig5.update_yaxes(title_text="Premio lordo (€)", secondary_y=False)
        fig5.update_yaxes(title_text="Loss ratio (%)", secondary_y=True)
        st.plotly_chart(fig5, use_container_width=True)


# ══════════════════════════════════════════════
# REPORT
# ══════════════════════════════════════════════
elif PAGE == "📄 Report":
    st.markdown("""
    <div class='main-header'>
      <div style='font-size:32px'>📄</div>
      <div><h1>Report attuariale</h1>
      <p>Sintesi portafoglio · Confronto flotte · Export PDF professionale</p></div>
    </div>
    """, unsafe_allow_html=True)

    flotte_df7  = get_flotte()
    sinistri_df7 = get_sinistri()

    if flotte_df7.empty:
        st.info("Aggiungi flotte per generare il report.")
    else:
        calcoli7 = [calcola_premio(r["provincia"], int(r["nveic"]), CIL_MAP.get(r["cilindrata"],1.0))
                    for _, r in flotte_df7.iterrows()]

        tv7 = int(flotte_df7["nveic"].sum())
        tp7 = sum(c["lordo_fleet"] for c in calcoli7)
        ts7 = sum(c["sin_attesi"] for c in calcoli7)
        tr7 = float(sinistri_df7["riserva"].sum()) if not sinistri_df7.empty else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Veicoli totali",    f"{tv7:,}")
        c2.metric("Premio RCA lordo",  fmt_e(round(tp7)))
        c3.metric("Sin. att./anno",    f"{ts7:.1f}")
        c4.metric("Riserva totale",    fmt_e(round(tr7)))

        st.markdown("---")
        rows7 = []
        for i, (_, r) in enumerate(flotte_df7.iterrows()):
            c = calcoli7[i]; p = c["prov"]
            sins7 = sinistri_df7[sinistri_df7["flotta_id"] == int(r["id"])] if not sinistri_df7.empty else pd.DataFrame()
            ris7  = float(sins7["riserva"].sum()) if not sins7.empty else 0
            lr7   = f"{ris7/c['lordo_fleet']*100:.1f}%" if c["lordo_fleet"] > 0 else "—"
            rows7.append({
                "Flotta":          r["nome"],
                "Provincia":       p["nome"],
                "Zona":            f"Z{p['zona']}",
                "Veicoli":         int(r["nveic"]),
                "Freq.":           f"{p['freq']:.3f}",
                "Premio/veic.":    fmt_e(round(c["lordo_rca"])),
                "Premio fleet":    fmt_e(round(c["lordo_fleet"])),
                "Sin. att.":       f"{c['sin_attesi']:.1f}",
                "Loss ratio":      lr7,
                "Imp. prov.":      f"{p['imp']*100:.1f}%",
            })
        st.dataframe(pd.DataFrame(rows7), hide_index=True, use_container_width=True)

        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            st.subheader("📥 Esporta Excel")
            buf_xl = io.BytesIO()
            with pd.ExcelWriter(buf_xl, engine="openpyxl") as writer:
                pd.DataFrame(rows7).to_excel(writer, sheet_name="Portafoglio", index=False)
                if not sinistri_df7.empty:
                    sinistri_df7.to_excel(writer, sheet_name="Sinistri", index=False)
                flotte_df7.to_excel(writer, sheet_name="Anagrafica", index=False)
            st.download_button("📊 Scarica Excel completo", buf_xl.getvalue(),
                               f"actfleet_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               type="primary")

        with col_btn2:
            st.subheader("📄 Esporta PDF")
            if st.button("🖨️ Genera PDF professionale", type="primary"):
                with st.spinner("Generazione PDF in corso..."):
                    pdf_bytes = genera_report(flotte_df7, sinistri_df7, calcoli7)
                st.download_button("📥 Scarica PDF", pdf_bytes,
                                   f"actfleet_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                                   "application/pdf")
                st.success("✅ PDF generato!")
