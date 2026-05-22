"""
vuce.py — Consulta CIVUCE por NCM
Extrae tributos de importación desde la API de VUCE (qa.ci.vuce.gob.ar)
Uso: from modulos.vuce import consultar_tributos_ncm, render_vuce_badge
"""

import re
import requests
from bs4 import BeautifulSoup

_BASE  = "https://qa.ci.vuce.gob.ar"
_EMAIL = "vuce@vuce.gob.ar"
_token_cache = {"token": None}


# ── Auth ─────────────────────────────────────────────────────────────────────

def _get_token() -> str:
    if _token_cache["token"]:
        return _token_cache["token"]
    r = requests.post(f"{_BASE}/auth/generate", json={"email": _EMAIL}, timeout=10)
    r.raise_for_status()
    data = r.json()
    token = data.get("token") or data.get("data")
    if not token or not isinstance(token, str):
        raise ValueError(f"Token inesperado: {data}")
    _token_cache["token"] = token
    return token


def _headers() -> dict:
    return {"x-api-key": _get_token()}


# ── Parseo HTML ───────────────────────────────────────────────────────────────

def _extraer_valor_html(html: str) -> str | None:
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "html.parser")
        for td in soup.find_all("td"):
            texto = td.get_text(strip=True)
            match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", texto)
            if match:
                return match.group(0).replace(",", ".")
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", soup.get_text())
        if match:
            return match.group(0).replace(",", ".")
    except Exception:
        pass
    return None


# ── Árbol anidado ─────────────────────────────────────────────────────────────

def _hoja_arbol(data: dict) -> dict:
    nodo = data.get("actual", {})
    while "hijo" in nodo and isinstance(nodo["hijo"], dict):
        nodo = nodo["hijo"].get("actual", nodo["hijo"])
    return nodo


# ── Consultas ─────────────────────────────────────────────────────────────────

def consultar_posicion(ncm: str, pais: int = 156) -> dict:
    try:
        r = requests.get(
            f"{_BASE}/cice/posicionesPosicion",
            params={"posicion": ncm, "operacion": "importacion", "pais": pais},
            headers=_headers(),
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        hoja = _hoja_arbol(data.get("data", {}))
        return {
            "posicion":      hoja.get("posicion"),
            "descripcion":   hoja.get("descripcion"),
            "die_extrazona": hoja.get("derechos_importacion_extrazona"),
            "die_intrazona": hoja.get("derechos_importacion_intrazona"),
            "aec":           hoja.get("arancel_externo_comun"),
            "dumping":       bool(hoja.get("dumping", 0)),
            "bk":            bool(hoja.get("bk", 0)),
            "la":            bool(hoja.get("la", 0)),
            "error":         None,
        }
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            _token_cache["token"] = None
            return consultar_posicion(ncm, pais)
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def consultar_cluster(ncm: str, cluster: int) -> str | None:
    try:
        r = requests.get(
            f"{_BASE}/tributaciones/obtenerCluster",
            params={"posicion": ncm, "operacion": "I", "cluster": cluster},
            headers=_headers(),
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        resumenes = data.get("data", {}).get("resumen", [])
        for item in resumenes:
            valor = _extraer_valor_html(item.get("resumen", ""))
            if valor:
                return valor
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            _token_cache["token"] = None
            return consultar_cluster(ncm, cluster)
    except Exception:
        pass
    return None


def consultar_tributos_ncm(ncm: str, pais: int = 156) -> dict:
    resultado = {
        "ncm":           ncm,
        "descripcion":   None,
        "die_extrazona": None,
        "die_intrazona": None,
        "aec":           None,
        "dumping":       False,
        "bk":            False,
        "la":            False,
        "iibb":          None,
        "iva":           None,
        "iva_ad":        None,
        "ganancias":     None,
        "te":            None,
        "error":         None,
    }

    pos = consultar_posicion(ncm, pais)
    if pos.get("error"):
        resultado["error"] = pos["error"]
        return resultado
    resultado.update({k: pos[k] for k in pos if k in resultado})

    cluster_map = {
        "iibb":      12,
        "iva":       13,
        "iva_ad":    14,
        "ganancias": 15,
        "te":        36,
    }
    for campo, cluster_id in cluster_map.items():
        resultado[campo] = consultar_cluster(ncm, cluster_id)

    return resultado


# ── Renderizado ───────────────────────────────────────────────────────────────

def render_vuce_badge(res: dict) -> str:
    if res.get("error"):
        return f'<span style="color:#888;font-size:11px;">VUCE: {res["error"]}</span>'

    items = []
    if res.get("die_extrazona") is not None:
        items.append(("DIE", f'{res["die_extrazona"]}%', "#1565C0"))
    if res.get("aec") is not None:
        items.append(("AEC", f'{res["aec"]}%', "#1565C0"))

    tributos = [
        ("IVA",       res.get("iva"),       "#0D47A1"),
        ("IVA AD",    res.get("iva_ad"),    "#E65100"),
        ("Ganancias", res.get("ganancias"), "#4A148C"),
        ("TE",        res.get("te"),        "#1B5E20"),
        ("IIBB",      res.get("iibb"),      "#37474F"),
    ]
    for nombre, valor, color in tributos:
        if valor:
            items.append((nombre, valor, color))

    alertas = []
    if res.get("dumping"):
        alertas.append(("⚠️ DUMPING", "#B71C1C"))
    if res.get("bk"):
        alertas.append(("🚫 BK", "#B71C1C"))

    badges = []
    for nombre, valor, color in items:
        badges.append(
            f'<span style="background:{color};color:white;font-size:11px;'
            f'padding:3px 8px;border-radius:20px;margin:2px;display:inline-block;">'
            f'{nombre} {valor}</span>'
        )
    for nombre, color in alertas:
        badges.append(
            f'<span style="background:{color};color:white;font-size:11px;'
            f'padding:3px 8px;border-radius:20px;margin:2px;display:inline-block;">'
            f'{nombre}</span>'
        )

    if not badges:
        return '<span style="color:#888;font-size:11px;">VUCE: sin datos</span>'

    from datetime import date
    hoy = date.today().strftime("%d/%m/%Y")
    return (
        '<div style="margin-top:4px;margin-bottom:6px;">'
        + " ".join(badges)
        + f'<span style="font-size:9px;color:#888;margin-left:8px;">Info VUCE · {hoy}</span>'
        + "</div>"
    )
