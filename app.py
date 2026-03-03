import io
import pandas as pd
import numpy as np
import streamlit as st

pd.options.mode.chained_assignment = None

# Columnas del Excel
COL_CUENTA = "Cuenta"
COL_DESCRIPCION = "Comentario"
COL_DEBE = "Debe"
COL_HABER = "Haber"
COL_SALDO = "Saldo"

def limpiar_numeros(columna):
    if pd.api.types.is_numeric_dtype(columna):
        return columna.astype(float)
    return (
        columna.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("nan", "", regex=False)
        .replace("", np.nan)
        .astype(float)
    )

st.title("Generador de Balance y PyG desde Libro Mayor")

uploaded_file = st.file_uploader(
    "Sube tu libro mayor Excel", 
    type=["xlsx", "xls"]
)

if uploaded_file is not None:
    with st.spinner("Procesando archivo..."):
		
        gl_completo = pd.read_excel(uploaded_file, header=None)
        header_fila = detectar_header_fila(gl_completo)
        gl = gl_completo.iloc[header_fila:].reset_index(drop=True)
        gl.columns = gl.iloc[0]
        gl = gl[1:].reset_index(drop=True)
        st.info(f"Columnas detectadas: {gl.columns.tolist()}")
        
        gl.loc[:, COL_CUENTA] = gl[COL_CUENTA].ffill()
        
        gl_totales = gl[
            gl.astype(str)
            .apply(lambda row: row.str.lower().str.contains("suma movimientos", na=False).any(), axis=1)
        ]
        
        for col in [COL_DEBE, COL_HABER, COL_SALDO]:
            if col in gl_totales.columns:
                gl_totales[col] = limpiar_numeros(gl_totales[col])
                gl_totales[col] = gl_totales[col].fillna(0)
        
        balance_cuentas = gl_totales[
            ~gl_totales[COL_CUENTA].astype(str).str.startswith(("6", "7"))
        ].copy()
        balance_cuentas.rename(columns={COL_SALDO: "saldo_final"}, inplace=True)
        balance_export = balance_cuentas[[COL_CUENTA, "saldo_final"]].copy()
        
        pyg_result = gl_totales[
            gl_totales[COL_CUENTA].astype(str).str.startswith(("6", "7"))
        ].copy()
        pyg_result.rename(columns={COL_SALDO: "saldo_final"}, inplace=True)
        pyg_export = pyg_result[[COL_CUENTA, "saldo_final"]].copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Vista previa Balance")
        st.dataframe(balance_export.head(10), use_container_width=True)
        st.info(f"Total cuentas balance: {len(balance_export)}")
    
    with col2:
        st.subheader("Vista previa PyG")
        st.dataframe(pyg_export.head(10), use_container_width=True)
        st.info(f"Total cuentas PyG: {len(pyg_export)}")
    
    st.markdown("---")
    
    buffer_balance = io.BytesIO()
    with pd.ExcelWriter(buffer_balance, engine="openpyxl") as writer:
        balance_export.to_excel(writer, index=False, sheet_name="Balance")
    buffer_balance.seek(0)
    
    buffer_pyg = io.BytesIO()
    with pd.ExcelWriter(buffer_pyg, engine="openpyxl") as writer:
        pyg_export.to_excel(writer, index=False, sheet_name="PyG")
    buffer_pyg.seek(0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="Descargar Balance",
            data=buffer_balance,
            file_name="balance_resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        st.download_button(
            label="Descargar PyG",
            data=buffer_pyg,
            file_name="pyg_resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    st.success("Archivos generados correctamente!")







