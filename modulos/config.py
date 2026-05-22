import streamlit as st
import db

BCRA_CODIGOS = {
    "USD": ["dolar", "usd"],
    "EUR": ["euro", "eur"],
    "GBP": ["libra", "gbp", "esterlina"],
}

def _fetch_bcra_cotizaciones():
    """Trae USD, EUR, GBP desde la API del BCRA. Devuelve dict {moneda: venta}."""
    import requests
    resultados = {}
    try:
        r = requests.get(
            "https://api.bcra.gob.ar/estadisticas/v3.0/cotizaciones",
            timeout=7,
            headers={"User-Agent": "SDF-BIOTEC/1.0"},
            verify=False
        )
        data = r.json()
        detalle = data.get("results", {}).get("detalle", [])
        for item in detalle:
            codigo = item.get("codigoMoneda", "").lower()
            descripcion = item.get("descripcion", "").lower()
            texto = codigo + " " + descripcion
            for moneda, claves in BCRA_CODIGOS.items():
                if moneda not in resultados:
                    if any(c in texto for c in claves):
                        venta = item.get("tipoCotizacion")
                        if venta and float(venta) > 0:
                            resultados[moneda] = float(venta)
    except Exception:
        pass

    # Fallback USD via dolarapi si BCRA no lo devolvio
    if "USD" not in resultados:
        try:
            import requests
            r2 = requests.get("https://dolarapi.com/v1/dolares/oficial", timeout=5)
            resultados["USD"] = float(r2.json()["venta"])
        except Exception:
            pass
    return resultados


