from db import get_config, get_tarifas_acarreo

def _get_predictor():
    """Import lazy para evitar circular imports."""
    try:
        from modulos.predictor import calcular_terminal_aereo, estimar_deposito
        return calcular_terminal_aereo, estimar_deposito
    except Exception:
        return None, None

def calcular_acarreo(despachante: str, kg: float, distancia_km: int, tc: float) -> float:
    """Calcula el acarreo en USD según despachante, kg y distancia."""
    tarifas = get_tarifas_acarreo(despachante)
    if not tarifas:
        return 0.0

    # Encontrar fila correcta (límite inferior)
    fila = tarifas[0]
    for t in tarifas:
        if kg >= t["hasta_kg"]:
            fila = t
        else:
            break

    dist = int(distancia_km)
    if dist == 0:
        ars = fila["caba"]
    elif dist == 30:
        ars = fila["gba_30"]
    elif dist == 50:
        ars = fila["gba_50"]
    elif dist == 70:
        ars = fila.get("gba_70") or fila["gba_50"]
    else:
        ars = fila.get("gba_100") or fila.get("pilar") or fila["gba_50"]

    return round(ars / tc, 2) if tc else 0.0

def calcular_item(item: dict, bloque: str, co: str, tc: float) -> dict:
    """
    Calcula tributos para un ítem individual de un costeo multi-producto.
    """
    kg = float(item.get("cantidad_kg", 0))
    precio_unit = float(item.get("precio_unit", 0))
    flete_prop = float(item.get("flete_proporcional", 0))
    ajuste_inc = float(item.get("ajuste_incluir", 0))
    ajuste_ded = float(item.get("ajuste_deducir", 0))

    die_pct       = float(item.get("die_pct", 0))
    te_pct        = float(item.get("te_pct", 0.03))
    iva_pct       = float(item.get("iva_pct", 0.21))
    iva_ad_ncm    = item.get("iva_ad_ncm", "NO").upper()
    iva_ad_pct    = float(item.get("iva_ad_pct", 0.20))
    ganancias_ncm = item.get("ganancias_ncm", "NO").upper()
    ganancias_pct = float(item.get("ganancias_pct", 0.06))

    bloque = bloque.upper()
    co = co.upper()
    exento = bloque == "MERCOSUR" or (bloque == "ALADI" and co == "SI")

    fob = round(kg * precio_unit, 2)
    seguro = round((fob + flete_prop) * 0.005, 2)
    cif = round(fob + flete_prop + seguro, 2)
    valor_aduana = round(cif + ajuste_inc - ajuste_ded, 2)

    di         = 0.0 if exento else round(valor_aduana * die_pct, 2)
    te         = 0.0 if exento else round(valor_aduana * te_pct, 2)
    base_imp   = round(valor_aduana + di + te, 2)
    iva        = round(base_imp * iva_pct, 2)
    iva_ad     = round(base_imp * iva_ad_pct, 2) if iva_ad_ncm == "SI" and not exento else 0.0
    ganancias  = round(base_imp * ganancias_pct, 2) if ganancias_ncm == "SI" and not exento else 0.0
    ing_brutos = round(base_imp * 0.0122, 2)
    total_vep  = round(di + te + iva + iva_ad + ganancias + ing_brutos, 2)

    return {
        "producto":       item.get("producto", ""),
        "ncm":            item.get("ncm", ""),
        "cantidad_kg":    kg,
        "precio_unit":    precio_unit,
        "fob":            fob,
        "flete_prop":     flete_prop,
        "cif":            cif,
        "valor_aduana":   valor_aduana,
        "di":             di,
        "te":             te,
        "base_imponible": base_imp,
        "iva":            iva,
        "iva_ad":         iva_ad,
        "ganancias":      ganancias,
        "ing_brutos":     ing_brutos,
        "total_vep_usd":  total_vep,
    }
