"""
bienvenida.py — Pantalla de bienvenida y tour interactivo para modo demo
"""
import streamlit as st

def render(is_demo: bool = True):

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1F3864,#2E75B6);
                border-radius:12px;padding:32px 36px;margin-bottom:24px;">
        <h1 style="color:white;margin:0;font-size:2rem;">🧪 SDF BIOTEC</h1>
        <p style="color:#B3D4F5;margin:8px 0 0 0;font-size:1.1rem;">
            Sistema de costeo de importaciones para la industria alimentaria argentina
        </p>
    </div>
    """, unsafe_allow_html=True)

    if is_demo:
        st.info("👋 Estás en **modo demo**. Los datos son de ejemplo. Explorá libremente.")

    # ── Qué hace la app ───────────────────────────────────────────────────────
    st.markdown("## ¿Qué hace esta app?")
    st.markdown("""
    **SDF BIOTEC** automatiza el costeo de importaciones para una empresa de insumos
    alimentarios. Reemplaza un proceso manual en Excel que tomaba horas por un flujo
    digital que tarda minutos.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background:#E8F5E9;border-radius:10px;padding:16px;height:130px;">
        <h3 style="color:#1B5E20;margin:0;">📋 Costeo</h3>
        <p style="font-size:13px;color:#2E7D32;margin-top:8px;">
        Calculá valor aduana, VEP, gastos locales
        y adelanto al despachante automáticamente.
        </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:#E3F2FD;border-radius:10px;padding:16px;height:130px;">
        <h3 style="color:#0D47A1;margin:0;">📁 Historial</h3>
        <p style="font-size:13px;color:#1565C0;margin-top:8px;">
        Registrá y consultá costeos anteriores.
        Filtrá, comparé y exportá a Excel.
        </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background:#FFF3E0;border-radius:10px;padding:16px;height:130px;">
        <h3 style="color:#E65100;margin:0;">🔍 VUCE en vivo</h3>
        <p style="font-size:13px;color:#BF360C;margin-top:8px;">
        Tributos actualizados desde la Ventanilla
        Única de Comercio Exterior en tiempo real.
        </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Demo interactivo VUCE ─────────────────────────────────────────────────
    st.markdown("## 🔍 Probá VUCE en vivo")
    st.markdown("""
    Ingresá una posición arancelaria (NCM) y la app consulta automáticamente
    los tributos de importación desde el gobierno argentino. Sin base de datos propia —
    datos frescos en cada consulta.
    """)

    # Ejemplos rápidos
    st.markdown("**Ejemplos rápidos:**")
    ejemplos = {
        "Alginato de Sodio": "3913.10.00.210P",
        "Transglutaminasa": "3507.90.42.000V",
        "Carragenina": "1302.39.10.000A",
        "Natamicina 50%": "3808.92.99.990M",
        "Agar": "1302.31.00.000V",
    }

    cols = st.columns(len(ejemplos))
    for col, (nombre, ncm) in zip(cols, ejemplos.items()):
        if col.button(nombre, key=f"ej_{ncm}", use_container_width=True):
            st.session_state["demo_ncm"] = ncm
            st.session_state["demo_nombre"] = nombre

    # Input libre
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        ncm_input = st.text_input(
            "O ingresá un NCM manualmente",
            placeholder="ej: 3913.10.00.210P",
            value=st.session_state.get("demo_ncm", ""),
            key="ncm_manual"
        )
    with col_btn:
        st.write("")
        st.write("")
        if st.button("🔎 Consultar", type="primary", use_container_width=True):
            if ncm_input.strip():
                st.session_state["demo_ncm"] = ncm_input.strip()
                st.session_state["demo_nombre"] = ncm_input.strip()

    # Ejecutar consulta
    ncm_a_consultar = st.session_state.get("demo_ncm")
    if ncm_a_consultar:
        st.markdown(f"### Resultado para `{ncm_a_consultar}`")

        # Paso 1: Auth
        with st.status("Consultando VUCE...", expanded=True) as status:
            st.write("🔐 Paso 1: Obteniendo token JWT de VUCE...")

            try:
                from modulos.vuce import consultar_tributos_ncm, _get_token
                token = _get_token()
                st.write(f"✅ Token obtenido: `{token[:40]}...`")

                st.write("🌐 Paso 2: Consultando posición arancelaria...")
                from modulos.vuce import consultar_posicion
                pos = consultar_posicion(ncm_a_consultar)
                if pos.get("error"):
                    st.error(f"Error: {pos['error']}")
                    status.update(label="Error al consultar", state="error")
                else:
                    st.write(f"✅ Posición encontrada: **{pos.get('descripcion', 'N/A')}**")

                    st.write("📊 Paso 3: Consultando tributos (IVA, Ganancias, TE...)...")
                    res = consultar_tributos_ncm(ncm_a_consultar)
                    st.write("✅ Tributos obtenidos desde HTML embebido en JSON")

                    status.update(label="✅ Consulta completada", state="complete")

                    # Mostrar resultado
                    st.markdown("#### Datos extraídos de VUCE")

                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("DIE", f"{pos.get('die_extrazona', '0')}%")
                    col2.metric("IVA", res.get("iva") or "21%")
                    col3.metric("IVA AD", res.get("iva_ad") or "20%")
                    col4.metric("Ganancias", res.get("ganancias") or "6%")
                    col5.metric("AEC", f"{pos.get('aec', '0')}%")

                    flags = []
                    if pos.get("dumping"): flags.append("⚠️ DUMPING")
                    if pos.get("bk"):      flags.append("🚫 Barrera")
                    if flags:
                        st.warning(" | ".join(flags))

                    # Mostrar el flujo técnico
                    with st.expander("🛠️ Ver cómo se hizo — código real"):
                        st.code(f"""
# 1. Obtener JWT dinámico
POST https://qa.ci.vuce.gob.ar/auth/generate
Body: {{"email": "vuce@vuce.gob.ar"}}
→ Token: {token[:50]}...

# 2. Consultar posición arancelaria
GET https://qa.ci.vuce.gob.ar/cice/posicionesPosicion
    ?posicion={ncm_a_consultar}&operacion=importacion&pais=156
Headers: x-api-key: <token>
→ Árbol anidado: navegar actual→hijo→actual→hijo hasta el NCM exacto

# 3. Consultar tributos por cluster
GET https://qa.ci.vuce.gob.ar/tributaciones/obtenerCluster
    ?posicion={ncm_a_consultar}&cluster=13  # IVA
    ?posicion={ncm_a_consultar}&cluster=14  # IVA Adicional
    ?posicion={ncm_a_consultar}&cluster=15  # Ganancias
    ?posicion={ncm_a_consultar}&cluster=36  # Tasa Estadística
→ HTML embebido en JSON → BeautifulSoup para extraer porcentajes
                        """, language="bash")

            except Exception as e:
                st.error(f"Error: {e}")
                status.update(label="Error", state="error")

    st.divider()

    # ── Stack técnico ─────────────────────────────────────────────────────────
    with st.expander("🗄️ Stack técnico"):
        st.markdown("""
        | Componente | Tecnología |
        |---|---|
        | Frontend | Streamlit |
        | Base de datos | SQLite (local) |
        | Scraping VUCE | requests + BeautifulSoup |
        | Exportación | openpyxl + fpdf2 |
        | Auth | streamlit-authenticator |
        | Lenguaje | Python 3.13 |
        """)

    st.divider()

    # ── Tour rápido ───────────────────────────────────────────────────────────
    st.markdown("## 🗺️ Tour rápido")
    st.markdown("""
    1. **Costeo** → seleccioná *Alginato de Sodio*, cargá 3000 KG a USD 9.00, flete USD 3200,
       Modal Marítimo → mirá cómo se calculan automáticamente los tributos con VUCE
    2. **Historial** → explorá los costeos de ejemplo DEMO-001 y DEMO-002
    3. Volvé a **Costeo** → hacé click en ✏️ Editar desde historial para ver el flujo completo
    """)

    if is_demo:
        st.success("👆 Usá el menú de la izquierda para navegar. ¡Explorá sin miedo!")

    st.divider()
    st.markdown("""
    <div style="text-align:center;color:#888;font-size:13px;">
    Desarrollado por <strong>Leandro Apodaca Alemán</strong> —
    <a href="https://linkedin.com/in/leandro-apodaca-aleman-848aa614b" target="_blank">LinkedIn</a> ·
    <a href="https://github.com/ahleandro12" target="_blank">GitHub</a>
    </div>
    """, unsafe_allow_html=True)
