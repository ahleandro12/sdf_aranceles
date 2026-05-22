import streamlit as st
import pandas as pd
import db

def render():
    tab1, tab2 = st.tabs(["Mestre (Trumen)", "Adduci (Traslog)"])

    for tab, despa in [(tab1,"MESTRE"), (tab2,"ADDUCI")]:
        with tab:
            tarifas = db.get_tarifas_acarreo(despa)
            if tarifas:
                df_t = pd.DataFrame(tarifas)[["hasta_kg","caba","gba_30","gba_50","pilar","updated_at"]]
                df_t.columns = ["Desde KG","CABA","GBA <=30km","GBA <=50km","Pilar","Actualizado"]
                st.dataframe(df_t, use_container_width=True, hide_index=True)

            st.divider()
            st.caption("Columnas requeridas: desde_kg, caba, gba_30, gba_50, pilar")
            arch = st.file_uploader(f"Subir tarifario {despa} (.xlsx)", type=["xlsx"], key=despa)
            if arch:
                try:
                    df_n = pd.read_excel(arch)
                    df_n.columns = [c.lower().strip() for c in df_n.columns]
                    st.dataframe(df_n, use_container_width=True)
                    if st.button(f"Confirmar {despa}", key=f"btn_{despa}"):
                        for _, row in df_n.iterrows():
                            db.upsert_tarifa(despa, "STANDARD",
                                row.get("desde_kg",0), row.get("caba",0),
                                row.get("gba_30",0), row.get("gba_50",0), row.get("pilar",0))
                        st.success("Actualizado.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
