"""
predictor.py — Predictor de costos de importación basado en matriz histórica
"""

import pandas as pd
import streamlit as st
import db

# ── Tabla TCA depósito fiscal aéreo ──────────────────────────────────────────

TCA_TABLA = [
    (0,     5,     52.31),
    (5,     10,    71.14),
    (10,    20,    103.14),
    (20,    50,    149.93),
    (50,    100,   205.82),
    (100,   200,   279.50),
    (200,   350,   381.16),
    (350,   500,   526.48),
    (500,   750,   622.56),
    (750,   1000,  750.60),
    (1000,  1500,  880.22),
    (1500,  2000,  1019.95),
    (2000,  2500,  1155.66),
    (2500,  3000,  1359.42),
    (3000,  4000,  1577.46),
    (4000,  5000,  1916.92),
    (5000,  7000,  2279.29),
    (7000,  10000, 2742.22),
    (10000, None,  3258.56),
]

def calcular_terminal_aereo(kg: float) -> float:
    """Calcula el depósito fiscal TCA para embarques aéreos según KG."""
    for desde, hasta, precio in TCA_TABLA:
        if hasta is None or kg <= hasta:
            return precio
    return TCA_TABLA[-1][2]


# ── Importar matriz ───────────────────────────────────────────────────────────

def importar_matriz(xlsx_path: str) -> int:
    df = pd.read_excel(xlsx_path)
    df.columns = [
        'btc', 'producto', 'kg', 'precio_unit', 'valor_factura',
        'honorarios', 'comis_banco', 'lakaut', 'deposito_fiscal_kg',
        'gastos_despa', 'forwarder_kg', 'anmat', 'gastos_impo',
        'transporte_kg', 'seguridad', 'otro', 'mercaderia_transito',
        'total', 'costo_final_unit', 'modal'
    ]
    df = df[df['btc'].notna() & df['btc'].astype(str).str.startswith('BTC')]
    conn = db.get_conn()
    conn.execute("DROP TABLE IF EXISTS matriz_costos")
    conn.execute("""
        CREATE TABLE matriz_costos (
            btc TEXT, producto TEXT, kg REAL, precio_unit REAL,
            valor_factura REAL, honorarios REAL, comis_banco REAL,
            lakaut REAL, deposito_fiscal_kg REAL, gastos_despa REAL,
            forwarder_kg REAL, anmat REAL, gastos_impo REAL,
            transporte_kg REAL, seguridad REAL, otro REAL,
            mercaderia_transito REAL, total REAL, costo_final_unit REAL,
            modal TEXT
        )
    """)
    df.to_sql('matriz_costos', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()
    return len(df)


def matriz_disponible() -> bool:
    try:
        conn = db.get_conn()
        count = conn.execute("SELECT COUNT(*) FROM matriz_costos").fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


# ── Predicción ────────────────────────────────────────────────────────────────

def predecir_costos(producto: str, kg: float, modal: str) -> dict | None:
    if not matriz_disponible():
        return None

    conn = db.get_conn()

    # Match exacto por producto + modal
    rows = conn.execute(
        "SELECT * FROM matriz_costos WHERE UPPER(producto) = UPPER(?) AND modal = ? AND kg > 0",
        (producto, modal)
    ).fetchall()

    # Fallback: producto exacto sin importar modal (con advertencia)
    if not rows:
        rows = conn.execute(
            "SELECT * FROM matriz_costos WHERE UPPER(producto) = UPPER(?) AND kg > 0",
            (producto,)
        ).fetchall()

    # Fallback por palabra clave + modal
    if not rows:
        for palabra in [p for p in producto.upper().split() if len(p) > 3]:
            rows = conn.execute(
                "SELECT * FROM matriz_costos WHERE UPPER(producto) LIKE ? AND modal = ? AND kg > 0",
                (f"%{palabra}%", modal)
            ).fetchall()
            if rows:
                break

    # Fallback general por modal
    if not rows:
        rows = conn.execute(
            "SELECT * FROM matriz_costos WHERE modal = ? AND kg > 0 AND forwarder_kg IS NOT NULL",
            (modal,)
        ).fetchall()

    conn.close()
    if not rows:
        return None

    cols = [
        'btc', 'producto', 'kg', 'precio_unit', 'valor_factura',
        'honorarios', 'comis_banco', 'lakaut', 'deposito_fiscal_kg',
        'gastos_despa', 'forwarder_kg', 'anmat', 'gastos_impo',
        'transporte_kg', 'seguridad', 'otro', 'mercaderia_transito',
        'total', 'costo_final_unit', 'modal'
    ]
    df = pd.DataFrame(rows, columns=cols)

    def _rango(col):
        vals = df[col].dropna()
        vals = vals[vals > 0]
        if vals.empty:
            return None
        return {"min": round(vals.min(),2), "avg": round(vals.mean(),2),
                "max": round(vals.max(),2), "count": len(vals)}

    # Calcular ratios por KG para depósito y forwarder
    def _ratio(col):
        """Promedio de (valor/kg) por embarque individual."""
        mask = (df[col].notna()) & (df[col] > 0) & (df['kg'] > 0)
        if not mask.any():
            return None
        ratios = df.loc[mask, col] / df.loc[mask, 'kg']
        return {"min": round(ratios.min(),4), "avg": round(ratios.mean(),4),
                "max": round(ratios.max(),4), "count": len(ratios)}

    muestra_chica = len(df) < 2
    modal_ref = df['modal'].mode()[0] if not df['modal'].empty else modal
    modal_mixto = df['modal'].nunique() > 1

    return {
        "fuente":        "exacto" if producto.upper() in df['producto'].str.upper().values else "modal",
        "modal":         modal,
        "modal_ref":     modal_ref,
        "modal_mixto":   modal_mixto,
        "muestra_chica": muestra_chica,
        "embarques":     len(df),
        "productos_ref": df['producto'].unique().tolist()[:5],
        "kg_referencia": round(df['kg'].mean(), 0),
        "forwarder":     _ratio('forwarder_kg'),
        "deposito":      _ratio('deposito_fiscal_kg'),
        "transporte":    _ratio('transporte_kg'),
        "honorarios":    _rango('honorarios'),
        "gastos_despa":  _rango('gastos_despa'),
        "anmat":         _rango('anmat'),
        "gastos_impo":   _rango('gastos_impo'),
        "costo_unit_avg": round(df['costo_final_unit'].dropna().mean(), 2) if not df['costo_final_unit'].dropna().empty else None,
    }


def estimar_deposito(producto: str, kg: float, modal: str) -> float | None:
    """
    Estima el depósito fiscal:
    - Aéreo: tabla TCA fija
    - Marítimo/Terrestre: (deposito_histórico / kg_histórico) × kg_nuevo
    """
    if modal == "Aereo":
        return calcular_terminal_aereo(kg)

    pred = predecir_costos(producto, kg, modal)
    if not pred or not pred.get("deposito"):
        return None

    dep = pred["deposito"]
    # dep["avg"] ya es ratio por KG (valor/kg por embarque)
    return round(dep["avg"] * kg, 2)


def estimar_forwarder(producto: str, kg: float, modal: str) -> float | None:
    """
    Estima el flete del forwarder:
    (forwarder_histórico / kg_histórico) × kg_nuevo
    """
    pred = predecir_costos(producto, kg, modal)
    if not pred or not pred.get("forwarder"):
        return None

    fwd = pred["forwarder"]
    return round(fwd["avg"] * kg, 2)


# ── Badge flete estimado ──────────────────────────────────────────────────────

def render_predictor_badge(producto: str, kg: float, modal: str):
    """Muestra estimación de flete en el formulario de costeo."""
    if not matriz_disponible() or not producto or kg <= 0:
        return

    pred = predecir_costos(producto, kg, modal)
    if not pred or not pred.get("forwarder"):
        return

    fwd = pred["forwarder"]
    flete_estimado = round(float(fwd["avg"]) * kg, 0)
    flete_min = round(float(fwd["min"]) * kg, 0)
    flete_max = round(float(fwd["max"]) * kg, 0)
    fuente = pred.get("modal_ref", modal)
    n = pred["embarques"]

    advertencias = []
    if pred.get("muestra_chica"):
        advertencias.append("⚠️ muestra chica")
    if pred.get("modal_mixto"):
        advertencias.append("⚠️ modales mixtos")
    adv_txt = " · ".join(advertencias)
    color_bg = "#FFF3E0" if advertencias else "#E8EAF6"
    color_txt = "#E65100" if advertencias else "#3949AB"
    color_sub = "#BF360C" if advertencias else "#7986CB"

    st.markdown(
        f'<div style="background:{color_bg};border-radius:8px;padding:6px 12px;margin:4px 0;display:inline-block;">'
        f'<span style="font-size:11px;color:{color_txt};font-weight:600;">✈️ Flete estimado: '
        f'USD {int(flete_estimado):,}</span>'
        f'<span style="font-size:10px;color:{color_sub};"> (rango {int(flete_min):,}–{int(flete_max):,} · '
        f'{n} ref {fuente}{" · " + adv_txt if adv_txt else ""})</span>'
        f'</div>',
        unsafe_allow_html=True
    )


# ── Panel histórico ───────────────────────────────────────────────────────────

def render_panel_historico():
    if not matriz_disponible():
        st.warning("No hay datos de matriz cargados.")
        return

    conn = db.get_conn()
    df = pd.read_sql("SELECT * FROM matriz_costos WHERE kg > 0", conn)
    conn.close()

    st.markdown(f"**{len(df)} embarques** en la matriz histórica")
    col1, col2, col3 = st.columns(3)
    col1.metric("Marítimos",  len(df[df['modal']=='Maritimo']))
    col2.metric("Aéreos",     len(df[df['modal']=='Aereo']))
    col3.metric("Terrestres", len(df[df['modal']=='Terrestre']))

    modal_sel = st.selectbox("Filtrar por modal", ["Todos","Maritimo","Aereo","Terrestre"], key="hist_modal")
    prod_sel  = st.text_input("Buscar producto", key="hist_prod")

    df_show = df.copy()
    if modal_sel != "Todos":
        df_show = df_show[df_show['modal'] == modal_sel]
    if prod_sel:
        df_show = df_show[df_show['producto'].str.contains(prod_sel, case=False, na=False)]

    df_show = df_show[['btc','producto','kg','modal','forwarder_kg','honorarios',
                        'deposito_fiscal_kg','transporte_kg','gastos_impo','costo_final_unit']].rename(columns={
        'btc':'BTC','producto':'Producto','kg':'KG','modal':'Modal',
        'forwarder_kg':'Fwd Total','honorarios':'Honorarios',
        'deposito_fiscal_kg':'Depósito','transporte_kg':'Transporte',
        'gastos_impo':'Gastos Impo.','costo_final_unit':'Costo/Un'
    })
    st.dataframe(df_show, use_container_width=True, hide_index=True)
