import streamlit as st
from utils.api_utils import obter_dados_jogadores, obter_dados_times, obter_historico_por_temporadas
import plotly.graph_objects as go
import base64
import os

FOTOS_DIR = "fotos"

def carregar_foto_jogador(nome_jogador):
    """Carrega a foto do jogador localmente, se existir, ou usa uma imagem padrão."""
    nome_formatado = nome_jogador.lower().replace(" ", "-") + ".png"
    caminho_foto = os.path.join(FOTOS_DIR, nome_formatado)

    if os.path.exists(caminho_foto):  
        with open(caminho_foto, "rb") as img_file:
            base64_str = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{base64_str}"
    
    return "https://via.placeholder.com/150"

st.header("📈 Análise Contra Adversário")

# Seleção de Jogador e Adversário
jogadores = obter_dados_jogadores()
times = obter_dados_times()

jogador_selecionado = st.selectbox("Escolha um jogador", jogadores, format_func=lambda x: x["full_name"])
adversario = st.selectbox("Escolha um adversário", times, format_func=lambda x: x["full_name"])

temporadas = ["2021-22", "2022-23", "2023-24", "2024-25"]
temporadas_selecionadas = st.multiselect("Selecione as temporadas", temporadas, default=temporadas)

if st.button("Analisar"):
    player_id = jogador_selecionado["id"]
    adversario_abbr = adversario["abbreviation"]
    historico = obter_historico_por_temporadas(player_id, temporadas_selecionadas)

    jogos = historico[historico["MATCHUP"].str.contains(adversario_abbr)]
    
    if not jogos.empty:
        # Calcular médias
        media_pontos = jogos["PTS"].mean()
        media_assistencias = jogos["AST"].mean()
        media_rebotes = jogos["REB"].mean()

        col1, col2 = st.columns([1, 3])

        # Exibir foto do jogador
        with col1:
            foto = carregar_foto_jogador(jogador_selecionado["full_name"])
            st.markdown(f'<img src="{foto}" width="150">', unsafe_allow_html=True)

        with col2:
            st.markdown(f"### 📊 Estatísticas Médias contra {adversario['full_name']}")
            st.write(f"🏀 **Média de Pontos:** {media_pontos:.2f}")
            st.write(f"🎯 **Média de Assistências:** {media_assistencias:.2f}")  # LINHA CORRIGIDA
            st.write(f"💪 **Média de Rebotes:** {media_rebotes:.2f}")
        

        # Exibir dados detalhados das partidas
        st.dataframe(jogos[["GAME_DATE", "MATCHUP", "PTS", "REB", "AST", "STL", "BLK", "TOV", "PF"]])
    else:
        st.warning("Nenhuma partida encontrada contra esse adversário.")
