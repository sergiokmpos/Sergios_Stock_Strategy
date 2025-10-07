import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📈 Stock Analyzer — Resumo Mensal e Série Temporal")
st.markdown("""
Analise qualquer ativo: ações brasileiras, internacionais ou criptomoedas.
Insira o ticker, período desejado e obtenha:
- Resumo mensal com máximo, mínimo e datas
- Série temporal diária
- Frequência do dia do menor preço do mês
- Gráficos interativos
- Download dos dados em CSV
""")

# ===============================
# Função para baixar dados
# ===============================
@st.cache_data
def carregar_dados(ticker, start, end):
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)
    if df.empty:
        raise ValueError("Nenhum dado retornado. Verifique o ticker.")
    df = df.copy()
    df.reset_index(inplace=True)
    if "Date" not in df.columns:
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)
    return df

# ===============================
# Normalizar colunas OHLCV
# ===============================
def normalize_columns(df):
    """Normaliza colunas mesmo com MultiIndex ou sufixos de ticker."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join([str(i) for i in col if i]).strip() for col in df.columns.values]

    # Flatten tuplas
    df.columns = [("_".join(c) if isinstance(c, tuple) else c) for c in df.columns]

    # Remove sufixos do ticker
    cols_clean = []
    for c in df.columns:
        if "_" in c and any(x in c for x in ["Open", "High", "Low", "Close", "Volume"]):
            base = [x for x in ["Open", "High", "Low", "Close", "Volume"] if x in c][0]
            cols_clean.append(base)
        else:
            cols_clean.append(c)
    df.columns = cols_clean

    # Colunas essenciais
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in df.columns:
            if col == "Volume":
                df[col] = 0
            else:
                df[col] = df["Close"]

    return df[["Date", "Open", "High", "Low", "Close", "Volume"]]

# ===============================
# Resumo mensal detalhado
# ===============================
def resumo_mensal_detalhado(df):
    df["AnoMes"] = df["Date"].dt.to_period("M")
    registros = []

    for mes, g in df.groupby("AnoMes"):
        max_val = g["High"].max()
        min_val = g["Low"].min()
        max_data = g.loc[g["High"].idxmax(), "Date"].strftime("%Y-%m-%d")
        min_data = g.loc[g["Low"].idxmin(), "Date"].strftime("%Y-%m-%d")
        fechamento_medio = g["Close"].mean()

        registros.append({
            "Mês": str(mes),
            "Maior Preço": max_val,
            "Data Máximo": max_data,
            "Menor Preço": min_val,
            "Data Mínimo": min_data,
            "Fechamento Médio": fechamento_medio
        })

    return pd.DataFrame(registros)

# ===============================
# Frequência do dia do menor preço do mês
# ===============================
def dias_menor_preco(df):
    df["AnoMes"] = df["Date"].dt.to_period("M")
    dias = [{"Dia": i, "Contagem": 0} for i in range(1, 32)]
    dia_df = pd.DataFrame(dias)

    for mes, g in df.groupby("AnoMes"):
        idx_min = g["Low"].idxmin()
        dia_min = g.loc[idx_min, "Date"].day
        dia_df.loc[dia_df["Dia"] == dia_min, "Contagem"] += 1

    # Remove dias sem ocorrência
    dia_df = dia_df[dia_df["Contagem"] > 0]
    return dia_df

# ===============================
# Interface Streamlit
# ===============================
ticker = st.text_input("Ticker (ex: PETR4.SA, AAPL, BTC-USD):", "PETR4.SA")

col1, col2 = st.columns(2)
with col1:
    start = st.date_input("Data inicial:", datetime(2015, 1, 1))
with col2:
    end = st.date_input("Data final:", datetime.today())

if st.button("🔍 Buscar dados"):
    try:
        with st.spinner("Carregando dados..."):
            df = carregar_dados(ticker, start, end)
            df = normalize_columns(df)
            resumo = resumo_mensal_detalhado(df)
            df_dias_min = dias_menor_preco(df)

        st.success("✅ Dados carregados com sucesso!")

        # ---------------------------
        # DataFrames
        # ---------------------------
        st.subheader(f"📊 Resumo Mensal Detalhado — {ticker}")
        st.dataframe(resumo, use_container_width=True)

        st.subheader("📋 Série Temporal Diária")
        st.dataframe(df, use_container_width=True)

        st.subheader("📅 Frequência do dia do menor preço do mês")
        st.dataframe(df_dias_min, use_container_width=True)
        st.bar_chart(df_dias_min.set_index("Dia")["Contagem"], use_container_width=True)

        # ---------------------------
        # Gráficos
        # ---------------------------
        st.subheader("📈 Gráfico de Fechamento")
        st.line_chart(df.set_index("Date")["Close"], use_container_width=True)

        st.subheader("🕯️ Gráfico Candlestick Interativo")
        fig_candle = go.Figure(data=[go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker
        )])
        fig_candle.update_layout(xaxis_rangeslider_visible=False, height=500)
        st.plotly_chart(fig_candle, use_container_width=True)

        # ---------------------------
        # Botões de download CSV
        # ---------------------------
        st.download_button(
            "📥 Baixar Série Temporal (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_serie.csv"
        )
        st.download_button(
            "📥 Baixar Resumo Mensal (CSV)",
            resumo.to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_mensal.csv"
        )
        st.download_button(
            "📥 Baixar Frequência Dias (CSV)",
            df_dias_min.to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_dias_menor.csv"
        )

        # ---------------------------
        # Métricas rápidas
        # ---------------------------
        st.subheader("📊 Indicadores")
        col1, col2, col3 = st.columns(3)
        col1.metric("Preço Máximo", f"{df['High'].max():.2f}")
        col2.metric("Preço Mínimo", f"{df['Low'].min():.2f}")
        col3.metric("Variação (%)", f"{((df['Close'].iloc[-1]/df['Close'].iloc[0]-1)*100):.2f}%")

        st.markdown(
            """
            ---
            💡 **Dicas:**
            - Use `.SA` para ações brasileiras (ex: VALE3.SA, PETR4.SA)
            - Pode usar tickers internacionais ou criptos (ex: AAPL, BTC-USD)
            - Escolha qualquer período de datas
            - Clique novamente em **Buscar dados** após alterar parâmetros
            """
        )

    except Exception as e:
        st.error(f"⚠️ Erro: {e}")
