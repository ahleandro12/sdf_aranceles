import streamlit as st
import streamlit_authenticator as stauth

st.set_page_config(
    page_title="SDF BIOTEC",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Credenciales ──────────────────────────────────────────────────────────────

credentials = {
    "usernames": {
        "demo": {
            "name": "Demo User",
            "password": "$2b$12$2Hb9VN3tyU6tvVICFu4DU.qFo81HFJo61EiFieM1Wk.U9N2TfwJCy",
            "role": "demo",
        },
        "admin": {
            "name": "Leandro",
            "password": "$2b$12$RQKN4ExKWVIGDvjqo0NDFuiotRvQ8m3LnHrcfqBcN23wLwXrFhc6G",
            "role": "admin",
        },
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "sdf_biotec_cookie",
    "sdf_biotec_secret_key_2024_secure",
    cookie_expiry_days=7,
)

# ── Login ─────────────────────────────────────────────────────────────────────

authenticator.login(location="main")

name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

if authentication_status is None:
    st.info("👋 Ingresá con usuario **demo** / contraseña **demo2024** para explorar la app.")
    st.stop()

if authentication_status is False:
    st.error("Usuario o contraseña incorrectos.")
    st.stop()

if authentication_status is False:
    st.error("Usuario o contraseña incorrectos.")
    st.stop()

if authentication_status is None:
    st.info("👋 Ingresá con usuario **demo** / contraseña **demo2024** para explorar la app.")
    st.stop()

# ── Usuario autenticado ───────────────────────────────────────────────────────

role = credentials["usernames"][username]["role"]
is_demo = role == "demo"

import os
if is_demo:
    os.environ["SDF_DB_PATH"] = "data/demo.db"
else:
    os.environ.pop("SDF_DB_PATH", None)

import db
from modulos.ui import inject_css
from modulos import costeo, historial, sim, validacion, importar, config, tarifarios, posiciones

db.init_db()
if is_demo:
    db.init_demo_data()

inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("**🧪 BIOTEC**")
    st.caption("SDF Costeo v1.0")
    if is_demo:
        st.markdown(
            '<div style="background:#E65100;color:white;font-size:10px;'
            'padding:3px 8px;border-radius:4px;text-align:center;margin-bottom:4px;">MODO DEMO</div>',
            unsafe_allow_html=True
        )
    st.divider()

    opciones = ["🏠 Bienvenida", "📋 Costeo", "📁 Historial"]
    if not is_demo:
        opciones.append("⚙️ Config")

    seccion = st.radio("", opciones, label_visibility="collapsed")
    st.divider()
    cfg = db.get_all_config()
    st.metric("TC", f"${float(cfg.get('tc', 1400)):,.0f}")
    st.divider()
    authenticator.logout("Salir", location="sidebar")

# ── Secciones ─────────────────────────────────────────────────────────────────

if seccion == "🏠 Bienvenida":
    from modulos import bienvenida
    bienvenida.render(is_demo=is_demo)

elif seccion == "📋 Costeo":
    if is_demo:
        costeo.render()
    else:
        tab1, tab2 = st.tabs(["Nuevo costeo", "Importar lote"])
        with tab1:
            costeo.render()
        with tab2:
            importar.render()

elif seccion == "📁 Historial":
    if is_demo:
        historial.render()
    else:
        tab1, tab2, tab3 = st.tabs(["Historial", "Liquidacion SIM", "Validacion despacho"])
        with tab1:
            historial.render()
        with tab2:
            sim.render()
        with tab3:
            validacion.render()

elif seccion == "⚙️ Config":
    tab1, tab2, tab3 = st.tabs(["Configuracion", "Tarifarios", "Posiciones NCM"])
    with tab1:
        config.render()
    with tab2:
        tarifarios.render()
    with tab3:
        posiciones.render()
