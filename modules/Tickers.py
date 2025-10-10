# app_yahoo_search.py
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from pathlib import Path

CSV_FILE = Path("empresas_salvas.csv")

# ------------------------------
# Utilitários
# ------------------------------
def carregar_dados():
    if CSV_FILE.exists():
        try:
            return pd.read_csv(CSV_FILE)
        except Exception:
            return pd.DataFrame(columns=["Empresa", "Ticker", "Exchange"])
    return pd.DataFrame(columns=["Empresa", "Ticker", "Exchange"])

def salvar_dados(df):
    try:
        CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(CSV_FILE, index=False)
        return True, None
    except Exception as e:
        return False, str(e)

def buscar_ticker_por_nome(nome_empresa, max_results=8):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": nome_empresa, "lang": "en-US", "region": "US", "quotesCount": max_results, "newsCount": 0}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        return data.get("quotes", []) or []
    except Exception as e:
        st.error(f"Erro na busca no Yahoo: {e}")
        return []

# ------------------------------
# Função principal (exportável)
# ------------------------------
def show():
    st.title("🔎 Consulta de Empresas (Yahoo Finance)")

    # inicializa estado persistente do dataframe
    if "df_empresas" not in st.session_state:
        st.session_state.df_empresas = carregar_dados()

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

    st.write("---")

    # -------------- Pesquisa por nome --------------
    st.subheader("🔍 Pesquisar empresa por nome")
    with st.form("search_form", clear_on_submit=False):
        empresa_input = st.text_input("Digite nome ou parte do nome (ex: Apple, Petrobras)", key="search_text")
        search_submitted = st.form_submit_button("🔎 Pesquisar")
    if search_submitted and empresa_input and empresa_input.strip():
        resultados = buscar_ticker_por_nome(empresa_input.strip())
        if not resultados:
            st.warning("Nenhum resultado encontrado. Tente outra variação do nome.")
        else:
            # gerar rótulos e usar índices como opções (evita problemas ao retornar tuplas)
            labels = []
            for r in resultados:
                sym = r.get("symbol", "")
                short = r.get("shortname") or r.get("longname") or sym
                exch = r.get("exchange") or r.get("exchDisp") or ""
                labels.append(f"{short} — {sym} ({exch})")
            choice_index = st.selectbox("Escolha a correspondência correta", options=list(range(len(resultados))),
                                        format_func=lambda i: labels[i])
            selected = resultados[choice_index]
            symbol = selected.get("symbol")
            nome_exibido = selected.get("shortname") or selected.get("longname") or empresa_input

            st.markdown(f"**Selecionado:** {nome_exibido} — **{symbol}**")

            # tenta coletar dados via yfinance (com fallback)
            info = {}
            try:
                ticker = yf.Ticker(symbol)
                try:
                    info = ticker.info or {}
                except Exception:
                    info = getattr(ticker, "fast_info", {}) or {}
            except Exception as e:
                st.error(f"Erro ao inicializar yfinance: {e}")

            st.write("**Dados básicos (quando disponíveis):**")
            st.write(f"- Nome completo: {info.get('longName', nome_exibido)}")
            st.write(f"- Setor: {info.get('sector', 'N/A')}")
            st.write(f"- Indústria: {info.get('industry', 'N/A')}")
            st.write(f"- País: {info.get('country', selected.get('exchange', 'N/A'))}")
            st.write(f"- Moeda: {info.get('currency', 'N/A')}")
            market_cap = info.get('marketCap') or info.get('market_cap')
            st.write(f"- Valor de mercado: {market_cap if market_cap is not None else 'N/A'}")

            # Formulário consistente para adicionar a empresa encontrada
            with st.form("save_selected_form", clear_on_submit=True):
                # campos editáveis antes de salvar (mesma experiência do manual)
                nome_para_salvar = st.text_input("Nome para salvar", value=info.get("longName", nome_exibido), key="save_name")
                ticker_para_salvar = st.text_input("Ticker para salvar", value=symbol, key="save_ticker")
                exchange_para_salvar = st.text_input("Exchange (opcional)", value=selected.get("exchange", ""), key="save_exchange")
                salvar = st.form_submit_button("💾 Adicionar empresa pesquisada")
            if salvar:
                # valida duplicata (pela coluna Ticker)
                if ticker_para_salvar in st.session_state.df_empresas["Ticker"].astype(str).values:
                    st.info("⚠️ Ticker já existe no histórico.")
                else:
                    nova_linha = {"Empresa": nome_para_salvar, "Ticker": ticker_para_salvar, "Exchange": exchange_para_salvar}
                    st.session_state.df_empresas = pd.concat([st.session_state.df_empresas, pd.DataFrame([nova_linha])], ignore_index=True)
                    ok, err = salvar_dados(st.session_state.df_empresas)
                    if ok:
                        st.success(f"✅ {ticker_para_salvar} adicionado e salvo em: {CSV_FILE.resolve()}")
                        st.write(f"Linhas no CSV: {len(st.session_state.df_empresas)}")
                    else:
                        st.error(f"Erro ao salvar CSV: {err}")

    st.write("---")

    # -------------- Adicionar manualmente --------------
    st.subheader("✍️ Adicionar manualmente")
    with st.form("manual_form", clear_on_submit=True):
        nome_manual = st.text_input("Nome da Empresa (manual)", key="manual_nome")
        ticker_manual = st.text_input("Ticker (manual)", key="manual_ticker")
        exchange_manual = st.text_input("Exchange (opcional)", key="manual_exchange")
        add = st.form_submit_button("➕ Adicionar manualmente")
    if add:
        if not nome_manual or not ticker_manual:
            st.warning("Preencha nome e ticker.")
        else:
            if ticker_manual in st.session_state.df_empresas["Ticker"].astype(str).values:
                st.info("⚠️ Ticker já existe no histórico.")
            else:
                nova_linha = {"Empresa": nome_manual, "Ticker": ticker_manual, "Exchange": exchange_manual}
                st.session_state.df_empresas = pd.concat([st.session_state.df_empresas, pd.DataFrame([nova_linha])], ignore_index=True)
                ok, err = salvar_dados(st.session_state.df_empresas)
                if ok:
                    st.success("✅ Empresa adicionada manualmente!")
                    st.write(f"Salvo em: {CSV_FILE.resolve()} (linhas: {len(st.session_state.df_empresas)})")
                else:
                    st.error(f"Erro ao salvar CSV: {err}")

    st.write("---")
    st.caption("Obs: se você executar o app em um servidor/ambiente com permissões restritas, verifique o diretório atual e permissões de escrita. Se estiver usando um container, o arquivo ficará no filesystem do container.")
