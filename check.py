import sqlite3
conn = sqlite3.connect('data/biotec.db')
rows = conn.execute("SELECT btc, kg, forwarder_kg FROM matriz_costos WHERE producto LIKE '%ALGINATO%'").fetchall()
for r in rows:
    print(r)