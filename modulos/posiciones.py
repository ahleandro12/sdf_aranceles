import streamlit as st
from datetime import datetime
import db
from modulos.vuce import consultar_tributos_ncm

# ── Helpers ──────────────────────────────────────────────────────────────────

def _pct(val, decimals=1):
    try:
        return f"{float(val or 0)*100:.{decimals}f}%"
    except:
        return "—"

def _parse_pct(val_str: str | None) -> float | None:
    """Convierte '21%' o '21' a 0.21. Devuelve None si no puede."""
    if not val_str:
        return None
    try:
        return float(str(val_str).replace("%","").replace(",",".").strip()) / 100
    except:
        return None

def _diff_label(campo, viejo, nuevo) -> str:
    if viejo == nuevo:
        return f"✅ {campo}: {viejo} (sin cambio)"
    return f"⚠️ **{campo}**: ~~{viejo}~~ → **{nuevo}**"


# ── Buscador VUCE ─────────────────────────────────────────────────────────────

def _render_buscador_vuce():
    st.markdown("#### 🔍 Buscar NCM en VUCE")
    st.caption("Consultá tributos actualizados directamente desde la Ventanilla Única de Comercio Exterior.")

    col1, col2 = st.columns([3, 1])
    with col1:
        ncm_input = st.text_input("NCM", placeholder="ej: 3507.90.42.000V", key="vuce_ncm_input")
    with col2:
        pais_opts = {"China (156)": 156, "Brasil (076)": 76, "USA (840)": 840, "Alemania (276)": 276}
        pais_label = st.selectbox("País origen", list(pais_opts.keys()), key="vuce_pais")
        pais = pais_opts[pais_label]

    if st.button("🔎 Consultar VUCE", type="primary", key="btn_consultar_vuce"):
        if not ncm_input.strip():
            st.warning("Ingresá un NCM.")
            return
        with st.spinner("Consultando VUCE..."):
            res = consultar_tributos_ncm(ncm_input.strip(), pais)
        st.session_state["vuce_resultado"] = res
        st.session_state["vuce_ncm"] = ncm_input.strip()

    res = st.session_state.get("vuce_resultado")
    if not res:
        return

    if res.get("error"):
        st.error(f"Error VUCE: {res['error']}")
        return

    # ── Mostrar resultado ──
    st.divider()
    st.markdown(f"**{res['ncm']}**")
    if res.get("descripcion"):
        st.caption(res["descripcion"])

    # Parsear valores de VUCE
    iva_pct      = _parse_pct(res.get("iva"))      or 0.21
    iva_ad_pct   = _parse_pct(res.get("iva_ad"))   or 0.20
    gan_pct      = _parse_pct(res.get("ganancias")) or 0.06
    die_pct      = float(res.get("die_extrazona") or 0) / 100
    aec_pct      = float(res.get("aec") or 0) / 100

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("DIE",      f"{die_pct*100:.1f}%")
    col2.metric("IVA",      f"{iva_pct*100:.0f}%")
    col3.metric("IVA AD",   f"{iva_ad_pct*100:.0f}%")
    col4.metric("Ganancias",f"{gan_pct*100:.1f}%")
    col5.metric("AEC",      f"{aec_pct*100:.1f}%")

    flags = []
    if res.get("dumping"): flags.append("⚠️ DUMPING")
    if res.get("bk"):      flags.append("🚫 BK")
    if res.get("la"):      flags.append("📋 LIC.AUTO")
    if flags:
        st.warning("  |  ".join(flags))

    st.divider()

    # ── Verificar si ya existe en posiciones ──
    existente = db.get_posicion_by_ncm(res["ncm"])

    datos_vuce = {
        "die":          die_pct,
        "iva":          iva_pct,
        "iva_ad_pct":   iva_ad_pct,
        "ganancias_pct": gan_pct,
        "aec":          aec_pct,
        "dumping":      res.get("dumping", False),
        "la":           res.get("la", False),
    }

    if existente:
        # ── Mostrar diff ──
        st.markdown(f"**Ya tenés este NCM** como `{existente['producto']}`")
        if existente.get("vuce_consultado_at"):
            st.caption(f"Última consulta VUCE: {existente['vuce_consultado_at']}")

        diffs = []
        comparaciones = [
            ("DIE",       _pct(existente.get("die")),         f"{die_pct*100:.1f}%"),
            ("IVA",       _pct(existente.get("iva")),         f"{iva_pct*100:.0f}%"),
            ("IVA AD %",  _pct(existente.get("iva_ad_pct")),  f"{iva_ad_pct*100:.0f}%"),
            ("Ganancias", _pct(existente.get("ganancias_pct")),f"{gan_pct*100:.1f}%"),
            ("AEC",       _pct(existente.get("aec", 0)),      f"{aec_pct*100:.1f}%"),
        ]
        hay_cambios = False
        for campo, viejo, nuevo in comparaciones:
            if viejo != nuevo:
                hay_cambios = True
            diffs.append(_diff_label(campo, viejo, nuevo))

        for d in diffs:
            st.markdown(d)

        if not hay_cambios:
            st.success("✅ Los valores coinciden con VUCE. No hay cambios.")
        else:
            st.warning("Hay diferencias. ¿Actualizás con los valores de VUCE?")
            if st.button("✅ Actualizar con datos VUCE", key="btn_actualizar_vuce"):
                db.upsert_posicion_vuce(existente["producto"], res["ncm"], datos_vuce)
                st.success(f"✅ `{existente['producto']}` actualizado con datos de VUCE.")
                st.session_state["vuce_resultado"] = None
                st.rerun()

    else:
        # ── NCM nuevo — pedir nombre de producto ──
        st.info("Este NCM no está en tus posiciones. Podés agregarlo.")
        nombre = st.text_input("Nombre del producto", placeholder="ej: TRANSGLUTAMINASA", key="vuce_nombre_prod")
        if st.button("➕ Agregar a mis posiciones", key="btn_agregar_vuce"):
            if not nombre.strip():
                st.warning("Ingresá un nombre para el producto.")
            else:
                db.upsert_posicion_vuce(nombre.strip().upper(), res["ncm"], datos_vuce)
                st.success(f"✅ `{nombre.upper()}` agregado con datos de VUCE.")
                st.session_state["vuce_resultado"] = None
                st.rerun()