def render():
    cfg = db.get_all_config()

    # ── Panel de cotizaciones ──────────────────────────────────
    st.markdown("#### Cotizaciones")
    col_usd, col_eur, col_gbp, col_btn = st.columns([2, 2, 2, 1])
    with col_usd:
        st.metric("USD → ARS", f"$ {float(cfg.get('tc', 1400)):,.0f}")
    with col_eur:
        st.metric("EUR → ARS", f"$ {float(cfg.get('tc_eur', 0) or 0):,.0f}")
    with col_gbp:
        st.metric("GBP → ARS", f"$ {float(cfg.get('tc_gbp', 0) or 0):,.0f}")
    with col_btn:
        st.write("")
        if st.button("🔄 Actualizar BCRA", use_container_width=True):
            with st.spinner("Consultando BCRA..."):
                cotizaciones = _fetch_bcra_cotizaciones()
            if cotizaciones:
                if "USD" in cotizaciones:
                    db.set_config("tc", cotizaciones["USD"])
                if "EUR" in cotizaciones:
                    db.set_config("tc_eur", cotizaciones["EUR"])
                if "GBP" in cotizaciones:
                    db.set_config("tc_gbp", cotizaciones["GBP"])
                msgs = [f"{k}: $ {v:,.0f}" for k, v in cotizaciones.items()]
                st.success("Actualizado — " + " | ".join(msgs))
                st.rerun()
            else:
                st.error("No se pudo obtener cotizaciones. Verificá conexión.")

    st.divider()

    with st.form("cfg"):
        st.markdown("#### Tipo de cambio y parámetros")
        col1, col2 = st.columns(2)
        with col1:
            tc        = st.number_input("TC USD→ARS", value=float(cfg.get("tc", 1400)), step=10.0)
            tc_eur    = st.number_input("TC EUR→ARS", value=float(cfg.get("tc_eur", 0) or 0), step=10.0)
            tc_gbp    = st.number_input("TC GBP→ARS", value=float(cfg.get("tc_gbp", 0) or 0), step=10.0)
            dias_forz = st.number_input("Días forzoso (buque)", value=int(cfg.get("dias_forzoso", 5)))
        with col2:
            arancel   = st.number_input("Arancel SIM (USD)", value=float(cfg.get("arancel_sim_usd", 10)))
            dist      = st.selectbox("Distancia habitual", [0, 30, 50, 70, 100],
                index=[0, 30, 50, 70, 100].index(int(cfg.get("distancia_km", 50))),
                format_func=lambda x: {0:"CABA",30:"GBA ≤30km",50:"GBA ≤50km",
                                        70:"GBA ≤70km",100:"Pilar/Pacheco"}[x])
            a_pct = st.number_input("Adduci % V.Aduana", value=float(cfg.get("adduci_pct", 0.01)), format="%.4f")
            a_min = st.number_input("Adduci mínimo USD",  value=float(cfg.get("adduci_min", 100)))

        col3, col4 = st.columns(2)
        with col3:
            m_pct = st.number_input("Mestre % V.Aduana", value=float(cfg.get("mestre_pct", 0.008)), format="%.4f")
        with col4:
            m_min = st.number_input("Mestre mínimo USD",  value=float(cfg.get("mestre_min", 160)))

        st.markdown("#### Forwarder")
        col1, col2 = st.columns(2)
        with col1:
            fwd_f = st.number_input("Flete forwarder (USD)", value=float(cfg.get("forwarder_flete", 500)))
        with col2:
            fwd_g = st.number_input("Gastos forwarder (USD)", value=float(cfg.get("forwarder_gastos", 150)))

        st.markdown("#### Gastos fijos")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            term  = st.number_input("Terminal (USD)",      value=float(cfg.get("terminal_usd", 800)))
            sen   = st.number_input("SENASA (ARS)",        value=float(cfg.get("senasa_ars", 11300)))
        with col2:
            senm  = st.number_input("SENASA Madera (USD)", value=float(cfg.get("senasa_madera_usd", 15)))
            inal  = st.number_input("INAL (ARS)",          value=float(cfg.get("inal_ars", 28300)))
        with col3:
            gop   = st.number_input("G.Operativos (ARS)",  value=float(cfg.get("gastos_op_ars", 85000)))
            anmat = st.number_input("VEP ANMAT (ARS)",     value=float(cfg.get("vep_anmat_ars", 102370)))
        with col4:
            gban  = st.number_input("G.Bancarios (USD)",   value=float(cfg.get("gastos_bancarios_usd", 95)))
            lak   = st.number_input("Lakaut (USD)",        value=float(cfg.get("lakaut_usd", 30)))

        if st.form_submit_button("💾 Guardar", type="primary"):
            for k, v in {
                "tc": tc, "tc_eur": tc_eur, "tc_gbp": tc_gbp,
                "dias_forzoso": dias_forz, "arancel_sim_usd": arancel,
                "distancia_km": dist, "adduci_pct": a_pct, "adduci_min": a_min,
                "mestre_pct": m_pct, "mestre_min": m_min,
                "forwarder_flete": fwd_f, "forwarder_gastos": fwd_g,
                "terminal_usd": term, "senasa_ars": sen,
                "senasa_madera_usd": senm, "inal_ars": inal,
                "gastos_op_ars": gop, "vep_anmat_ars": anmat,
                "gastos_bancarios_usd": gban, "lakaut_usd": lak,
            }.items():
                db.set_config(k, v)
            st.success("Guardado.")
            st.rerun()

    st.divider()

    # ── Matriz de costos histórica ──────────────────────────────
    st.markdown("#### 📊 Matriz de costos histórica")
    from modulos.predictor import importar_matriz, matriz_disponible, render_panel_historico

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        arch_matriz = st.file_uploader(
            "Importar matriz (.xlsx)", type=["xlsx"], key="upload_matriz",
            help="Columnas requeridas: Referencia, Producto, KG, Modal, etc."
        )
    with col_m2:
        st.write(""); st.write("")
        if arch_matriz and st.button("📥 Importar", type="primary", use_container_width=True):
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(arch_matriz.read())
                tmp_path = tmp.name
            with st.spinner("Importando..."):
                n = importar_matriz(tmp_path)
            os.unlink(tmp_path)
            st.success(f"✅ {n} embarques importados.")
            st.rerun()

    if matriz_disponible():
        render_panel_historico()
    else:
        st.info("Sin datos. Importá la matriz para habilitar el predictor de costos.")