def calcular_costeo(datos: dict) -> dict:
    """
    Recibe todos los inputs y devuelve el costeo completo.
    datos esperados:
        btc, producto, ncm, proveedor, despachante, incoterm, origen, bloque, co,
        tc, cantidad_kg, precio_unit, flete, ajuste_incluir, ajuste_deducir,
        die_pct, te_pct, iva_pct, iva_ad_ncm, ganancias_ncm,
        distancia_km
    """
    tc = float(datos.get("tc", 0)) or 1400
    kg = float(datos.get("cantidad_kg", 0))
    precio_unit = float(datos.get("precio_unit", 0))
    flete = float(datos.get("flete", 0))
    ajuste_inc = float(datos.get("ajuste_incluir", 0))
    ajuste_ded = float(datos.get("ajuste_deducir", 0))
    bloque = datos.get("bloque", "NO MERCOSUR").upper()
    co = datos.get("co", "NO").upper()
    incoterm = datos.get("incoterm", "FOB").upper()
    despachante = datos.get("despachante", "MESTRE").upper()
    distancia_km = int(datos.get("distancia_km", 50))

    die_pct = float(datos.get("die_pct", 0))
    te_pct = float(datos.get("te_pct", 0.03))
    iva_pct = float(datos.get("iva_pct", 0.21))
    iva_ad_ncm = datos.get("iva_ad_ncm", "NO").upper()
    ganancias_ncm = datos.get("ganancias_ncm", "NO").upper()
    iva_ad_pct = float(datos.get("iva_ad_pct", 0.20))
    ganancias_pct = float(datos.get("ganancias_pct", 0.06))

    # B · Valor mercadería
    fob = round(kg * precio_unit, 2)

    flete_collect = 0.0
    flete_prepaid = 0.0
    if incoterm in ("CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"):
        flete_prepaid = flete
    else:
        flete_collect = flete

    cfr = round(fob + flete_prepaid + flete_collect, 2)
    seguro = round(cfr * 0.005, 2)
    cif = round(cfr + seguro, 2)
    valor_aduana = round(cif + ajuste_inc - ajuste_ded, 2)

    # C · Tributos — exención MERCOSUR / ALADI+CO
    exento = bloque == "MERCOSUR" or (bloque == "ALADI" and co == "SI")

    di = 0.0 if exento else round(valor_aduana * die_pct, 2)
    te = 0.0 if exento else round(valor_aduana * te_pct, 2)
    base_imp = round(valor_aduana + di + te, 2)
    iva = round(base_imp * iva_pct, 2)
    iva_ad = round(base_imp * iva_ad_pct, 2) if iva_ad_ncm == "SI" and not exento else 0.0
    ganancias = round(base_imp * ganancias_pct, 2) if ganancias_ncm == "SI" and not exento else 0.0
    ing_brutos = round(base_imp * 0.0122, 2)
    arancel_sim = float(get_config("arancel_sim_usd", 10))
    multa = float(datos.get("multa", 0))

    total_vep = round(iva + iva_ad + ganancias + ing_brutos + di + te + arancel_sim + multa, 2)
    total_vep_ars = round(total_vep * tc, 2)

    # D · Gastos locales
    # Forwarder: estimado del predictor histórico (solo referencia, se carga manual en flete)
    forwarder = float(get_config("forwarder_flete", 500)) + float(get_config("forwarder_gastos", 150))

    # Terminal/depósito fiscal: TCA para aéreo, predictor para marítimo/terrestre
    _modal = datos.get("modal", "Maritimo")
    _producto = datos.get("producto", "")
    _calc_tca, _estimar_dep = _get_predictor()
    if _modal == "Aereo" and _calc_tca:
        terminal = _calc_tca(kg)
    elif _modal in ("Maritimo", "Terrestre") and _estimar_dep:
        terminal_pred = _estimar_dep(_producto, kg, _modal)
        terminal = terminal_pred if terminal_pred else float(get_config("terminal_usd", 800))
    else:
        terminal = float(get_config("terminal_usd", 800))
    acarreo = calcular_acarreo(despachante, kg, distancia_km, tc)
    custodia = float(get_config("custodia_ars", 0)) / tc
    senasa = float(get_config("senasa_ars", 11300)) / tc
    senasa_madera = float(get_config("senasa_madera_usd", 15))
    inal = float(get_config("inal_ars", 28300)) / tc
    gastos_op = float(get_config("gastos_op_ars", 85000)) / tc
    gastos_bancarios = float(get_config("gastos_bancarios_usd", 95))
    lakaut = float(get_config("lakaut_usd", 30))
    vep_anmat = float(get_config("vep_anmat_ars", 102370)) / tc

    # Honorarios: max(valor_aduana * pct, minimo)
    if despachante == "ADDUCI":
        hon_pct = float(get_config("adduci_pct", 0.01))
        hon_min = float(get_config("adduci_min", 100))
    else:
        hon_pct = float(get_config("mestre_pct", 0.008))
        hon_min = float(get_config("mestre_min", 160))
    honorarios = round(max(valor_aduana * hon_pct, hon_min), 2)

    subtotal_gastos = round(
        forwarder + terminal + acarreo + custodia + senasa +
        senasa_madera + inal + gastos_op + honorarios +
        vep_anmat + gastos_bancarios + lakaut, 2
    )

    # Adelanto al despachante (dia del despacho):
    # VEP + Terminal + Acarreo + SENASA + SENASA Madera + Gastos Op + Lakaut
    # NO incluye: Forwarder (BIOTEC paga aparte), Honorarios (45 dias), G.Bancarios, INAL, VEP ANMAT
    transferencia_despa = round(
        total_vep + terminal + acarreo + senasa +
        senasa_madera + gastos_op + lakaut, 2
    )

    precio_total = round(base_imp + total_vep + subtotal_gastos, 2)
    costo_kg = round(precio_total / kg, 4) if kg else 0.0

    return {
        # inputs
        "btc": datos.get("btc", ""),
        "producto": datos.get("producto", ""),
        "ncm": datos.get("ncm", ""),
        "proveedor": datos.get("proveedor", ""),
        "despachante": datos.get("despachante", ""),
        "incoterm": incoterm,
        "origen": datos.get("origen", ""),
        "bloque": bloque,
        "co": co,
        "tc": tc,
        "cantidad_kg": kg,
        "precio_unit": precio_unit,
        # mercadería
        "fob": fob,
        "flete": flete,
        "cfr": cfr,
        "seguro": seguro,
        "cif": cif,
        "ajuste_incluir": ajuste_inc,
        "ajuste_deducir": ajuste_ded,
        "valor_aduana": valor_aduana,
        # tributos
        "di": di,
        "te": te,
        "base_imponible": base_imp,
        "iva": iva,
        "iva_ad": iva_ad,
        "ganancias": ganancias,
        "ing_brutos": ing_brutos,
        "arancel_sim": arancel_sim,
        "multa": multa,
        "total_vep_usd": total_vep,
        "total_vep_ars": total_vep_ars,
        # gastos
        "forwarder": forwarder,
        "terminal": terminal,
        "acarreo": acarreo,
        "custodia": custodia,
        "senasa": senasa,
        "senasa_madera": senasa_madera,
        "inal": inal,
        "gastos_op": gastos_op,
        "honorarios": honorarios,
        "vep_anmat": vep_anmat,
        "gastos_bancarios": gastos_bancarios,
        "lakaut": lakaut,
        "subtotal_gastos": subtotal_gastos,
        "transferencia_despa": transferencia_despa,
        # totales
        "precio_total": precio_total,
        "costo_kg": costo_kg,
        # pagos directos BIOTEC
        "pagos_directos_biotec": round((inal + vep_anmat) * tc, 2),
    }
