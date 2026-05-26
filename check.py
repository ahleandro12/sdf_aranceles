import sqlite3
conn = sqlite3.connect('data/demo.db')
try:
    rows = conn.execute("SELECT producto, kg, forwarder_kg FROM matriz_costos").fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print("Error:", e)