import streamlit as st
from datetime import datetime
import db, calculos, exportar
from modulos.ui import gastos_html, metricas

COLS_DB = [
    "btc","producto","ncm","proveedor","despachante","incoterm","origen","bloque","co",
    "tc","cantidad_kg","precio_unit","fob","flete","cfr","seguro","cif",
    "ajuste_incluir","ajuste_deducir","valor_aduana","di","te","base_imponible",
    "iva","iva_ad","ganancias","ing_brutos","arancel_sim","multa",
    "total_vep_usd","total_vep_ars","forwarder","terminal","acarreo","custodia",
    "senasa","senasa_madera","inal","gastos_op","honorarios","vep_anmat",
    "gastos_bancarios","lakaut","subtotal_gastos","transferencia_despa",
    "precio_total","costo_kg","etd","eta","modal"
]

DEFAULTS = {
    "modal": "Maritimo", "btc": "", "proveedor": "", "despachante": "Mestre",
    "incoterm": "FOB", "origen_sel": "Qingdao", "origen_libre": "",
    "bloque": "NO MERCOSUR", "co": "NO", "tc_input": 1400.0,
    "flete": 0.0, "distancia_km": 50, "multa": 0.0,
    "ajuste_incluir": 0.0, "ajuste_deducir": 0.0,
    "etd": "", "eta": "",
    "items": [],
}

