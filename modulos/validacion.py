import streamlit as st
import pandas as pd
from io import BytesIO
import db, parser_sim

def render():
    historial = db.get_historial()
    btcs = [r["btc"] for r in historial] if historial else []

    col1, col2 = st.columns([1,2])
    with col1:
        btc_sel = st.selectbox("BTC a validar", [""] + btcs)
        pdf_file = st.file_uploader("PDF del despacho", type=["pdf"])

    if not (pdf_file and btc_sel):
        return

    costeo = db.get_costeo_by_btc(btc_sel)
    if not costeo:
        st.error("BTC no encontrado.")
        return

    with st.spinner("Parseando PDF..."):
        datos_real = parser_sim.parsear_sim(BytesIO(pdf_file.read()))

    st.divider()
    st.subheader(f"Estimado vs Real — {btc_sel}")

    comparacion = [
        ("Valor en aduana", costeo["valor_aduana"],   datos_real.get("valor_aduana_real")),
        ("IVA",             costeo["iva"],             datos_real.get("iva_real")),
        ("IVA Adicional",   costeo["iva_ad"],          datos_real.get("iva_ad_real")),
        ("Ganancias",       costeo["ganancias"],       datos_real.get("ganancias_real")),
        ("Ing. Brutos",     costeo["ing_brutos"],      datos_real.get("ing_brutos_real")),
        ("T. Estadistica",  costeo["te"],              datos_real.get("te_real")),
        ("Total VEP",       costeo["total_vep_usd"],   datos_real.get("total_vep_real")),
    ]
    filas = []
    for nombre, est, real in comparacion:
        est = float(est or 0); real = float(real or 0)
        diff = real - est
        filas.append({"Concepto": nombre,
                      "Estimado": f"USD {est:,.2f}",
                      "Real (SIM)": f"USD {real:,.2f}" if real else "-",
                      "Diferencia": f"{'+' if diff>=0 else ''}{diff:,.2f}",
                      "Pct": f"{diff/est*100:+.1f}%" if est else "-"})
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    diff_vep = float(datos_real.get("total_vep_real") or 0) - float(costeo["total_vep_usd"])
    st.metric("Diferencia VEP", f"USD {diff_vep:+,.2f}")

    if datos_real.get("tc_real"):
        st.info(f"TC real del despacho: ${float(datos_real['tc_real']):,.3f} | TC estimado: ${float(costeo['tc']):,.0f}")

    if st.button("💾 Guardar validacion", type="primary"):
        db.save_validacion({
            "btc": btc_sel,
            "fob_real": datos_real.get("fob_real"),
            "valor_aduana_real": datos_real.get("valor_aduana_real"),
            "te_real": datos_real.get("te_real", 0),
            "iva_real": datos_real.get("iva_real", 0),
            "iva_ad_real": datos_real.get("iva_ad_real", 0),
            "ganancias_real": datos_real.get("ganancias_real", 0),
            "ing_brutos_real": datos_real.get("ing_brutos_real", 0),
            "arancel_sim_real": datos_real.get("arancel_sim_real", 10),
            "total_vep_real": datos_real.get("total_vep_real", 0),
            "tc_real": datos_real.get("tc_real"),
            "diff_valor_aduana": float(datos_real.get("valor_aduana_real") or 0) - float(costeo["valor_aduana"]),
            "diff_total_vep": diff_vep,
            "pdf_nombre": pdf_file.name,
        })
        st.success("Validacion guardada.")
