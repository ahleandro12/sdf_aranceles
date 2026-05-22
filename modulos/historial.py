import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import db, exportar
from modulos.ui import vep_html, gastos_html, metricas

def render():
    historial = db.get_historial()
    if not historial:
        st.info("Sin registros aun.")
        return

    df = pd.DataFrame(historial)
    col1, col2, col3 = st.columns(3)
    with col1:
        fb = st.text_input("Filtrar BTC")
    with col2:
        fp = st.selectbox("Producto", ["Todos"] + sorted(df["producto"].dropna().unique().tolist()))
    with col3:
        fd = st.selectbox("Despachante", ["Todos","Mestre","Adduci"])

    if fb: df = df[df["btc"].str.contains(fb, case=False, na=False)]
    if fp != "Todos": df = df[df["producto"] == fp]
    if fd != "Todos": df = df[df["despachante"].str.upper() == fd.upper()]

    cols = ["fecha","btc","producto","proveedor","despachante",
            "valor_aduana","total_vep_usd","subtotal_gastos","precio_total","costo_kg"]
    df_show = df[cols].copy()
    df_show.columns = ["Fecha","BTC","Producto","Proveedor","Despachante",
                       "V.Aduana","VEP (USD)","Gastos (USD)","Total (USD)","Costo/KG"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)
    st.caption(f"{len(df_show)} registros")

    if st.button("📥 Exportar Excel"):
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_show.to_excel(w, index=False, sheet_name="Historial")
        st.download_button("⬇️ Descargar", buf.getvalue(),
            file_name=f"historial_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.divider()
    st.markdown("#### Detalle por BTC")
    btcs_filtrados = df["btc"].tolist()
    if not btcs_filtrados:
        return

    btc_det = st.selectbox("Seleccionar BTC", btcs_filtrados, key="hist_btc_sel")
    if not btc_det:
        return

    costeo = db.get_costeo_by_btc(btc_det)
    if not costeo:
        return

    tc = float(costeo["tc"])
    st.caption(f"{costeo['producto']} | {costeo['ncm']} | {costeo['proveedor']} | {costeo['despachante']} | {costeo['fecha']}")
    if costeo.get("notas"):
        st.info(f"📝 {costeo['notas']}")

    col_v, col_g = st.columns(2)
    with col_v:
        st.markdown(vep_html(costeo), unsafe_allow_html=True)
    with col_g:
        st.markdown(gastos_html(costeo, costeo.get("despachante","")), unsafe_allow_html=True)

    metricas(costeo)

    st.divider()
    xlsx = exportar.generar_excel(costeo)
    st.download_button("📊 Descargar Excel este costeo", data=xlsx,
        file_name=f"SDF_{btc_det}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("✏️ Editar este costeo", key=f"edit_{btc_det}"):
                st.session_state["btc"] = costeo["btc"]
                st.session_state["proveedor"] = costeo["proveedor"]
                st.session_state["despachante"] = costeo["despachante"]
                st.session_state["incoterm"] = costeo["incoterm"]
                st.session_state["origen_sel"] = costeo["origen"] if costeo["origen"] in ["Qingdao","Shanghai","Xiamen","Frankfurt","Hamburg","Barcelona","Reino Unido","Montevideo","Lima","Santiago","Makassar"] else "Otro"
                st.session_state["origen_libre"] = costeo["origen"]
                st.session_state["bloque"] = costeo["bloque"]
                st.session_state["co"] = costeo["co"]
                st.session_state["tc_input"] = float(costeo["tc"])
                st.session_state["flete"] = float(costeo["flete"] or 0)
                st.session_state["multa"] = float(costeo["multa"] or 0)
                # Cargar ETD/ETA
                from datetime import date
                def _parse_date(val):
                    if not val:
                        return None
                    try:
                        return date.fromisoformat(str(val)[:10])
                    except Exception:
                        return None
                st.session_state["etd"] = _parse_date(costeo.get("etd"))
                st.session_state["eta"] = _parse_date(costeo.get("eta"))
                # Cargar ítems desde costeo_items si existen, sino crear uno con el producto principal
                items_guardados = db.get_costeo_items(btc_det)
                if items_guardados:
                    st.session_state["btc_items"] = [
                        {"producto": it["producto"], "ncm": it["ncm"],
                         "cantidad_kg": float(it["cantidad_kg"]),
                         "precio_unit": float(it["precio_unit"]),
                         "die_pct": float(it.get("die",0)),
                         "te_pct": 0.03, "iva_pct": 0.21,
                         "iva_ad_ncm": "NO", "iva_ad_pct": 0.20,
                         "ganancias_ncm": "NO", "ganancias_pct": 0.06}
                        for it in items_guardados
                    ]
                else:
                    st.session_state["btc_items"] = [{
                        "producto": costeo["producto"],
                        "ncm": costeo["ncm"],
                        "cantidad_kg": float(costeo["cantidad_kg"]),
                        "precio_unit": float(costeo["precio_unit"]),
                        "die_pct": 0.0, "te_pct": 0.03, "iva_pct": 0.21,
                        "iva_ad_ncm": "NO", "iva_ad_pct": 0.20,
                        "ganancias_ncm": "NO", "ganancias_pct": 0.06,
                    }]
                st.session_state["modal"] = costeo.get("modal", "Maritimo")    
                st.session_state["_edit_loaded"] = True
                st.success("✅ Datos cargados. Andá a 📋 Costeo para editar.")
