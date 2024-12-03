import json
import streamlit as st
import pandas as pd
import os

# Configuração do Streamlit
st.set_page_config(page_title="Estatísticas de Jogadores", layout="wide")
st.title("Estatísticas de Jogadores da NBA")

# Seções da barra lateral
st.sidebar.header("Configurações")

# Upload do arquivo JSON
uploaded_file = st.sidebar.file_uploader("Envie o arquivo JSON", type="json")

if uploaded_file is not None:
    # Carregar dados do JSON enviado
    jogadores_data = json.load(uploaded_file)

    # Criar listas de times e status
    times_disponiveis = sorted(set(jogador['Time'] for jogador in jogadores_data))
    status_disponiveis = list(jogadores_data[0].keys())[2:]  # Pega os status a partir do terceiro campo

    # Configurações do filtro
    time_selecionado = st.sidebar.selectbox("Escolha um time", times_disponiveis)
    status_selecionado = st.sidebar.selectbox("Escolha um status", status_disponiveis)

    # Filtrar jogadores do time selecionado
    jogadores_do_time = [jogador for jogador in jogadores_data if jogador['Time'] == time_selecionado]

    # Dividir jogadores em pares
    jogadores_em_pares = [jogadores_do_time[i:i+2] for i in range(0, len(jogadores_do_time), 2)]

    # Exibir informações dos jogadores em pares
    for par in jogadores_em_pares:
        cols = st.columns(2)  # Criar duas colunas para os pares
        for idx, jogador in enumerate(par):
            # Dados do jogador
            nome_jogador = jogador['Nome Completo']
            time_jogador = jogador['Time']
            caminho_imagem = f"fotos/{nome_jogador.lower().replace(' ', '-')}.png"
            if not os.path.exists(caminho_imagem):
                caminho_imagem = "https://via.placeholder.com/150"  # Imagem padrão se não for encontrada

            # Dados do status selecionado
            dados_status = jogador[status_selecionado]

            # Exibir informações do jogador na coluna correspondente
            with cols[idx]:
                st.image(caminho_imagem, width=150)
                st.subheader(nome_jogador)
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
        st.markdown("---")  # Linha separadora entre pares
else:
    st.sidebar.warning("Por favor, envie um arquivo JSON para visualizar os dados.")
