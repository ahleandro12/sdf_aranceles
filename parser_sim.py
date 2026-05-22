import re
import pdfplumber
import pytesseract
from PIL import Image
from io import BytesIO

# Path a Tesseract en Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\leaapo\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

CONCEPTOS_MAP = {
    "010": "di",
    "011": "te",
    "415": "iva",
    "422": "iva_ad",
    "424": "ganancias",
    "500": "arancel_sim",
    "900": "ing_brutos",
}

def _es_digital(pdf_bytes) -> bool:
    """Detecta si el PDF tiene texto seleccionable o es imagen escaneada."""
    try:
        with pdfplumber.open(pdf_bytes) as pdf:
            text = pdf.pages[0].extract_text() or ""
            return len(text.strip()) > 50
    except:
        return False

def _extraer_texto_digital(pdf_bytes) -> str:
    with pdfplumber.open(pdf_bytes) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def _extraer_texto_ocr(pdf_bytes) -> str:
    """Convierte páginas del PDF a imagen y aplica OCR."""
    try:
        from pdf2image import convert_from_bytes
        imagenes = convert_from_bytes(pdf_bytes.read(), dpi=250)
        texto = ""
        for img in imagenes:
            texto += pytesseract.image_to_string(img, lang="spa") + "\n"
        return texto
    except Exception as e:
        return f"ERROR OCR: {e}"

def _extraer_tributos(text: str) -> dict:
    """Suma todas las apariciones de cada código tributario."""
    acumulados = {campo: 0.0 for campo in CONCEPTOS_MAP.values()}
    for linea in text.split('\n'):
        for codigo, campo in CONCEPTOS_MAP.items():
            pattern = rf'\(\s*0*{codigo}\s*\).*?([\d\.,]+)\s*$'
            m = re.search(pattern, linea, re.IGNORECASE)
            if m:
                valor = _parse_num(m.group(1))
                if valor > 0:
                    acumulados[campo] += valor
                break
    return acumulados

def parsear_sim(pdf_bytes) -> dict:
    resultado = {
        "btc": None,
        "fob_real": None,
        "valor_aduana_real": None,
        "tc_real": None,
        "di_real": 0.0,
        "te_real": 0.0,
        "iva_real": 0.0,
        "iva_ad_real": 0.0,
        "ganancias_real": 0.0,
        "ing_brutos_real": 0.0,
        "arancel_sim_real": 0.0,
        "total_vep_real": 0.0,
        "errores": [],
        "metodo": "",
    }

    # Leer bytes una sola vez
    if hasattr(pdf_bytes, 'read'):
        raw = pdf_bytes.read()
    else:
        raw = pdf_bytes

    # Detectar tipo y extraer texto
    digital = _es_digital(BytesIO(raw))
    if digital:
        text = _extraer_texto_digital(BytesIO(raw))
        resultado["metodo"] = "digital"
    else:
        text = _extraer_texto_ocr(BytesIO(raw))
        resultado["metodo"] = "ocr"

    if not text or len(text.strip()) < 20:
        resultado["errores"].append("No se pudo extraer texto del PDF.")
        return resultado

    # BTC
    btc_match = re.search(r'BTC[\s\-]?(\d{4})', text, re.IGNORECASE)
    if btc_match:
        resultado["btc"] = f"BTC-{btc_match.group(1)}"

    # FOB Total en Dólar — sumar todos los ítems
    fob_matches = re.findall(r'FOB\s+Total\s+en\s+D[oó]lar[^\d]*([\d\.,]+)', text, re.IGNORECASE)
    if fob_matches:
        resultado["fob_real"] = round(sum(_parse_num(v) for v in fob_matches), 2)

    # Valor en Aduana — sumar todos los ítems
    vad_matches = re.findall(r'Valor en Aduana en D[oó]lar[^\d]*([\d\.,]+)', text, re.IGNORECASE)
    if vad_matches:
        resultado["valor_aduana_real"] = round(sum(_parse_num(v) for v in vad_matches), 2)

    # TC
    cotiz_match = re.search(r'Cotiz\s*=\s*([\d\.,]+)', text, re.IGNORECASE)
    if cotiz_match:
        resultado["tc_real"] = _parse_num(cotiz_match.group(1))

    # Tributos acumulados
    acumulados = _extraer_tributos(text)
    for campo, valor in acumulados.items():
        resultado[f"{campo}_real"] = round(valor, 2)

    # Arancel SIM default si no se encontró
    if resultado["arancel_sim_real"] == 0:
        resultado["arancel_sim_real"] = 10.0

    resultado["total_vep_real"] = round(sum(
        resultado[f"{campo}_real"] for campo in CONCEPTOS_MAP.values()
    ), 2)

    return resultado


def _parse_num(s: str) -> float:
    try:
        s = s.strip().replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return float(s)
    except:
        return 0.0
