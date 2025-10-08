import streamlit as st

# Importa os módulos
from modules import (
    home,
    DiaMenorValor,
    ParticipacaoInvestidores,
    #carteira_inteligente,
    #radar_mercado,
    #simulador_investimentos,
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
        #"💼 Carteira Inteligente",
        #"🌍 Radar de Mercado",
        #"🧮 Simulador de Investimentos",
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
#elif abas == "💼 Carteira Inteligente":
#    carteira_inteligente.show()
#elif abas == "🌍 Radar de Mercado":
#    radar_mercado.show()
#elif abas == "🧮 Simulador de Investimentos":
#    simulador_investimentos.show()
#elif abas == "⚙️ Configurações":
#    configuracoes.show()

# Rodapé
st.markdown("---")
st.caption("Desenvolvido por Senhor Sérgio • Powered by Python & Streamlit 💡")
