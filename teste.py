import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO
import openpyxl


st.set_page_config(page_title="Extrator de FMEA", layout="wide")

st.title("📄 Extrator de Tabela FMEA de PDF")
st.markdown("Envie o arquivo PDF e selecione as páginas para extrair os dados da tabela FMEA.")

uploaded_file = st.file_uploader("📎 Envie o arquivo PDF", type=["pdf"])

start_page = st.number_input("Página inicial (ex: 7)", min_value=1, value=7)
end_page = st.number_input("Página final (ex: 129)", min_value=1, value=7)

if uploaded_file and st.button("🔍 Extrair FMEA"):
    with pdfplumber.open(uploaded_file) as pdf:
        fmea_data = []

        # Cabeçalho da tabela FMEA
        columns = [
            "Etapa do Processo / Função", "Requisitos", "Modo de falha Potencial", "Efeito Potencial da Falha",
            "Severidade", "Classificação", "Causa Potencial da Falha", "Controles Atuais do Processo Prevenção",
            "Ocorrência", "Controles Atuais do Processo Detecção", "Detecção", "NPR",
            "Ações Recomendadas", "Responsável e Prazo", "Ações Tomadas e Data de Efetivação",
            "Severidade (Pós)", "Ocorrência (Pós)", "Detecção (Pós)", "NPR (Pós)"
        ]

        for i in range(start_page - 1, end_page):
            page = pdf.pages[i]
            table = page.extract_table()

            if table:
                for row in table[1:]:  # Ignora o cabeçalho original
                    if len(row) == len(columns):
                        fmea_data.append(dict(zip(columns, row)))
                    else:
                        st.warning(f"⚠️ Página {i+1}: linha ignorada por não ter {len(columns)} colunas.")

        if fmea_data:
            df = pd.DataFrame(fmea_data)
            st.success(f"✅ {len(df)} registros extraídos com sucesso!")
            st.dataframe(df)


            # Criar arquivo Excel em memória
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)

            # Botão de download
            st.download_button(
                label="📥 Baixar como Excel",
                data=output,
                file_name="FMEA_extraido.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )




        else:
            st.error("Nenhuma tabela FMEA encontrada nas páginas selecionadas.")