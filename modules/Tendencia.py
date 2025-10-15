# modules/DolarTendencia.py
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

class DolarTendencia:
    @staticmethod
    def show():
        st.title("📈 Tendência do Dólar (USD/BRL) – Indicadores Yahoo Finance")

        # Baixa dados do último ano
        ticker = "USDBRL=X"
        df = yf.download(ticker, period="1y", interval="1d").dropna()

        if df.empty:
            st.error("Não foi possível obter dados do Yahoo Finance.")
            return

        # Calcula os 5 indicadores principais
        df["MA20"] = df["Close"].rolling(20).mean()          # Média móvel curta
        df["MA50"] = df["Close"].rolling(50).mean()          # Média móvel longa
        df["RSI"] = 100 - (100 / (1 + df["Close"].pct_change().clip(lower=0).rolling(14).mean() /
                                  abs(df["Close"].pct_change()).rolling(14).mean()))
        df["MACD"] = df["Close"].ewm(span=12, adjust=False).mean() - df["Close"].ewm(span=26, adjust=False).mean()
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["Volatility"] = df["Close"].pct_change().rolling(20).std() * 100

        st.subheader("Indicadores utilizados")
        st.markdown("""
        1️⃣ **Média Móvel 20 dias (MA20)** – mostra tendência de curto prazo  
        2️⃣ **Média Móvel 50 dias (MA50)** – mostra tendência de médio prazo  
        3️⃣ **RSI (Índice de Força Relativa)** – indica sobrecompra (>70) ou sobrevenda (<30)  
        4️⃣ **MACD (Moving Average Convergence Divergence)** – mede momentum e cruzamentos de tendência  
        5️⃣ **Volatilidade (20 dias)** – mostra intensidade das variações recentes
        """)

        # Plot
        st.subheader("📊 Gráfico do Dólar e Médias Móveis")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df.index, df["Close"], label="Fechamento", color="black")
        ax.plot(df.index, df["MA20"], label="MA20", color="blue", linestyle="--")
        ax.plot(df.index, df["MA50"], label="MA50", color="orange", linestyle="--")
        ax.legend()
        ax.set_title("USD/BRL - Últimos 12 meses")
        ax.set_ylabel("Cotação (R$)")
        st.pyplot(fig)

        # Exibe métricas resumidas
        st.subheader("📋 Resumo dos Indicadores (última data)")
        last = df.iloc[-1]
        st.write(pd.DataFrame({
            "Indicador": ["MA20", "MA50", "RSI", "MACD", "Volatilidade"],
            "Valor": [last["MA20"], last["MA50"], last["RSI"], last["MACD"], last["Volatility"]]
        }).set_index("Indicador"))

        # Interpretação automática
        st.subheader("🧭 Interpretação da Tendência Atual")
        tendencia = ""
        if last["MA20"] > last["MA50"]:
            tendencia = "alta (curto prazo acima do médio prazo)"
        elif last["MA20"] < last["MA50"]:
            tendencia = "baixa (curto prazo abaixo do médio prazo)"
        else:
            tendencia = "neutra"

        rsi_status = "sobrecomprado" if last["RSI"] > 70 else "sobrevendido" if last["RSI"] < 30 else "neutro"

        st.success(f"Tendência de {tendencia}. RSI indica mercado {rsi_status}. "
                   f"Volatilidade atual: {last['Volatility']:.2f}%.")

