"""
importador.py — Importacion masiva de operaciones desde Excel
"""
import pandas as pd
from io import BytesIO

# Mapeo puerto/origen -> bloque
ORIGEN_BLOQUE = {
    # MERCOSUR
    "brasil": "MERCOSUR", "são paulo": "MERCOSUR", "campinas": "MERCOSUR",
    "uruguaiana": "MERCOSUR", "montevideo": "MERCOSUR", "san josé uy": "MERCOSUR",
    "uruguay": "MERCOSUR", "paraguay": "MERCOSUR", "asuncion": "MERCOSUR",
    "venezuela": "MERCOSUR",
    # ALADI
    "santiago": "ALADI", "chile": "ALADI",
    "lima": "ALADI", "peru": "ALADI", "perú": "ALADI",
    "colombia": "ALADI", "bogota": "ALADI",
    "mexico": "ALADI", "méxico": "ALADI",
    "bolivia": "ALADI",
    "ecuador": "ALADI",
    "cuba": "ALADI",
    "panama": "ALADI", "panamá": "ALADI",
    # NO MERCOSUR (default)
    "qingdao": "NO MERCOSUR", "shanghai": "NO MERCOSUR", "xiamen": "NO MERCOSUR",
    "xingang": "NO MERCOSUR", "fujian": "NO MERCOSUR", "makassar": "NO MERCOSUR",
    "china": "NO MERCOSUR", "indonesia": "NO MERCOSUR",
    "frankfurt": "NO MERCOSUR", "hamburg": "NO MERCOSUR", "bremerhaven": "NO MERCOSUR",
    "barcelona": "NO MERCOSUR", "viena": "NO MERCOSUR", "austria": "NO MERCOSUR",
    "reino unido": "NO MERCOSUR", "uk": "NO MERCOSUR",
    "catania": "NO MERCOSUR", "italia": "NO MERCOSUR",
    "israel": "NO MERCOSUR",
    "india": "NO MERCOSUR",
    "japon": "NO MERCOSUR", "japón": "NO MERCOSUR",
}

def deducir_bloque(origen: str) -> str:
    if not origen:
        return "NO MERCOSUR"
    key = str(origen).strip().lower()
    for k, v in ORIGEN_BLOQUE.items():
        if k in key:
            return v
    return "NO MERCOSUR"

def leer_excel(file_bytes) -> pd.DataFrame:
    """Lee el Excel de operaciones y normaliza columnas."""
    df = pd.read_excel(BytesIO(file_bytes), dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df

def normalizar_filas(df: pd.DataFrame) -> list:
    """
    Convierte cada fila del Excel en un dict compatible con calculos.calcular_costeo.
    Retorna lista de dicts con los datos normalizados + campos editables.
    """
    filas = []
    for _, row in df.iterrows():
        def g(cols, default=""):
            for c in cols:
                v = row.get(c, "")
                if pd.notna(v) and str(v).strip() not in ("", "nan", "None"):
                    return str(v).strip()
            return default

        btc      = g(["Referencia", "BTC", "btc"])
        producto = g(["Producto (NCM)", "Producto", "producto"])
        proveedor= g(["Proveedor", "proveedor"])
        ncm      = g(["NCM", "ncm"])
        incoterm = g(["Incoterm", "incoterm"], "FOB").upper()
        origen   = g(["Puerto Origen", "Origen", "origen"]).strip()
        etd      = g(["ETD", "etd"])
        eta      = g(["ETA", "eta"])
        tt_dias  = g(["TT Días", "TT", "tt_dias"], "0")
        estado   = g(["Estado", "estado"], "Pendiente")

        try:
            cantidad_kg = float(str(g(["Cantidad (kg)", "Cantidad", "cantidad_kg"], "0")).replace(",", "."))
        except:
            cantidad_kg = 0.0

        try:
            precio_unit = float(str(g(["Precio Unit. (USD/kg)", "Precio Unit.", "precio_unit"], "0")).replace(",", "."))
        except:
            precio_unit = 0.0

        # Deducir bloque desde origen
        bloque = deducir_bloque(origen)

        # Saltar filas sin BTC o sin datos mínimos
        if not btc or btc.lower() in ("nan", "none", ""):
            continue

        filas.append({
            "btc":          btc,
            "producto":     producto,
            "proveedor":    proveedor,
            "ncm":          ncm,
            "incoterm":     incoterm,
            "origen":       origen,
            "bloque":       bloque,
            "co":           "NO",           # editable en preview
            "despachante":  "Mestre",       # editable en preview
            "cantidad_kg":  cantidad_kg,
            "precio_unit":  precio_unit,
            "etd":          etd,
            "eta":          eta,
            "tt_dias":      tt_dias,
            "estado":       estado,
            "flete":        0.0,
            "ajuste_incluir": 0.0,
            "ajuste_deducir": 0.0,
            "multa":        0.0,
        })

    return filas