def _init_state(tc):
    DEFAULTS["tc_input"] = tc
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "btc_items" not in st.session_state or not isinstance(st.session_state.btc_items, list):
        st.session_state.btc_items = []
    if st.session_state.get("_edit_loaded"):
        for key in ["tc_input", "flete", "multa", "btc", "proveedor", "origen_libre",
                    "ajuste_incluir", "ajuste_deducir", "modal", "despachante", "incoterm"]:
            if key in st.session_state:
                val = st.session_state[key]
                del st.session_state[key]
                st.session_state[key] = val
        for i, item in enumerate(st.session_state.btc_items):
            for k in [f"prod_{i}", f"kg_{i}", f"pu_{i}"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state[f"prod_{i}"] = item["producto"]
            st.session_state[f"kg_{i}"]   = float(item["cantidad_kg"])
            st.session_state[f"pu_{i}"]   = float(item["precio_unit"])
        st.session_state["_edit_loaded"] = False
        st.rerun()

def _item_vacio():
    return {"producto": "", "ncm": "", "cantidad_kg": 0.0, "precio_unit": 0.0,
            "die_pct": 0.0, "te_pct": 0.03, "iva_pct": 0.21,
            "iva_ad_ncm": "NO", "iva_ad_pct": 0.20,
            "ganancias_ncm": "NO", "ganancias_pct": 0.06}

def render():
    cfg = db.get_all_config()
    tc = float(cfg.get("tc", 1400))
    posiciones = db.get_posiciones()
    productos_unicos = [""] + list(dict.fromkeys([p["producto"] for p in posiciones]))
    pos_dict = {p["producto"]: p for p in posiciones}

    _init_state(tc)

    st.markdown("#### Datos generales")
    col1, col2, col3 = st.columns(3)
    with col1:
        btc = st.text_input("BTC", key="btc", placeholder="BTC-2574")
        proveedor = st.text_input("Proveedor", key="proveedor")
    with col2:
        despachante = st.selectbox("Despachante", ["Mestre","Adduci"], key="despachante")
        INCOTERMS = ["EXW","FCA","FAS","FOB","CFR","CPT","CIF","CIP","DAP","DPU","DDP"]
        INCOTERM_HELP = {
            "EXW":"Ex Works — flete 100% collect, sin seguro vendedor",
            "FCA":"Free Carrier — flete collect desde punto entrega",
            "FAS":"Free Alongside Ship — flete collect desde muelle origen",
            "FOB":"Free On Board — flete collect desde puerto origen",
            "CFR":"Cost & Freight — flete prepaid, seguro por cuenta comprador",
            "CPT":"Carriage Paid To — flete prepaid multimodal",
            "CIF":"Cost Insurance Freight — flete + seguro prepaid",
            "CIP":"Carriage & Insurance Paid — flete + seguro prepaid multimodal",
            "DAP":"Delivered At Place — flete prepaid, sin despacho importación",
            "DPU":"Delivered at Place Unloaded — flete prepaid + descarga",
            "DDP":"Delivered Duty Paid — flete prepaid + todos los costos",
        }
        incoterm = st.selectbox("Incoterm", INCOTERMS,
            index=INCOTERMS.index(st.session_state.get("incoterm","FOB"))
                  if st.session_state.get("incoterm","FOB") in INCOTERMS else 3,
            key="incoterm",
            help=INCOTERM_HELP.get(st.session_state.get("incoterm","FOB"), ""))
        st.caption(f"_{INCOTERM_HELP.get(incoterm,'')}_")
        origenes = ["Qingdao","Shanghai","Xiamen","Frankfurt","Hamburg",
                    "Barcelona","Reino Unido","Montevideo","Lima","Santiago","Makassar","Otro"]
        origen_sel = st.selectbox("Origen", origenes,
                                  index=origenes.index(st.session_state.origen_sel)
                                  if st.session_state.origen_sel in origenes else 0,
                                  key="origen_sel")
        origen = st.text_input("Especificar", key="origen_libre") if origen_sel == "Otro" else origen_sel
    with col3:
        bloque = st.selectbox("Bloque", ["NO MERCOSUR","MERCOSUR","ALADI"], key="bloque")
        co = st.selectbox("C.O.", ["NO","SI"], key="co")
        modal = st.selectbox("Modal", ["Maritimo","Aereo","Terrestre"], key="modal")
        tc_input = st.number_input("TC USD->ARS", step=10.0, key="tc_input")
        flete_total = st.number_input("Flete total (USD)", min_value=0.0, step=10.0, key="flete",
                                      help="Se distribuye proporcionalmente entre ítems por FOB")

    col_etd, col_eta, col_aj1, col_aj2 = st.columns(4)
    with col_etd:
        etd = st.date_input("ETD (salida)", value=None, key="etd",
                            help="Estimated Time of Departure")
    with col_eta:
        eta = st.date_input("ETA (arribo)", value=None, key="eta",
                            help="Estimated Time of Arrival")
    with col_aj1:
        ajuste_inc = st.number_input("Ajuste incluir (USD)", min_value=0.0, step=10.0,
                                     key="ajuste_incluir",
                                     help="Monto a sumar al valor CIF para V.Aduana")
    with col_aj2:
        ajuste_ded = st.number_input("Ajuste deducir (USD)", min_value=0.0, step=10.0,
                                     key="ajuste_deducir",
                                     help="Monto a restar del valor CIF para V.Aduana")

    st.divider()
    st.markdown("#### Ítems del despacho")

    if not st.session_state.btc_items:
        st.session_state.btc_items = [_item_vacio()]

    items_result = []
    to_delete = None

    for i, item in enumerate(st.session_state.btc_items):
        with st.container():
            col_title, col_del = st.columns([10, 1])
            with col_title:
                st.markdown(f"**Ítem {i+1}**")
            with col_del:
                if st.button("✕", key=f"del_{i}", help="Eliminar ítem") and len(st.session_state.btc_items) > 1:
                    to_delete = i

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                prod = st.selectbox("Producto", productos_unicos,
                    index=productos_unicos.index(item["producto"]) if item["producto"] in productos_unicos else 0,
                    key=f"prod_{i}")
            with col2:
                kg = st.number_input("KG", min_value=0.0, step=100.0,
                    value=float(item["cantidad_kg"]), key=f"kg_{i}")
            with col3:
                pu = st.number_input("Precio unit (USD)", min_value=0.0, step=0.01,
                    value=float(item["precio_unit"]), key=f"pu_{i}")
            with col4:
                fob_item = round(kg * pu, 2)
                st.metric("FOB ítem", f"USD {fob_item:,.2f}")

            pos = pos_dict.get(prod, {})
            ncm = pos.get("ncm", item.get("ncm",""))
            die_pct = pos.get("die", item.get("die_pct",0))
            te_pct = pos.get("te", item.get("te_pct",0.03))
            iva_pct = pos.get("iva", item.get("iva_pct",0.21))
            iva_ad_ncm = pos.get("iva_ad", item.get("iva_ad_ncm","NO"))
            iva_ad_pct = pos.get("iva_ad_pct", item.get("iva_ad_pct",0.20))
            ganancias_ncm = pos.get("ganancias", item.get("ganancias_ncm","NO"))
            ganancias_pct = pos.get("ganancias_pct", item.get("ganancias_pct",0.06))

            if ncm:
                from modulos.vuce import consultar_tributos_ncm, render_vuce_badge
                res_vuce = consultar_tributos_ncm(ncm)
                st.markdown(render_vuce_badge(res_vuce), unsafe_allow_html=True)
                from modulos.predictor import render_predictor_badge
                render_predictor_badge(prod, kg, modal)

            st.session_state.btc_items[i] = {
                "producto": prod, "ncm": ncm,
                "cantidad_kg": kg, "precio_unit": pu,
                "die_pct": die_pct, "te_pct": te_pct, "iva_pct": iva_pct,
                "iva_ad_ncm": iva_ad_ncm, "iva_ad_pct": iva_ad_pct,
                "ganancias_ncm": ganancias_ncm, "ganancias_pct": ganancias_pct,
            }

            if kg > 0 and pu > 0:
                fob_total_all = sum(
                    it.get("cantidad_kg",0) * it.get("precio_unit",0)
                    for it in st.session_state.btc_items
                )
                flete_prop = round(fob_item / fob_total_all * flete_total, 2) if fob_total_all > 0 else 0
                res_item = calculos.calcular_item(
                    {**st.session_state.btc_items[i], "flete_proporcional": flete_prop},
                    bloque, co, tc_input
                )
                items_result.append(res_item)

            st.markdown("---")

    if to_delete is not None:
        st.session_state.btc_items.pop(to_delete)
        st.rerun()

    if st.button("➕ Agregar ítem", use_container_width=False):
        st.session_state.btc_items.append(_item_vacio())
        st.rerun()

    if items_result and all(r["fob"] > 0 for r in items_result):
        st.divider()
        st.markdown("#### Resumen VEP por ítem")

        col_headers = st.columns([3,2,2,2,2,2,2])
        headers = ["Producto","FOB","V.Aduana","IVA","IVA AD","Ganancias","VEP Total"]
        for col, h in zip(col_headers, headers):
            col.markdown(f"**{h}**")

        for r in items_result:
            cols = st.columns([3,2,2,2,2,2,2])
            cols[0].write(r["producto"][:20])
            cols[1].write(f"USD {r['fob']:,.0f}")
            cols[2].write(f"USD {r['valor_aduana']:,.0f}")
            cols[3].write(f"USD {r['iva']:,.0f}")
            cols[4].write(f"USD {r['iva_ad']:,.0f}")
            cols[5].write(f"USD {r['ganancias']:,.0f}")
            cols[6].write(f"USD {r['total_vep_usd']:,.0f}")

        total_fob = sum(r["fob"] for r in items_result)
        total_va = sum(r["valor_aduana"] for r in items_result)
        total_iva = sum(r["iva"] for r in items_result)
        total_iva_ad = sum(r["iva_ad"] for r in items_result)
        total_gan = sum(r["ganancias"] for r in items_result)
        total_ib = sum(r["ing_brutos"] for r in items_result)
        total_di = sum(r["di"] for r in items_result)
        total_te = sum(r["te"] for r in items_result)
        total_vep_items = sum(r["total_vep_usd"] for r in items_result)
        total_kg = sum(r["cantidad_kg"] for r in items_result)

        arancel_sim = float(db.get_config("arancel_sim_usd", 10))
        multa = float(st.session_state.get("multa", 0))
        total_vep = round(total_vep_items + arancel_sim + multa, 2)
        total_vep_ars = round(total_vep * tc_input, 2)

        st.markdown(
            f'<div style="background:#1B5E20;color:white;border-radius:8px;padding:8px 14px;'
            f'display:flex;justify-content:space-between;margin-top:8px;">'
            f'<span>Total VEP (USD)</span><span>USD {total_vep:,.2f}</span></div>'
            f'<div style="background:#0D47A1;color:white;border-radius:8px;padding:8px 14px;'
            f'display:flex;justify-content:space-between;margin-top:4px;">'
            f'<span>Total VEP (ARS)</span><span>$ {total_vep_ars:,.0f}</span></div>',
            unsafe_allow_html=True)

        st.divider()
        dist_opts = [0,30,50,70,100]
        distancia_km = st.selectbox("Distancia acarreo", dist_opts,
            index=dist_opts.index(st.session_state.distancia_km) if st.session_state.distancia_km in dist_opts else 2,
            format_func=lambda x:{0:"CABA",30:"GBA <=30km",50:"GBA <=50km",70:"GBA <=70km",100:"Pilar/Pacheco"}[x],
            key="distancia_km")

        item_principal = max(items_result, key=lambda x: x["fob"])
        resultado_total = calculos.calcular_costeo({
            "btc": btc, "producto": " + ".join([r["producto"] for r in items_result]),
            "ncm": item_principal["ncm"],
            "proveedor": proveedor, "despachante": despachante,
            "incoterm": incoterm, "origen": origen,
            "bloque": bloque, "co": co, "tc": tc_input,
            "cantidad_kg": total_kg,
            "precio_unit": round(total_fob / total_kg, 4) if total_kg else 0,
            "flete": flete_total,
            "ajuste_incluir": ajuste_inc, "ajuste_deducir": ajuste_ded,
            "die_pct": total_di / total_va if total_va else 0,
            "te_pct": total_te / total_va if total_va else 0,
            "iva_pct": total_iva / (total_va + total_di + total_te) if (total_va + total_di + total_te) else 0.21,
            "iva_ad_ncm": "SI" if total_iva_ad > 0 else "NO",
            "iva_ad_pct": total_iva_ad / (total_va + total_di + total_te) if total_iva_ad > 0 and (total_va + total_di + total_te) else 0.20,
            "ganancias_ncm": "SI" if total_gan > 0 else "NO",
            "ganancias_pct": total_gan / (total_va + total_di + total_te) if total_gan > 0 and (total_va + total_di + total_te) else 0.06,
            "distancia_km": distancia_km, "multa": multa, "modal": modal,
        })

        resultado_total["di"] = total_di
        resultado_total["te"] = total_te
        resultado_total["iva"] = total_iva
        resultado_total["iva_ad"] = total_iva_ad
        resultado_total["ganancias"] = total_gan
        resultado_total["ing_brutos"] = total_ib
        resultado_total["total_vep_usd"] = total_vep
        resultado_total["total_vep_ars"] = total_vep_ars
        resultado_total["valor_aduana"] = total_va
        resultado_total["precio_total"] = round(total_va + total_vep + resultado_total["subtotal_gastos"], 2)
        resultado_total["costo_kg"] = round(resultado_total["precio_total"] / total_kg, 4) if total_kg else 0

        col_g = st.columns([1,1])
        with col_g[0]:
            st.markdown("**Gastos locales**")
            from modulos.ui import gastos_html
            st.markdown(gastos_html(resultado_total, despachante), unsafe_allow_html=True)
        with col_g[1]:
            metricas(resultado_total)

        st.divider()
        col_b1, col_b2, col_b3, col_b4 = st.columns([2,1,1,1])
        with col_b1:
            notas = st.text_input("Notas (opcional)")
        with col_b2:
            guardar = st.button("💾 Guardar", type="primary", use_container_width=True)
        with col_b3:
            exportar_btn = st.button("📊 Excel", use_container_width=True)
        with col_b4:
            limpiar = st.button("🗑️ Limpiar", use_container_width=True)

        if guardar:
            if not btc:
                st.error("Ingresa el BTC.")
            else:
                data = {k: resultado_total.get(k, 0) for k in COLS_DB}
                data["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                data["notas"] = notas
                data["etd"] = str(etd) if etd else ""
                data["eta"] = str(eta) if eta else ""
                data["modal"] = modal
                data["producto"] = " + ".join([r["producto"] for r in items_result])
                try:
                    db.save_costeo(data)
                    db.save_costeo_items(btc, items_result)
                    st.success(f"✅ {btc} guardado con {len(items_result)} ítems.")
                except Exception as e:
                    st.error(f"Error: {e}")

        if exportar_btn:
            resultado_total["notas"] = notas
            xlsx = exportar.generar_excel(resultado_total)
            st.download_button("⬇️ Excel", data=xlsx,
                file_name=f"SDF_{btc or 'borrador'}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if limpiar:
            for k in DEFAULTS:
                st.session_state[k] = DEFAULTS[k]
            st.session_state.btc_items = [_item_vacio()]
            st.rerun()
