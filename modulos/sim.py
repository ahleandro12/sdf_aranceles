import streamlit as st
import pandas as pd
import db

def render():
    historial = db.get_historial()
    if not historial:
        st.info("No hay costeos guardados aun.")
        return

    btc_sel = st.selectbox("BTC", [r["btc"] for r in historial])
    costeo = db.get_costeo_by_btc(btc_sel)
    if not costeo:
        return

    st.subheader(f"{btc_sel} — {costeo['producto']}")
    st.caption(f"{costeo['ncm']} | {costeo['proveedor']}")

    tc = float(costeo["tc"])
    tributos = [
        ("I.V.A.",               "415", costeo["iva"]),
        ("IVA Adicional Inscr.", "422", costeo["iva_ad"]),
        ("Imp. a las Ganancias", "424", costeo["ganancias"]),
        ("Ing. Brutos BS.AS.",   "900", costeo["ing_brutos"]),
        ("Tasa de Estadistica",  "011", costeo["te"]),
        ("Arancel SIM Impo.",    "500", costeo["arancel_sim"]),
        ("Derecho Importacion",  "010", costeo["di"]),
    ]
    filas = [{"Concepto": n, "Codigo": cod,
              "USD": f"USD {float(v):,.2f}", "ARS": f"$ {float(v)*tc:,.0f}"}
             for n, cod, v in tributos if float(v or 0) > 0]
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total VEP (ARS)", f"$ {float(costeo['total_vep_ars']):,.0f}")
    with col2:
        st.metric("Total VEP (USD)", f"USD {float(costeo['total_vep_usd']):,.2f}")

    st.divider()
    st.markdown("**Pagos directos BIOTEC** (fuera del SIM)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("VEP ANMAT", f"$ {float(costeo['vep_anmat'])*tc:,.0f}")
    with col2:
        st.metric("INAL", f"$ {float(costeo['inal'])*tc:,.0f}")
    with col3:
        st.metric("Total", f"$ {(float(costeo['vep_anmat'])+float(costeo['inal']))*tc:,.0f}")
