# modules/Momentum.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

CSV_FILE = Path("empresas_salvas.csv")

def carregar_dados():
    if CSV_FILE.exists():
        try:
            return pd.read_csv(CSV_FILE)
        except Exception:
            return pd.DataFrame(columns=["Empresa", "Ticker", "Exchange"])
    return pd.DataFrame(columns=["Empresa", "Ticker", "Exchange"])

class Momentum:
    @staticmethod
    def show():
        st.title("📈 Comparativo de Momentum (até 10 ativos)")


                # topo: histórico + download
        st.subheader("📂 Histórico de Empresas Salvas")
        st.dataframe(st.session_state.df_empresas)
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Recarregar CSV do disco"):
                st.session_state.df_empresas = carregar_dados()
                st.rerun()
        with col2:
            if not st.session_state.df_empresas.empty:
                csv_bytes = st.session_state.df_empresas.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Baixar CSV", data=csv_bytes, file_name=CSV_FILE.name, mime="text/csv")

        # --- Entradas do usuário ---
        st.write("Digite até 10 tickers (ex: PETR4.SA, VALE3.SA, AAPL, MSFT...)")
        cols = st.columns(5)
        tickers = []
        for i in range(10):
            col = cols[i % 5]
            with col:
                t = st.text_input(f"Ticker {i+1}:", value="" if i > 1 else ("AAPL" if i == 0 else "MSFT"))
                if t.strip():
                    tickers.append(t.upper())

        periodo = st.selectbox("Período de análise:", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
        janela = st.slider("Período do Momentum (em dias):", 5, 60, 14)

        if st.button("Gerar Análise"):
            if not tickers:
                st.warning("Digite ao menos um ticker para gerar o gráfico.")
                return

            try:
                dfs = {}
                for ticker in tickers:
                    data = yf.download(ticker, period=periodo, progress=False)
                    if data.empty:
                        st.warning(f"Nenhum dado encontrado para {ticker}")
                        continue
                    data = data[["Close"]].dropna()
                    data["Momentum"] = data["Close"] - data["Close"].shift(janela)
                    dfs[ticker] = data

                if not dfs:
                    st.error("Nenhum dado válido encontrado para os tickers informados.")
                    return

                # --- Gráfico 1: Preços ---
                fig_price = go.Figure()
                for ticker, df in dfs.items():
                    fig_price.add_trace(go.Scatter(
                        x=df.index, y=df["Close"], mode="lines", name=ticker
                    ))

                fig_price.update_layout(
                    title="Preço de Fechamento",
                    xaxis_title="Data",
                    yaxis_title="Preço",
                    template="plotly_white",
                    height=500
                )
                st.plotly_chart(fig_price, use_container_width=True)

                # --- Gráfico 2: Momentum ---
                fig_momentum = go.Figure()
                for ticker, df in dfs.items():
                    fig_momentum.add_trace(go.Scatter(
                        x=df.index, y=df["Momentum"], mode="lines", name=f"{ticker} Momentum"
                    ))

                fig_momentum.add_hline(y=0, line_dash="dash", line_color="gray")
                fig_momentum.update_layout(
                    title=f"Momentum Comparativo ({janela} dias)",
                    xaxis_title="Data",
                    yaxis_title="Momentum",
                    template="plotly_white",
                    height=500
                )
                st.plotly_chart(fig_momentum, use_container_width=True)

                # --- Interpretação automática ---
                momentum_final = []
                for ticker, df in dfs.items():
                    if not df["Momentum"].dropna().empty:
                        ultimo_valor = df["Momentum"].iloc[-1]
                        momentum_final.append((ticker, ultimo_valor))

                if momentum_final:
                    df_rank = pd.DataFrame(momentum_final, columns=["Ticker", "Momentum"]).sort_values(
                        "Momentum", ascending=False
                    )
                    st.subheader("🏁 Ranking de Momentum Atual")
                    st.dataframe(df_rank.style.format({"Momentum": "{:.2f}"}))

                    # Mostra top 3
                    top3 = df_rank.head(3)
                    top_text = " | ".join([f"{t} ({m:.2f})" for t, m in top3.values])
                    st.success(f"Ativos com maior momentum: {top_text}")

                    # Interpretação rápida do 1º colocado
                    top1_ticker, top1_valor = top3.iloc[0]
                    if top1_valor > 0:
                        st.info(f"➡️ {top1_ticker} lidera com momentum **positivo** ({top1_valor:.2f}), indicando tendência de alta.")
                    else:
                        st.warning(f"⚠️ {top1_ticker} lidera, mas com momentum **negativo** ({top1_valor:.2f}), indicando fraqueza no curto prazo.")

            except Exception as e:
                st.error(f"❌ Erro ao obter dados: {e}")


# --- Expõe show() no nível do módulo ---
def show():
    Momentum.show()
