import re
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st
import plotly.express as px


# --- Função auxiliar: converte strings de valores com sufixos (mi, bi, etc.) em float ---
def _parse_value(x):
    if x is None:
        return np.nan
    s = str(x).strip()
    if s in ("", "-", "—", "None", "nan", "NaN"):
        return np.nan

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    s = s.replace("R$", "").replace("r$", "").replace("\xa0", "").strip()
    m = re.match(r'^([+-]?)([\d\.,]+)\s*([A-Za-z%]*)$', s)
    if not m:
        s2 = re.sub(r'[^\d\.,\-]', '', s)
        try:
            return float(s2.replace(',', '.'))
        except:
            return np.nan

    sign_char, num_str, suffix = m.groups()
    if sign_char == "-":
        negative = True

    # Formato BR/EN
    if "." in num_str and "," in num_str and num_str.find(".") < num_str.find(","):
        num_str = num_str.replace(".", "").replace(",", ".")
    elif "," in num_str and "." not in num_str:
        num_str = num_str.replace(",", ".")

    try:
        val = float(num_str)
    except:
        return np.nan

    # Multiplicador conforme sufixo
    suf = (suffix or "").lower().strip()
    mult = 1.0
    if suf in ("mi", "m", "milhao", "milhões", "milhoes", "milhão"):
        mult = 1e6
    elif suf in ("bi", "b", "bilhao", "bilhões", "bilhoes"):
        mult = 1e9
    elif suf in ("k", "mil"):
        mult = 1e3

    result = val * mult
    if negative:
        result = -result
    return result


# --- Função principal ---
def show():
    st.title("💰 Fluxo Acumulado e Participação por Tipo de Investidor – B3")
    st.markdown("""
    Este painel mostra **quem está adicionando ou retirando dinheiro da Bolsa** e **qual grupo domina o saldo acumulado**.  
    Dados: [dadosdemercado.com.br/fluxo](https://www.dadosdemercado.com.br/fluxo)
    """)

    url = "https://www.dadosdemercado.com.br/fluxo"

    try:
        # --- Scraping ---
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")
        if table is None:
            st.error("⚠️ Não encontrei tabela na página.")
            return

        df = pd.read_html(str(table))[0]
        df.columns = [c.strip() for c in df.columns]

        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        df = df.dropna(subset=[date_col])

        # --- Converte valores ---
        value_cols = [c for c in df.columns if c != date_col and not re.search(r'total|variaç', c, flags=re.I)]
        for c in value_cols:
            df[c] = df[c].apply(_parse_value)

        df = df.sort_values(by=date_col).reset_index(drop=True)

        st.subheader("📅 Fluxo Diário (R$)")
        st.dataframe(df, use_container_width=True)

        # --- Cálculo de acumulado ---
        df_cum = df.copy()
        for c in value_cols:
            df_cum[c] = df[c].cumsum()

        # --- Gráfico de linha: fluxo acumulado ---
        df_melt = df_cum.melt(id_vars=date_col, var_name="Investidor", value_name="Fluxo Acumulado (R$)")
        st.subheader("📈 Evolução Acumulada – Quem está adicionando ou retirando capital")
        fig_line = px.line(
            df_melt,
            x=date_col,
            y="Fluxo Acumulado (R$)",
            color="Investidor",
            markers=False,
            title="Fluxo Acumulado por Tipo de Investidor",
        )
        fig_line.update_layout(hovermode="x unified", legend_title_text="Tipo de Investidor")
        st.plotly_chart(fig_line, use_container_width=True)

        # --- Ranking final ---
        latest = df_cum.iloc[-1][value_cols].sort_values(ascending=False)
        result_df = latest.reset_index()
        result_df.columns = ["Investidor", "Fluxo Acumulado (R$)"]
        result_df["Fluxo Acumulado (R$) Num"] = result_df["Fluxo Acumulado (R$)"]
        result_df["Fluxo Acumulado (R$)"] = result_df["Fluxo Acumulado (R$) Num"].apply(
            lambda x: f"R$ {x/1e9:.2f} bi" if abs(x) > 1e9 else f"R$ {x/1e6:.2f} mi"
        )

        st.subheader("🏆 Ranking – Quem mais adicionou / retirou dinheiro no período")
        st.dataframe(result_df[["Investidor", "Fluxo Acumulado (R$)"]], use_container_width=True)

        # --- Atualização ---
        update_info = soup.find("p", class_="text-muted")
        if update_info:
            st.caption(f"📆 {update_info.text.strip()}")

    except Exception as e:
        st.error(f"❌ Erro ao obter/processar dados: {e}")
