import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdetails, commonteamroster, teamgamelog
import base64

# 🔥 Configuração da Página
st.set_page_config(page_title="Comparação de Times", layout="wide")

# 📂 Diretórios das imagens
LOGOS_DIR = "Logos"
FOTOS_DIR = "fotos"

# 🎯 Função para obter o ID do time pelo nome
def obter_id_time(nome_time):
    lista_times = teams.get_teams()
    for time in lista_times:
        if time["full_name"] == nome_time:
            return time["id"]
    return None

def encode_image_to_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    return None

# 🎯 Função para carregar a logo do time
def carregar_logo_time(nome_time):
    nome_formatado = nome_time.lower().replace(" ", "_") + ".png"
    caminho_logo = os.path.join(LOGOS_DIR, nome_formatado)

    img_base64 = encode_image_to_base64(caminho_logo)
    if img_base64:
        return f"data:image/png;base64,{img_base64}"
    
    return "https://via.placeholder.com/150"

# 🎯 Função para obter estatísticas dos jogos
def calcular_estatisticas_jogos(team_id):
    try:
        jogos = teamgamelog.TeamGameLog(team_id=team_id, season="2024-25").get_data_frames()[0]

        jogos_casa = jogos[jogos["MATCHUP"].str.contains("vs")]
        jogos_fora = jogos[jogos["MATCHUP"].str.contains("@")]

        estatisticas = {
            "Vitórias em Casa": (jogos_casa["WL"] == "W").sum(),
            "Derrotas em Casa": (jogos_casa["WL"] == "L").sum(),
            "Vitórias Fora": (jogos_fora["WL"] == "W").sum(),
            "Derrotas Fora": (jogos_fora["WL"] == "L").sum(),
            "Pontos por Jogo": jogos["PTS"].mean(),
            "Assistências por Jogo": jogos["AST"].mean(),
            "Rebotes por Jogo": jogos["REB"].mean(),
        }

        return estatisticas, jogos

    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {e}")
        return None, pd.DataFrame()

# 🎯 Função para obter o elenco do time
def obter_elenco_time(team_id):
    return commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]

# 🎯 Função para carregar a foto do jogador (mantendo layout original)
def carregar_foto_jogador(nome_jogador):
    nome_formatado = nome_jogador.lower().replace(" ", "-") + ".png"
    caminho_foto = os.path.join(FOTOS_DIR, nome_formatado)

    if os.path.exists(caminho_foto):  
        with open(caminho_foto, "rb") as img_file:
            base64_str = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{base64_str}"
    
    return "https://via.placeholder.com/80"

# 🎯 Seleção de Times
lista_times = [t["full_name"] for t in teams.get_teams()]

col1, col2 = st.columns(2)

with col1:
    time_1 = st.selectbox("Escolha o primeiro time", lista_times, index=0)

with col2:
    time_2 = st.selectbox("Escolha o segundo time", lista_times, index=1)

# Obter IDs dos times
team_1_id = obter_id_time(time_1)
team_2_id = obter_id_time(time_2)

# 🔹 Exibir os dados lado a lado
if team_1_id and team_2_id:
    estatisticas_1, jogos_temporada_1 = calcular_estatisticas_jogos(team_1_id)
    estatisticas_2, jogos_temporada_2 = calcular_estatisticas_jogos(team_2_id)

    col1, col2 = st.columns(2)

    with col1:
        st.image(carregar_logo_time(time_1), width=150)
        st.subheader(f"📊 Estatísticas do {time_1}")
        for chave, valor in estatisticas_1.items():
            st.write(f"**{chave}:** {valor:.1f}" if isinstance(valor, float) else f"**{chave}:** {valor}")

    with col2:
        st.image(carregar_logo_time(time_2), width=150)
        st.subheader(f"📊 Estatísticas do {time_2}")
        for chave, valor in estatisticas_2.items():
            st.write(f"**{chave}:** {valor:.1f}" if isinstance(valor, float) else f"**{chave}:** {valor}")

    # 📌 Exibir elencos lado a lado (mantendo o formato original)
    elenco_1 = obter_elenco_time(team_1_id)
    elenco_2 = obter_elenco_time(team_2_id)


    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Elenco do {time_1}")
        num_colunas = 5
        jogadores = elenco_1.to_dict(orient="records")
        
        for i in range(0, len(jogadores), num_colunas):
            cols = st.columns(num_colunas)
            for j, jogador in enumerate(jogadores[i:i + num_colunas]):
                with cols[j]:
                    foto_url = carregar_foto_jogador(jogador["PLAYER"])
                    st.markdown(
                        f'<a href="/jogadores?team={time_1}&player={jogador["PLAYER"]}">'
                        f'<img src="{foto_url}" width="80">'
                        '</a>',
                        unsafe_allow_html=True
                    )
                    st.write(f"**{jogador['PLAYER']}**")
                    st.write(f"📌 {jogador['POSITION']}")

    with col2:
        st.subheader(f"Elenco do {time_2}")
        num_colunas = 5
        jogadores = elenco_2.to_dict(orient="records")

        for i in range(0, len(jogadores), num_colunas):
            cols = st.columns(num_colunas)
            for j, jogador in enumerate(jogadores[i:i + num_colunas]):
                with cols[j]:
                    foto_url = carregar_foto_jogador(jogador["PLAYER"])
                    st.markdown(
                        f'<a href="/jogadores?team={time_2}&player={jogador["PLAYER"]}">'
                        f'<img src="{foto_url}" width="80">'
                        '</a>',
                        unsafe_allow_html=True
                    )
                    st.write(f"**{jogador['PLAYER']}**")
                    st.write(f"📌 {jogador['POSITION']}")

else:
    st.error("❌ Times não encontrados. Selecione times válidos.")
