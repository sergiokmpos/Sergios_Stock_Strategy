import streamlit as st

# Importa os módulos
from modules import (
    home,
    DiaMenorValor,
    ParticipacaoInvestidores,
    Tickers,
    Momentum,
    Tendencia
    #configuracoes
)

# Configurações da página
st.set_page_config(
    page_title="Investimentos Inteligentes",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar de navegação
st.sidebar.title("📂 Navegação")

abas = st.sidebar.radio(
    "Selecione um módulo:",
    (
        "🏠 Home",
        "📊 Dia Menor Valor e Hitorico",
        "📈 Participação Investidores",
        "🔎 Consulta de Empresas",
        "📈 Análise de Momentum",
        "📈 Tendencia"
        #"⚙️ Configurações"
    )
)

# Roteamento das páginas
if abas == "🏠 Home":
    home.show()
elif abas == "📊 Dia Menor Valor e Hitorico":
    DiaMenorValor.show()
elif abas == "📈 Participação Investidores":
    ParticipacaoInvestidores.show()
elif abas == "🔎 Consulta de Empresas":
     Tickers.show()
elif abas == "📈 Análise de Momentum":
     Momentum.show()
elif abas == "📈 Tendencia":
     Tendencia.show()
#elif abas == "🧮⚙️ Configurações":
#    configuracoes.show()

# Rodapé
st.markdown("---")
st.caption("Desenvolvido por Senhor Sérgio • Powered by Python & Streamlit 💡")
