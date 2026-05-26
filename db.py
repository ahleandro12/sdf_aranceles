import sqlite3
from pathlib import Path

import os as _os
DB_PATH = Path(_os.environ.get("SDF_DB_PATH", str(Path(__file__).parent / "data" / "biotec.db")))

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    CREATE TABLE IF NOT EXISTS posiciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT UNIQUE,
        ncm TEXT,
        die REAL DEFAULT 0,
        te REAL DEFAULT 0.03,
        iva REAL DEFAULT 0.21,
        iva_ad TEXT DEFAULT 'NO',
        iva_ad_pct REAL DEFAULT 0.20,
        ganancias TEXT DEFAULT 'NO',
        ganancias_pct REAL DEFAULT 0.06,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS tarifas_acarreo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        despachante TEXT,
        tipo TEXT,
        hasta_kg REAL,
        caba REAL,
        gba_30 REAL,
        gba_50 REAL,
        gba_70 REAL,
        gba_100 REAL,
        pilar REAL,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS costeos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        btc TEXT UNIQUE,
        fecha TEXT,
        producto TEXT,
        ncm TEXT,
        proveedor TEXT,
        despachante TEXT,
        incoterm TEXT,
        origen TEXT,
        bloque TEXT,
        co TEXT,
        tc REAL,
        cantidad_kg REAL,
        precio_unit REAL,
        fob REAL,
        flete REAL DEFAULT 0,
        cfr REAL,
        seguro REAL,
        cif REAL,
        ajuste_incluir REAL DEFAULT 0,
        ajuste_deducir REAL DEFAULT 0,
        valor_aduana REAL,
        di REAL DEFAULT 0,
        te REAL DEFAULT 0,
        base_imponible REAL,
        iva REAL,
        iva_ad REAL,
        ganancias REAL,
        ing_brutos REAL,
        arancel_sim REAL DEFAULT 10,
        multa REAL DEFAULT 0,
        total_vep_usd REAL,
        total_vep_ars REAL,
        forwarder REAL DEFAULT 0,
        terminal REAL DEFAULT 0,
        acarreo REAL DEFAULT 0,
        custodia REAL DEFAULT 0,
        senasa REAL DEFAULT 0,
        senasa_madera REAL DEFAULT 0,
        inal REAL DEFAULT 0,
        gastos_op REAL DEFAULT 0,
        honorarios REAL DEFAULT 0,
        vep_anmat REAL DEFAULT 0,
        gastos_bancarios REAL DEFAULT 0,
        lakaut REAL DEFAULT 0,
        subtotal_gastos REAL,
        transferencia_despa REAL,
        precio_total REAL,
        costo_kg REAL,
        notas TEXT DEFAULT '',
        etd TEXT DEFAULT '',
        eta TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS costeo_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        btc TEXT,
        item_num INTEGER,
        producto TEXT,
        ncm TEXT,
        cantidad_kg REAL,
        precio_unit REAL,
        fob REAL,
        valor_aduana REAL,
        die REAL DEFAULT 0,
        te REAL DEFAULT 0,
        base_imponible REAL,
        iva REAL DEFAULT 0,
        iva_ad REAL DEFAULT 0,
        ganancias REAL DEFAULT 0,
        ing_brutos REAL DEFAULT 0,
        total_vep_usd REAL DEFAULT 0,
        FOREIGN KEY (btc) REFERENCES costeos(btc)
    );
    CREATE TABLE IF NOT EXISTS validaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        btc TEXT,
        fecha_validacion TEXT DEFAULT (datetime('now')),
        fob_real REAL,
        valor_aduana_real REAL,
        te_real REAL,
        iva_real REAL,
        iva_ad_real REAL,
        ganancias_real REAL,
        ing_brutos_real REAL,
        arancel_sim_real REAL DEFAULT 10,
        total_vep_real REAL,
        tc_real REAL,
        diff_valor_aduana REAL,
        diff_total_vep REAL,
        pdf_nombre TEXT,
        FOREIGN KEY (btc) REFERENCES costeos(btc)
    );
    CREATE TABLE IF NOT EXISTS arancel (
        ncm TEXT PRIMARY KEY,
        descripcion TEXT,
        die REAL DEFAULT 0,
        re REAL DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    """)

    defaults = {
        "tc": "1400", "dias_forzoso": "5",
        "adduci_pct": "0.01", "adduci_min": "100",
        "mestre_pct": "0.008", "mestre_min": "160",
        "forwarder_flete": "500", "forwarder_gastos": "150",
        "terminal_usd": "800", "custodia_ars": "0",
        "senasa_ars": "11300", "senasa_madera_usd": "15",
        "inal_ars": "28300", "gastos_op_ars": "85000",
        "vep_anmat_ars": "102370", "gastos_bancarios_usd": "95",
        "lakaut_usd": "30", "arancel_sim_usd": "10", "distancia_km": "50",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (k, v))

    posiciones_default = [
        ("ALGINATO DE SODIO",        "3913.10.00.210P", 0,     0.03, 0.21, "SI", "SI"),
        ("ALGINATO PROPILENGLICOL",  "3913.10.00.310V", 0,     0.03, 0.21, "SI", "SI"),
        ("CARRAGENINA",              "1302.39.10.000A", 0.09,  0.03, 0.21, "NO", "NO"),
        ("GOMA XANTICA",             "3913.90.20.000H", 0,     0.03, 0.21, "NO", "NO"),
        ("GOMA GELLAN",              "3913.90.90.000B", 0,     0.03, 0.21, "SI", "SI"),
        ("GOMA TARA",                "1302.39.90.000D", 0.072, 0.03, 0.21, "NO", "NO"),
        ("GOMA GUAR",                "1302.32.20.000B", 0,     0.03, 0.21, "NO", "NO"),
        ("GOMA GARROFIN",            "1302.32.19.000K", 0.072, 0.03, 0.21, "NO", "NO"),
        ("GOMA KONJAC",              "1302.39.90.000D", 0.072, 0.03, 0.21, "NO", "NO"),
        ("AGAR",                     "1302.31.00.000V", 0.09,  0.03, 0.21, "NO", "NO"),
        ("NATAMICINA",               "3808.92.99.990M", 0.08,  0.03, 0.21, "SI", "SI"),
        ("NISINA",                   "3824.99.89.990D", 0.126, 0.03, 0.21, "SI", "SI"),
        ("HEXAMETAFOSFATO DE SODIO", "2835.39.10.000D", 0.09,  0.03, 0.21, "SI", "SI"),
        ("VITAMINA B12",             "2936.26.10.000J", 0.126, 0.03, 0.21, "NO", "NO"),
        ("VITAMINA D3",              "2936.29.21.000M", 0,     0.03, 0.21, "NO", "NO"),
        ("CITROFOL",                 "2918.15.00.200E", 0.108, 0.03, 0.21, "SI", "SI"),
        ("TRANSGLUTAMINASA",         "3507.90.42.000V", 0,     0.03, 0.21, "NO", "NO"),
        ("POLIDEXTROSA",             "3907.10.41.000A", 0,     0,    0.21, "NO", "NO"),
        ("SULFATO DE CALCIO",        "2833.29.90.100R", 0.09,  0.03, 0.21, "NO", "NO"),
        ("CLORURO DE POTASIO",       "3104.20.90.000Y", 0,     0.03, 0.21, "NO", "NO"),
        ("TEXTURE ANALYSER",         "9027.89.99.900A", 0.02,  0,    0.21, "SI", "SI"),
        ("CASEINATE DE SODIO",       "3501.90.11.900W", 0.126, 0.03, 0.21, "NO", "NO"),
        ("QUESO EN POLVO",           "0406.20.00.990U", 0.16,  0.03, 0.21, "NO", "NO"),
        ("GLUCO DELTA LACTONA",      "2932.20.90.900C", 0,     0,    0.21, "SI", "SI"),
    ]
    for p in posiciones_default:
        c.execute("INSERT OR IGNORE INTO posiciones (producto,ncm,die,te,iva,iva_ad,ganancias) VALUES (?,?,?,?,?,?,?)", p)

    mestre = [
        (0,     217605, 240755, 263895, 309280, 366685),
        (801,   338890, 368500, 407265, 485110, 581440),
        (7501,  516225, 548525, 583695, 664550, 748255),
        (20001, 564760, 592260, 627430, 708130, 820395),
    ]
    for m in mestre:
        c.execute("INSERT OR IGNORE INTO tarifas_acarreo (despachante,tipo,hasta_kg,caba,gba_30,gba_50,pilar,gba_70,gba_100) VALUES ('MESTRE','STANDARD',?,?,?,?,?,?,?)",
            (m[0], m[1], m[2], m[3], m[3], m[4], m[5]))

    adduci = [
        (0,     242000, 328000, 328000, 0),
        (51,    368000, 461000, 461000, 504000),
        (4901,  420000, 557000, 557000, 684000),
        (20001, 486000, 641700, 641700, 772800),
    ]
    for a in adduci:
        c.execute("INSERT OR IGNORE INTO tarifas_acarreo (despachante,tipo,hasta_kg,caba,gba_30,gba_50,pilar) VALUES ('ADDUCI','STANDARD',?,?,?,?,?)",
            (a[0], a[1], a[2], a[3], a[4]))

    # Migraciones — agregar columnas si no existen (safe para DBs existentes)
    for col_def in ["etd TEXT DEFAULT ''", "eta TEXT DEFAULT ''", "modal TEXT DEFAULT 'Maritimo'", "incoterm_guardado TEXT DEFAULT ''"]:
        col_name = col_def.split()[0]
        try:
            c.execute(f"ALTER TABLE costeos ADD COLUMN {col_def}")
        except Exception:
            pass  # columna ya existe

    for col_def in [
        "vuce_consultado_at TEXT DEFAULT ''",
        "aec REAL DEFAULT 0",
        "dumping INTEGER DEFAULT 0",
        "la INTEGER DEFAULT 0",
    ]:
        try:
            c.execute(f"ALTER TABLE posiciones ADD COLUMN {col_def}")
        except Exception:
            pass  # columna ya existe

    conn.commit()
    conn.close()

def get_config(key, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def set_config(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO config (key,value) VALUES (?,?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_all_config():
    conn = get_conn()
    rows = conn.execute("SELECT key, value FROM config").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def get_posiciones():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM posiciones ORDER BY producto").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_posicion_by_producto(producto):
    conn = get_conn()
    row = conn.execute("SELECT * FROM posiciones WHERE producto=?", (producto,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_costeo(data: dict):
    conn = get_conn()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    conn.execute(f"INSERT OR REPLACE INTO costeos ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()

def get_historial():
    conn = get_conn()
    rows = conn.execute("""
        SELECT c.*, v.total_vep_real, v.diff_total_vep, v.diff_valor_aduana
        FROM costeos c
        LEFT JOIN validaciones v ON c.btc = v.btc
        ORDER BY c.fecha DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_costeo_by_btc(btc):
    conn = get_conn()
    row = conn.execute("SELECT * FROM costeos WHERE btc=?", (btc,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_validacion(data: dict):
    conn = get_conn()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    conn.execute(f"INSERT INTO validaciones ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()

def get_tarifas_acarreo(despachante):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM tarifas_acarreo WHERE despachante=? AND tipo='STANDARD' ORDER BY hasta_kg",
        (despachante.upper(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def upsert_tarifa(despachante, tipo, hasta_kg, caba, gba_30, gba_50, pilar):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO tarifas_acarreo (despachante,tipo,hasta_kg,caba,gba_30,gba_50,pilar,updated_at) VALUES (?,?,?,?,?,?,?,datetime('now'))",
        (despachante, tipo, hasta_kg, caba, gba_30, gba_50, pilar))
    conn.commit()
    conn.close()

def save_costeo_items(btc: str, items: list):
    conn = get_conn()
    conn.execute("DELETE FROM costeo_items WHERE btc=?", (btc,))
    for i, item in enumerate(items, 1):
        conn.execute("""INSERT INTO costeo_items
            (btc, item_num, producto, ncm, cantidad_kg, precio_unit, fob,
             valor_aduana, die, te, base_imponible, iva, iva_ad, ganancias,
             ing_brutos, total_vep_usd)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (btc, i, item["producto"], item["ncm"],
             item["cantidad_kg"], item["precio_unit"], item["fob"],
             item["valor_aduana"], item["di"], item["te"], item["base_imponible"],
             item["iva"], item["iva_ad"], item["ganancias"],
             item["ing_brutos"], item["total_vep_usd"]))
    conn.commit()
    conn.close()

def get_costeo_items(btc: str) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM costeo_items WHERE btc=? ORDER BY item_num", (btc,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def importar_nomenclador(txt_path):
    import re
    with open(txt_path, 'rb') as f:
        content = f.read().decode('latin-1')
    registros = []
    for line in content.split('\n'):
        parts = line.split('@')
        if len(parts) < 10:
            continue
        ncm_raw = parts[1].strip()
        if not re.match(r'^[1-9]\d{3}\.\d{2}\.\d{2}\.\d{3}[A-Z]$', ncm_raw):
            continue
        try:
            die  = float(parts[4].strip().replace(',','.')) / 100
            re_v = float(parts[3].strip().replace(',','.')) / 100
            desc = parts[9].strip()
            registros.append((ncm_raw, desc, die, re_v))
        except:
            continue
    conn = get_conn()
    conn.executemany("INSERT OR REPLACE INTO arancel (ncm,descripcion,die,re) VALUES (?,?,?,?)", registros)
    conn.commit()
    conn.close()
    return len(registros)

def buscar_arancel(query, limit=10):
    conn = get_conn()
    q = f"%{query.upper()}%"
    rows = conn.execute("""
        SELECT ncm, descripcion, die, re FROM arancel
        WHERE ncm LIKE ? OR UPPER(descripcion) LIKE ?
        LIMIT ?
    """, (q, q, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_posicion_by_ncm(ncm: str) -> dict | None:
    """Busca una posición por NCM (no por producto)."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM posiciones WHERE ncm=?", (ncm,)).fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_posicion_vuce(producto: str, ncm: str, datos: dict):
    """
    Guarda o actualiza una posición con datos de VUCE.
    datos: dict con die, iva, iva_ad_pct, ganancias_pct, aec, dumping, la
    """
    from datetime import datetime
    conn = get_conn()
    existing = conn.execute("SELECT id FROM posiciones WHERE producto=? OR ncm=?", (producto, ncm)).fetchone()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    iva_ad    = "SI" if float(datos.get("iva_ad_pct") or 0) > 0 else "NO"
    ganancias = "SI" if float(datos.get("ganancias_pct") or 0) > 0 else "NO"

    if existing:
        conn.execute("""
            UPDATE posiciones SET
                producto=?, ncm=?, die=?, te=?, iva=?,
                iva_ad=?, iva_ad_pct=?, ganancias=?, ganancias_pct=?,
                aec=?, dumping=?, la=?, vuce_consultado_at=?, updated_at=datetime('now')
            WHERE id=?
        """, (
            producto, ncm,
            float(datos.get("die") or 0),
            0.03,
            float(datos.get("iva") or 0.21),
            iva_ad, float(datos.get("iva_ad_pct") or 0.20),
            ganancias, float(datos.get("ganancias_pct") or 0.06),
            float(datos.get("aec") or 0),
            int(bool(datos.get("dumping", False))),
            int(bool(datos.get("la", False))),
            now,
            existing["id"]
        ))
    else:
        conn.execute("""
            INSERT INTO posiciones
                (producto, ncm, die, te, iva, iva_ad, iva_ad_pct,
                 ganancias, ganancias_pct, aec, dumping, la, vuce_consultado_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            producto, ncm,
            float(datos.get("die") or 0),
            0.03,
            float(datos.get("iva") or 0.21),
            iva_ad, float(datos.get("iva_ad_pct") or 0.20),
            ganancias, float(datos.get("ganancias_pct") or 0.06),
            float(datos.get("aec") or 0),
            int(bool(datos.get("dumping", False))),
            int(bool(datos.get("la", False))),
            now,
        ))
    conn.commit()
    conn.close()


def init_demo_data():
    """Carga datos de ejemplo para el modo demo."""
    conn = get_conn()
    # Solo insertar si no hay datos
    count = conn.execute("SELECT COUNT(*) FROM posiciones").fetchone()[0]
    if count > 0:
        conn.close()
        return

    # Posiciones de ejemplo
    posiciones_demo = [
        ("ALGINATO DE SODIO",    "3913.10.00.210P", 0,     0.03, 0.21, "SI", "SI"),
        ("CARRAGENINA",          "1302.39.10.000A", 0.09,  0.03, 0.21, "NO", "NO"),
        ("GOMA XANTICA",         "3913.90.20.000H", 0,     0.03, 0.21, "NO", "NO"),
        ("GOMA GELLAN",          "3913.90.90.000B", 0,     0.03, 0.21, "SI", "SI"),
        ("TRANSGLUTAMINASA",     "3507.90.42.000V", 0,     0.03, 0.21, "SI", "SI"),
        ("NATAMICINA 50%",       "3808.92.99.990M", 0.08,  0.03, 0.21, "SI", "SI"),
        ("AGAR",                 "1302.31.00.000V", 0.09,  0.03, 0.21, "NO", "NO"),
    ]
    c = conn.cursor()
    for p in posiciones_demo:
        c.execute("INSERT OR IGNORE INTO posiciones (producto,ncm,die,te,iva,iva_ad,ganancias) VALUES (?,?,?,?,?,?,?)", p)

    # Config demo
    demo_config = {
        "tc": "1400", "arancel_sim_usd": "10",
        "mestre_pct": "0.008", "mestre_min": "160",
        "adduci_pct": "0.01", "adduci_min": "100",
        "terminal_usd": "800", "senasa_ars": "11300",
        "senasa_madera_usd": "15", "inal_ars": "28300",
        "gastos_op_ars": "85000", "vep_anmat_ars": "102370",
        "gastos_bancarios_usd": "95", "lakaut_usd": "30",
        "distancia_km": "50",
    }
    for k, v in demo_config.items():
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (k, v))

    # Costeos de ejemplo
    from datetime import datetime
    costeos_demo = [
        {
            "btc": "DEMO-001", "fecha": "2024-03-15 10:00",
            "producto": "ALGINATO DE SODIO", "ncm": "3913.10.00.210P",
            "proveedor": "Proveedor China S.A.", "despachante": "Mestre",
            "incoterm": "FOB", "origen": "Qingdao", "bloque": "NO MERCOSUR",
            "co": "NO", "tc": 1200, "cantidad_kg": 5000, "precio_unit": 8.90,
            "fob": 44500, "flete": 3200, "cfr": 47700, "seguro": 238.5,
            "cif": 47938.5, "ajuste_incluir": 0, "ajuste_deducir": 0,
            "valor_aduana": 47938.5, "di": 0, "te": 1438.16,
            "base_imponible": 49376.66, "iva": 10369.1, "iva_ad": 9875.33,
            "ganancias": 2962.6, "ing_brutos": 602.4, "arancel_sim": 10,
            "multa": 0, "total_vep_usd": 25257.59, "total_vep_ars": 30309108,
            "forwarder": 0, "terminal": 800, "acarreo": 320, "custodia": 0,
            "senasa": 9.42, "senasa_madera": 15, "inal": 23.58, "gastos_op": 70.83,
            "honorarios": 383.51, "vep_anmat": 85.31, "gastos_bancarios": 95,
            "lakaut": 30, "subtotal_gastos": 1832.65, "transferencia_despa": 28495.58,
            "precio_total": 77028.74, "costo_kg": 15.41,
            "notas": "Embarque de ejemplo", "etd": "2024-03-01", "eta": "2024-03-15",
            "modal": "Maritimo",
        },
        {
            "btc": "DEMO-002", "fecha": "2024-04-20 14:00",
            "producto": "TRANSGLUTAMINASA", "ncm": "3507.90.42.000V",
            "proveedor": "Enzimas del Este Ltd.", "despachante": "Adduci",
            "incoterm": "FCA", "origen": "Shanghai", "bloque": "NO MERCOSUR",
            "co": "NO", "tc": 1350, "cantidad_kg": 100, "precio_unit": 3.0,
            "fob": 300, "flete": 831, "cfr": 1131, "seguro": 5.66,
            "cif": 1136.66, "ajuste_incluir": 0, "ajuste_deducir": 0,
            "valor_aduana": 1136.66, "di": 0, "te": 34.1,
            "base_imponible": 1170.76, "iva": 245.86, "iva_ad": 234.15,
            "ganancias": 70.25, "ing_brutos": 14.28, "arancel_sim": 10,
            "multa": 0, "total_vep_usd": 608.64, "total_vep_ars": 821664,
            "forwarder": 0, "terminal": 205.82, "acarreo": 180, "custodia": 0,
            "senasa": 8.37, "senasa_madera": 15, "inal": 20.96, "gastos_op": 62.96,
            "honorarios": 100, "vep_anmat": 75.83, "gastos_bancarios": 95,
            "lakaut": 30, "subtotal_gastos": 793.94, "transferencia_despa": 1062.29,
            "precio_total": 2538.24, "costo_kg": 25.38,
            "notas": "Aéreo ejemplo", "etd": "2024-04-10", "eta": "2024-04-20",
            "modal": "Aereo",
        },
    ]
    for c_data in costeos_demo:
        cols = ", ".join(c_data.keys())
        vals = ", ".join(["?"] * len(c_data))
        try:
            c.execute(f"INSERT OR IGNORE INTO costeos ({cols}) VALUES ({vals})", list(c_data.values()))
        except Exception:
            pass

    # Matriz de costos de ejemplo para el predictor
    try:
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
        matriz_demo = [
            ("DEMO-001", "ALGINATO DE SODIO", 5000, 8.90, 44500, 362, 120, 22,
             838.70, 87.48, 864.19, 221.49, 1304.92, 381.62, 0, 0, 0, 48703, 9.74, "Maritimo"),
            ("DEMO-003", "ALGINATO DE SODIO", 3000, 10.10, 30300, 237, 138, 23,
             945.00, 93.69, 501.00, 151.50, 929.42, 354.10, 0, 0, 0, 33172, 11.06, "Maritimo"),
            ("DEMO-004", "ALGINATO DE SODIO", 5000, 8.80, 44000, 353, 100, 23,
             980.00, 94.73, 520.00, 220.00, 1336.93, 321.02, 0, 0, 0, 47949, 9.59, "Maritimo"),
            ("DEMO-005", "CARRAGENINA", 5000, 9.90, 49500, 508, 141, 20,
             800.00, 147.85, 1692.57, 495.00, 6116.43, 437.22, 0, 0, 0, 59859, 11.97, "Maritimo"),
            ("DEMO-006", "CARRAGENINA", 3000, 15.82, 47460, 382, 100, 23,
             306.64, 87.21, 665.00, 237.30, 346.29, 0, 0, 0, 0, 49608, 16.54, "Maritimo"),
            ("DEMO-007", "TRANSGLUTAMINASA", 100, 3.00, 300, 100, 50, 20,
             279.00, 152.58, 831.00, 1.51, 76.03, 402, 0, 0, 0, 2212, 22.12, "Aereo"),
            ("DEMO-008", "GOMA XANTICA", 2400, 8.00, 19200, 153, 77, 9,
             498.30, 52.95, 362.16, 96.00, 679.75, 183.02, 0, 0, 0, 21312, 8.88, "Maritimo"),
            ("DEMO-009", "AGAR", 5000, 12.90, 64500, 521, 130, 23,
             979.78, 95.58, 687.36, 322.50, 7839.20, 296.86, 0, 0, 0, 75395, 15.08, "Maritimo"),
            ("DEMO-010", "NATAMICINA 50%", 1000, 46.00, 46000, 460, 61, 9,
             404.00, 147.95, 204.61, 230.00, 129.30, 208.50, 0, 0, 0, 47856, 47.86, "Maritimo"),
            ("DEMO-011", "GOMA GELLAN", 3000, 14.80, 44400, 363, 130, 23,
             800.00, 101.35, 1378.20, 222.00, 1374.89, 352.15, 0, 0, 0, 49145, 16.38, "Maritimo"),
        ]
        conn.executemany(
            "INSERT INTO matriz_costos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            matriz_demo
        )
    except Exception as e:
        pass

        conn.commit()
    conn.close()
