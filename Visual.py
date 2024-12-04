import json
import streamlit as st
import pandas as pd
import os

# Configuração do Streamlit
st.set_page_config(page_title="Estatísticas de Jogadores", layout="wide")
st.title("Estatísticas de Jogadores da NBA")

# Carregar o arquivo JSON diretamente do diretório
caminho_json = os.path.join(os.path.dirname(__file__), "Jogadores_Resultado_Completo.json")
try:
    with open(caminho_json, 'r', encoding='utf-8') as f:
        jogadores_data = json.load(f)
except FileNotFoundError:
    st.error("Arquivo JSON não encontrado. Certifique-se de que 'Jogadores_Resultado_Completo.json' está no mesmo diretório do script.")
    st.stop()

# Filtrar apenas jogadores com as chaves necessárias
jogadores_com_dados = [jogador for jogador in jogadores_data if 'Time' in jogador and 'Nome Completo' in jogador]

# Criar listas de times e status dinamicamente
times_disponiveis = sorted(set(jogador['Time'] for jogador in jogadores_com_dados))
# Identificar os campos de status dinamicamente, excluindo 'Nome Completo' e 'Time'
status_disponiveis = [chave for chave in jogadores_com_dados[0].keys() if chave not in ['Nome Completo', 'Time']]

# Seções da barra lateral para configuração do filtro
st.sidebar.header("Configurações")
time_selecionado = st.sidebar.selectbox("Escolha um time", times_disponiveis)
status_selecionado = st.sidebar.selectbox("Escolha um status", status_disponiveis)

# Filtrar jogadores do time selecionado
jogadores_do_time = [jogador for jogador in jogadores_com_dados if jogador['Time'] == time_selecionado]

# Dividir jogadores em pares
jogadores_em_pares = [jogadores_do_time[i:i+2] for i in range(0, len(jogadores_do_time), 2)]

# Exibir informações dos jogadores em pares
for par in jogadores_em_pares:
    cols = st.columns(2)  # Criar duas colunas para os pares
    for idx, jogador in enumerate(par):
        # Dados do jogador
        nome_jogador = jogador.get('Nome Completo', 'Jogador Desconhecido')
        time_jogador = jogador.get('Time', 'Desconhecido')
        caminho_imagem = f"fotos/{nome_jogador.lower().replace(' ', '-')}.png"
        if not os.path.exists(caminho_imagem):
            caminho_imagem = "https://via.placeholder.com/150"  # Imagem padrão se não for encontrada

        # Dados do status selecionado
        dados_status = jogador.get(status_selecionado, [])

        # Exibir informações do jogador na coluna correspondente
        with cols[idx]:
            st.image(caminho_imagem, width=150)
            st.subheader(nome_jogador)
            if isinstance(dados_status, list) and dados_status:
                st.metric(label="Média nos Últimos Jogos", value=round(pd.Series(dados_status).mean(), 2))
                st.metric(label="Máximo nos Últimos Jogos", value=max(dados_status))
                st.subheader(f"Resumo dos Últimos Jogos - {status_selecionado}")
                st.write(
                    pd.DataFrame(
                        {
                            "Jogo": range(1, len(dados_status) + 1),
                            status_selecionado: dados_status,
                        }
                    )
                )
            else:
                st.warning("Dados insuficientes para mostrar estatísticas.")
    st.markdown("---")  # Linha separadora entre pares
