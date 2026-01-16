import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdetails, commonteamroster, teamgamelog
import base64
from nba_api.stats.static import teams
from nba_api.stats.endpoints import ScoreboardV2
from datetime import datetime
import pandas as pd

# 🔥 Configuração da Página
st.set_page_config(page_title="Detalhes da Equipe", layout="wide")

# 📂 Diretórios das imagens
LOGOS_DIR = "Logos"
FOTOS_DIR = "fotos"

# 📌 Obter o nome do time da URL ou permitir que o usuário escolha
query_params = st.query_params
team_name_url = query_params.get("team", "")

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

# Lista de times disponíveis para seleção
lista_times = [t["full_name"] for t in teams.get_teams()]
team_name = st.sidebar.selectbox("Escolha um time:", lista_times, 
                                 index=lista_times.index(team_name_url) if team_name_url in lista_times else 0)

# Obter o ID do time
team_id = obter_id_time(team_name)

st.title(f"🏀 Detalhes da Equipe - {team_name}")

# 🎯 Função para calcular estatísticas avançadas
# 🎯 Função para calcular estatísticas avançadas
def calcular_estatisticas_avancadas(team_id):
    try:
        jogos = teamgamelog.TeamGameLog(team_id=team_id, season="2025-26").get_data_frames()[0]
        
        jogos_casa = jogos[jogos["MATCHUP"].str.contains("vs")]
        jogos_fora = jogos[jogos["MATCHUP"].str.contains("@")]
        
        estatisticas = {
            "Casa - Vitórias": (jogos_casa["WL"] == "W").sum(),
            "Casa - Derrotas": (jogos_casa["WL"] == "L").sum(),
            "Fora - Vitórias": (jogos_fora["WL"] == "W").sum(),
            "Fora - Derrotas": (jogos_fora["WL"] == "L").sum(),
            "Pontos por Jogo": jogos["PTS"].mean(),
            "Assistências por Jogo": jogos["AST"].mean(),
            "Rebotes por Jogo": jogos["REB"].mean(),
            "FG%": jogos.get("FG_PCT", pd.Series()).mean() * 100,
            "3P%": jogos.get("FG3_PCT", pd.Series()).mean() * 100,
            "FT%": jogos.get("FT_PCT", pd.Series()).mean() * 100,
            "Turnovers por Jogo": jogos.get("TOV", pd.Series()).mean(),
        }
        return estatisticas, jogos
    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {e}")
        return None, pd.DataFrame()

# 🎯 Função para obter o elenco do time
def obter_elenco_time(team_id):
    return commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]

# 🎯 Função para carregar a logo do time
def carregar_logo_time(nome_time):
    nome_formatado = nome_time.lower().replace(" ", "_") + ".png"
    caminho_logo = os.path.join(LOGOS_DIR, nome_formatado)
    img_base64 = encode_image_to_base64(caminho_logo)
    return f"data:image/png;base64,{img_base64}" if img_base64 else "https://via.placeholder.com/150"


def get_jogos_do_dia(data=None):
    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")

    nomes_times = {team["id"]: team["full_name"] for team in teams.get_teams()}

    try:
        scoreboard = ScoreboardV2(game_date=data)
        df_lista = scoreboard.get_data_frames()

        if not df_lista:
            return []

        df = df_lista[0]

        df["Casa"] = df["HOME_TEAM_ID"].map(nomes_times)
        df["Visitante"] = df["VISITOR_TEAM_ID"].map(nomes_times)

        jogos_agendados = df[df["GAME_STATUS_TEXT"].str.contains("Scheduled|Pre|pm ET|am ET", na=False)]

        jogos = [
            {
                "team1_id": row["HOME_TEAM_ID"],
                "team2_id": row["VISITOR_TEAM_ID"],
                "team1_nome": row["Casa"],
                "team2_nome": row["Visitante"],
            }
            for _, row in jogos_agendados.iterrows()
        ]

        return jogos

    except Exception as e:
        print(f"Erro ao buscar jogos do dia: {e}")
        return []

# 🎯 Função para carregar a foto do jogador
def carregar_foto_jogador(nome_jogador):
    nome_formatado = nome_jogador.lower().replace(" ", "-") + ".png"
    caminho_foto = os.path.join(FOTOS_DIR, nome_formatado)
    img_base64 = encode_image_to_base64(caminho_foto)
    return f"data:image/png;base64,{img_base64}" if img_base64 else "https://via.placeholder.com/80"

# ✅ Exibir dados se o time foi encontrado
if team_id:
    estatisticas, jogos_temporada = calcular_estatisticas_avancadas(team_id)

    col1, col2, col3 = st.columns([1, 2, 3])

    with col1:
        st.image(carregar_logo_time(team_name), width=150)

    with col2:
        st.subheader("📊 Estatísticas do Time")
        if estatisticas:
            for chave, valor in estatisticas.items():
                st.write(f"🔹 {chave}: {valor:.1f}" if isinstance(valor, float) else f"🔹 {chave}: {valor}")
        else:
            st.write("Estatísticas não disponíveis.")

    with col3:
        st.subheader("📅 Jogos da Temporada Atual")
        if not jogos_temporada.empty:
            st.dataframe(jogos_temporada[["GAME_DATE", "MATCHUP", "WL", "PTS"]].rename(
                columns={"GAME_DATE": "Data", "MATCHUP": "Confronto", "WL": "Resultado", "PTS": "Pontos"}
            ))
        else:
            st.write("Nenhum jogo registrado para esta temporada.")

    # 🏀 Exibir elenco do time
    st.subheader("📝 Elenco Atual")
    elenco = obter_elenco_time(team_id)
    
    if not elenco.empty:
        num_colunas = 5
        jogadores = elenco.to_dict(orient="records")

        for i in range(0, len(jogadores), num_colunas):
            cols = st.columns(num_colunas)
            for j, jogador in enumerate(jogadores[i:i + num_colunas]):
                with cols[j]:
                    foto_url = carregar_foto_jogador(jogador["PLAYER"])
                    st.markdown(
                        f'<a href="/jogadores?team={team_name}&player={jogador["PLAYER"]}">'
                        f'<img src="{foto_url}" width="80">'
                        '</a>',
                        unsafe_allow_html=True
                    )
                    st.write(f"**{jogador['PLAYER']}**")
                    st.write(f"📌 {jogador['POSITION']}")

    else:
        st.write("Elenco não disponível no momento.")

else:
    st.error("❌ Time não encontrado. Selecione um time válido no menu lateral.")

