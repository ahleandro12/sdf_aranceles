"""Estilos y componentes compartidos."""
import streamlit as st

CSS = """
<style>
[data-testid="stSidebar"] { min-width:180 !important; max-width:180px !important; }
[data-testid="stSidebar"] .stRadio label { font-size:20px; padding:6px; }
[data-testid="stSidebar"] .stRadio { gap:2px; }
.section { background:var(--background-color); border:1px solid rgba(128,128,128,0.15);
           border-radius:10px; padding:14px 16px; margin-bottom:12px; }
.ncm-tag { display:inline-flex; gap:10px; background:#E8F5E9; color:#1B5E20;
           font-size:11px; padding:4px 12px; border-radius:20px; margin-bottom:8px; }
.calc-box { background:#E8F5E9; border:1px solid #A5D6A7; border-radius:8px; padding:10px 14px; }
.calc-row { display:flex; justify-content:space-between; font-size:13px; color:#2E7D32; padding:2px 0; }
.calc-total { font-weight:700; border-top:1px solid #A5D6A7; margin-top:5px; padding-top:6px; font-size:14px; }
.gasto-box { background:#E3F2FD; border:1px solid #90CAF9; border-radius:8px; padding:10px 14px; }
.gasto-row { display:flex; justify-content:space-between; font-size:13px; color:#1565C0; padding:2px 0; }
.gasto-biotec { color:#BF360C !important; font-style:italic; }
.gasto-total { font-weight:700; border-top:1px solid #90CAF9; margin-top:5px; padding-top:6px; font-size:14px; }
.highlight-green { background:#1B5E20; color:white; border-radius:8px; padding:8px 14px;
                   display:flex; justify-content:space-between; font-size:13px; font-weight:600; margin-top:6px; }
.highlight-blue { background:#0D47A1; color:white; border-radius:8px; padding:8px 14px;
                  display:flex; justify-content:space-between; font-size:13px; font-weight:600; margin-top:6px; }
.ref-box { background:#FFF8E1; border:1px solid #FFD54F; border-radius:8px; padding:10px 14px; margin-top:8px; }
.ref-title { font-size:11px; font-weight:600; color:#E65100; margin-bottom:6px; text-transform:uppercase; }
.ref-row { display:flex; justify-content:space-between; font-size:12px; color:#BF360C; padding:2px 0; }
</style>
"""

def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)

def vep_html(resultado):
    filas = [
        ("D. Importacion",   resultado["di"]),
        ("Tasa Estadistica", resultado["te"]),
        ("IVA",              resultado["iva"]),
        ("IVA Adicional",    resultado["iva_ad"]),
        ("Imp. Ganancias",   resultado["ganancias"]),
        ("Ing. Brutos",      resultado["ing_brutos"]),
        ("Arancel SIM",      resultado["arancel_sim"]),
        ("Multa",            resultado["multa"]),
    ]
    html = '<div class="calc-box">'
    for label, val in filas:
        if float(val or 0) > 0:
            html += f'<div class="calc-row"><span>{label}</span><span>USD {float(val):,.2f}</span></div>'
    html += f'<div class="calc-row calc-total"><span>Total VEP (USD)</span><span>USD {resultado["total_vep_usd"]:,.2f}</span></div>'
    html += '</div>'
    html += f'<div class="highlight-green"><span>Total VEP (ARS)</span><span>$ {resultado["total_vep_ars"]:,.0f}</span></div>'
    return html

def gastos_html(resultado, despachante=""):
    filas = [
        (f"Terminal/Almacen",        resultado["terminal"],         False),
        (f"Acarreo ({despachante})", resultado["acarreo"],          False),
        ("Custodia",                 resultado["custodia"],         False),
        ("SENASA",                   resultado["senasa"],           False),
        ("SENASA Madera",            resultado["senasa_madera"],    False),
        ("Gastos Operativos",        resultado["gastos_op"],        False),
        ("G. Bancarios",             resultado["gastos_bancarios"], False),
        ("Lakaut",                   resultado["lakaut"],           False),
        ("Honorarios Despachante",   resultado["honorarios"],       False),
        ("INAL — BIOTEC paga",       resultado["inal"],             True),
        ("VEP ANMAT — BIOTEC paga",  resultado["vep_anmat"],        True),
    ]
    html = '<div class="gasto-box">'
    for label, val, biotec in filas:
        if float(val or 0) > 0:
            cls = "gasto-row gasto-biotec" if biotec else "gasto-row"
            html += f'<div class="{cls}"><span>{label}</span><span>USD {float(val):,.2f}</span></div>'
    html += f'<div class="gasto-row gasto-total"><span>Subtotal gastos</span><span>USD {resultado["subtotal_gastos"]:,.2f}</span></div>'
    html += '</div>'
    html += f'<div class="highlight-blue"><span>Transferencia al despachante</span><span>USD {resultado["transferencia_despa"]:,.2f}</span></div>'
    return html

def metricas(resultado):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Base imponible", f"USD {float(resultado['base_imponible']):,.2f}")
        st.metric("Precio total",   f"USD {float(resultado['precio_total']):,.2f}")
    with col2:
        st.metric("Total VEP",  f"USD {float(resultado['total_vep_usd']):,.2f}")
        st.metric("Costo x KG", f"USD {float(resultado['costo_kg']):,.2f}")
