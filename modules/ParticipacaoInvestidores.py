import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go

def show():
    st.title('Fluxo de Investimento na B3 - Dados de Mercado')
    st.markdown('''
    Dados de fluxo de investimento por tipo de investidor na B3, extraídos do site [Dados de Mercado](https://www.dadosdemercado.com.br/fluxo).
    ''')

    @st.cache_data
    def scrape_b3_data(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')

        if not table:
            st.error("Não foi possível encontrar a tabela de dados no site.")
            return pd.DataFrame()

        headers = [th.text.strip() for th in table.find('thead').find_all('th')]
        data = []
        for row in table.find('tbody').find_all('tr'):
            cols = [ele.text.strip() for ele in row.find_all('td')]
            data.append(cols)

        df = pd.DataFrame(data, columns=headers)
        return df

    def process_data(df):
        df.columns = ['Data', 'Estrangeiro', 'Institucional', 'Pessoa física', 'Inst. Financeira', 'Outros']
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        for col in ['Estrangeiro', 'Institucional', 'Pessoa física', 'Inst. Financeira', 'Outros']:
            df[col] = (
                df[col]
                .str.replace(' mi', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .astype(float)
            )
        df = df.sort_values(by='Data').reset_index(drop=True)
        return df

    url = 'https://www.dadosdemercado.com.br/fluxo'
    df_raw = scrape_b3_data(url)

    if not df_raw.empty:
        df_processed = process_data(df_raw.copy())

        st.subheader('📊 Tabela de Fluxo de Investimento Diário')
        st.dataframe(df_processed)

        # Calcular variação diária
        df_diff = df_processed.set_index('Data').diff().dropna().reset_index()

        st.subheader('📈 Variação Diária na Participação dos Investidores')
        st.dataframe(df_diff)

        # === Gráfico 1: Variação diária ===
        fig1 = go.Figure()
        for col in ['Estrangeiro', 'Institucional', 'Pessoa física', 'Inst. Financeira', 'Outros']:
            fig1.add_trace(go.Scatter(
                x=df_diff['Data'], y=df_diff[col],
                mode='lines+markers', name=col
            ))

        fig1.update_layout(
            title='Variação Diária do Fluxo de Investimento por Tipo de Investidor',
            xaxis_title='Data',
            yaxis_title='Variação (milhões de R$)',
            hovermode='x unified'
        )
        st.plotly_chart(fig1, use_container_width=True)

# === Gráfico 2: Proporção empilhada em barras ===
        df_pct = df_processed.copy()
        total = df_pct[['Estrangeiro', 'Institucional', 'Pessoa física', 'Inst. Financeira', 'Outros']].sum(axis=1)
        for col in ['Estrangeiro', 'Institucional', 'Pessoa física', 'Inst. Financeira', 'Outros']:
            df_pct[col] = (df_pct[col] / total) * 100

        fig2 = go.Figure()
        for col in ['Estrangeiro', 'Institucional', 'Pessoa física', 'Inst. Financeira', 'Outros']:
            fig2.add_trace(go.Bar(
                x=df_pct['Data'],
                y=df_pct[col],
                name=col,
                hovertemplate=f'{col}: %{{y:.1f}}%',
            ))

        fig2.update_layout(
            barmode='stack',
            title='Proporção do Fluxo de Investimento por Tipo de Investidor (%)',
            xaxis_title='Data',
            yaxis_title='Participação (%)',
            hovermode='x unified',
            legend_title='Tipo de Investidor'
        )

        st.subheader('📊 Proporção do Fluxo de Investimento (Barras Empilhadas)')
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning('⚠️ Não foi possível carregar os dados. Verifique a URL ou a estrutura do site.')