# ── Render principal ──────────────────────────────────────────────────────────

def render():
    st.caption("Verificá y editá los parámetros arancelarios de cada producto.")

    st.markdown("""<style>
    .pos-card{background:var(--background-color);border:1px solid rgba(128,128,128,0.2);border-radius:10px;padding:12px 14px;margin-bottom:8px;}
    .pos-name{font-size:13px;font-weight:600;margin-bottom:3px;}
    .pos-ncm{font-size:10px;font-family:monospace;color:gray;margin-bottom:8px;}
    .pos-updated{font-size:9px;color:#aaa;margin-bottom:6px;}
    .pos-tags{display:flex;gap:4px;flex-wrap:wrap;}
    .tag{font-size:10px;padding:2px 7px;border-radius:20px;font-weight:500;}
    .tag-die{background:#E3F2FD;color:#0C447C;}
    .tag-iva{background:#E8F5E9;color:#1B5E20;}
    .tag-ad{background:#FFF8E1;color:#854F0B;}
    .tag-gan{background:#FCE4EC;color:#880E4F;}
    .tag-no{background:#F5F5F5;color:#9E9E9E;}
    .tag-vuce{background:#EDE7F6;color:#4527A0;}
    </style>""", unsafe_allow_html=True)

    # ── Buscador VUCE ──
    _render_buscador_vuce()

    st.divider()

    # ── Mis posiciones ──
    st.markdown("#### Mis posiciones")
    posiciones = db.get_posiciones()
    filtro = st.text_input("Buscar", placeholder="ej: alginato, 3913...", key="filtro_pos")

    if filtro:
        posiciones = [p for p in posiciones if filtro.lower() in p["producto"].lower() or filtro.lower() in p["ncm"].lower()]

    cols = st.columns(4)
    for i, pos in enumerate(posiciones):
        with cols[i % 4]:
            die_tag = f'<span class="tag tag-die">DIE {float(pos["die"])*100:.0f}%</span>'
            iva_tag = f'<span class="tag tag-iva">IVA {float(pos["iva"])*100:.0f}%</span>'
            ad_tag  = (f'<span class="tag tag-ad">IVA AD {float(pos.get("iva_ad_pct",0.20))*100:.0f}%</span>'
                      if pos["iva_ad"]=="SI" else '<span class="tag tag-no">IVA AD NO</span>')
            gan_tag = ('<span class="tag tag-gan">Gan SI</span>'
                      if pos["ganancias"]=="SI" else '<span class="tag tag-no">Gan NO</span>')
            vuce_tag = (f'<span class="tag tag-vuce">VUCE {pos["vuce_consultado_at"][:10]}</span>'
                       if pos.get("vuce_consultado_at") else '')
            st.markdown(
                f'<div class="pos-card">'
                f'<div class="pos-name">{pos["producto"].title()}</div>'
                f'<div class="pos-ncm">{pos["ncm"]}</div>'
                f'<div class="pos-tags">{die_tag}{iva_tag}{ad_tag}{gan_tag}{vuce_tag}</div>'
                f'</div>',
                unsafe_allow_html=True)

    st.divider()

    # ── Editar manual ──
    st.markdown("#### Editar manual")
    prod_sel = st.selectbox("Producto", [p["producto"] for p in db.get_posiciones()], key="sel_prod_edit")
    pos = db.get_posicion_by_producto(prod_sel)

    if pos:
        with st.form("form_pos"):
            col1, col2 = st.columns(2)
            with col1:
                ncm_e       = st.text_input("NCM", value=pos["ncm"])
                die_e       = st.number_input("DIE %", value=float(pos["die"])*100, step=0.1, format="%.2f")
                te_e        = st.number_input("TE %", value=float(pos["te"])*100, step=0.1, format="%.2f")
                iva_e       = st.number_input("IVA %", value=float(pos["iva"])*100, step=0.5, format="%.2f")
            with col2:
                iva_ad_e    = st.selectbox("IVA Adicional", ["NO","SI"], index=1 if pos["iva_ad"]=="SI" else 0)
                iva_ad_pct_e= st.number_input("IVA AD %", value=float(pos.get("iva_ad_pct",0.20))*100, step=0.5, format="%.2f")
                gan_e       = st.selectbox("Ganancias", ["NO","SI"], index=1 if pos["ganancias"]=="SI" else 0)
                gan_pct_e   = st.number_input("Ganancias %", value=float(pos.get("ganancias_pct",0.06))*100, step=0.5, format="%.2f")

            if st.form_submit_button("Guardar cambios", type="primary"):
                conn = db.get_conn()
                conn.execute("""UPDATE posiciones SET
                    ncm=?,die=?,te=?,iva=?,iva_ad=?,iva_ad_pct=?,ganancias=?,ganancias_pct=?
                    WHERE producto=?""",
                    (ncm_e, die_e/100, te_e/100, iva_e/100,
                     iva_ad_e, iva_ad_pct_e/100, gan_e, gan_pct_e/100, prod_sel))
                conn.commit(); conn.close()
                st.success(f"{prod_sel} actualizado.")
                st.rerun()

    with st.expander("+ Agregar nueva posición manual"):
        with st.form("form_nueva"):
            col1, col2 = st.columns(2)
            with col1:
                n_prod      = st.text_input("Producto")
                n_ncm       = st.text_input("NCM")
                n_die       = st.number_input("DIE %", value=0.0, step=0.1, format="%.2f")
                n_te        = st.number_input("TE %", value=3.0, step=0.1, format="%.2f")
                n_iva       = st.number_input("IVA %", value=21.0, step=0.5, format="%.2f")
            with col2:
                n_iva_ad    = st.selectbox("IVA Adicional", ["NO","SI"], key="n_iva_ad")
                n_iva_ad_pct= st.number_input("IVA AD %", value=20.0, step=0.5, format="%.2f")
                n_gan       = st.selectbox("Ganancias", ["NO","SI"], key="n_gan")
                n_gan_pct   = st.number_input("Ganancias %", value=6.0, step=0.5, format="%.2f")
            if st.form_submit_button("Agregar", type="primary"):
                if n_prod and n_ncm:
                    conn = db.get_conn()
                    conn.execute("""INSERT OR IGNORE INTO posiciones
                        (producto,ncm,die,te,iva,iva_ad,iva_ad_pct,ganancias,ganancias_pct)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                        (n_prod, n_ncm, n_die/100, n_te/100, n_iva/100,
                         n_iva_ad, n_iva_ad_pct/100, n_gan, n_gan_pct/100))
                    conn.commit(); conn.close()
                    st.success(f"{n_prod} agregado.")
                    st.rerun()
                else:
                    st.error("Completá producto y NCM.")
