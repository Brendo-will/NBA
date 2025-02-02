import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdetails, commonteamroster, teamgamelog
import base64


# 🔥 Configuração da Página
st.set_page_config(page_title="Detalhes da Equipe", layout="wide")

# 📂 Diretórios das imagens
LOGOS_DIR = "Logos"
FOTOS_DIR = "fotos"

# 📌 Obter o nome do time da URL ou permitir que o usuário escolha
query_params = st.query_params
team_name_url = query_params.get("team", [""])[0]


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
team_name = st.sidebar.selectbox("Escolha um time:", lista_times, index=lista_times.index(team_name_url) if team_name_url in lista_times else 0)

# Obter o ID do time
team_id = obter_id_time(team_name)

st.title(f"🏀 Detalhes da Equipe - {team_name}")

# 🎯 Função para obter detalhes do time
def obter_detalhes_time(team_id):
    if team_id:
        detalhes = teamdetails.TeamDetails(team_id=team_id).get_data_frames()
        return detalhes[0] if detalhes else None
    return None

# 🎯 Função para calcular estatísticas de jogos em casa e fora
def calcular_estatisticas_jogos(team_id):
    try:
        jogos = teamgamelog.TeamGameLog(team_id=team_id, season="2024-25").get_data_frames()[0]

        # Filtrar jogos em casa e fora
        jogos_casa = jogos[jogos["MATCHUP"].str.contains("vs")]
        jogos_fora = jogos[jogos["MATCHUP"].str.contains("@")]

        # Calcular vitórias, derrotas e estatísticas gerais
        estatisticas = {
            "Casa - Vitórias": (jogos_casa["WL"] == "W").sum(),
            "Casa - Derrotas": (jogos_casa["WL"] == "L").sum(),
            "Fora - Vitórias": (jogos_fora["WL"] == "W").sum(),
            "Fora - Derrotas": (jogos_fora["WL"] == "L").sum(),
            "Pontos por Jogo": jogos["PTS"].mean(),
            "Assistências por Jogo": jogos["AST"].mean(),
            "Rebotes por Jogo": jogos["REB"].mean(),
        }

        return estatisticas, jogos

    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {e}")
        return None, pd.DataFrame()

# 🎯 Função para obter os próximos jogos da temporada filtrando pelo time escolhido
def obter_proximos_jogos(time_nome):
    try:
        # URL da API da NBA que retorna o calendário da temporada 2024-25
        url = 'https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2024/league/00_full_schedule.json'
        response = requests.get(url)
        data = response.json()

        jogos_futuros = []
        hoje = datetime.now()

        # Percorre os dados da API e filtra os jogos futuros do time selecionado
        for mes in data['lscd']:  # Lista de meses
            for jogo in mes['mscd']['g']:  # Lista de jogos no mês
                data_jogo = datetime.strptime(jogo['gdte'], '%Y-%m-%d')

                # Filtrar apenas jogos futuros do time escolhido
                if data_jogo >= hoje and (jogo['v']['tn'] == time_nome or jogo['h']['tn'] == time_nome):
                    jogos_futuros.append({
                        'Data': data_jogo.strftime('%d/%m/%Y'),
                        'Confronto': f"{jogo['v']['tn']} @ {jogo['h']['tn']}",
                        'Time Visitante': jogo['v']['tn'],
                        'Time da Casa': jogo['h']['tn']
                    })

        return pd.DataFrame(jogos_futuros)

    except Exception as e:
        st.error(f"Erro ao obter os próximos jogos: {e}")
        return pd.DataFrame(columns=["Data", "Confronto", "Time Visitante", "Time da Casa"])

# 🎯 Função para obter o elenco do time
def obter_elenco_time(team_id):
    return commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]

# 🎯 Função para carregar a logo do time
def carregar_logo_time(nome_time):
    nome_formatado = nome_time.lower().replace(" ", "_") + ".png"
    caminho_logo = os.path.join(LOGOS_DIR, nome_formatado)
    img_base64 = encode_image_to_base64(caminho_logo)
    if img_base64:
        return f"data:image/png;base64,{img_base64}"
    return "https://via.placeholder.com/150"


# 🎯 Função para carregar a foto do jogador
def carregar_foto_jogador(nome_jogador):
    nome_formatado = nome_jogador.lower().replace(" ", "-") + ".png"
    caminho_foto = os.path.join(FOTOS_DIR, nome_formatado)
    img_base64 = encode_image_to_base64(caminho_foto)
    if img_base64:
        return f"data:image/png;base64,{img_base64}"
    return "https://via.placeholder.com/150"


# ✅ Exibir dados se o time foi encontrado
if team_id:
    estatisticas, jogos_temporada = calcular_estatisticas_jogos(team_id)

    col1, col2, col3 = st.columns([1, 2, 3])

    with col1:
        st.image(carregar_logo_time(team_name), width=150)

    with col2:
        st.subheader("📊 Estatísticas do Time")
        if estatisticas:
            st.write(f"🏠 Casa - Vitórias: {estatisticas['Casa - Vitórias']}, Derrotas: {estatisticas['Casa - Derrotas']}")
            st.write(f"✈️ Fora - Vitórias: {estatisticas['Fora - Vitórias']}, Derrotas: {estatisticas['Fora - Derrotas']}")
            st.write(f"🏀 Pontos por Jogo: {estatisticas['Pontos por Jogo']:.1f}")
            st.write(f"🎯 Assistências por Jogo: {estatisticas['Assistências por Jogo']:.1f}")
            st.write(f"🔄 Rebotes por Jogo: {estatisticas['Rebotes por Jogo']:.1f}")
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

    # 📝 Exibir elenco do time
    st.subheader("📝 Elenco Atual")
    elenco = obter_elenco_time(team_id)
    num_colunas = 5
    jogadores = elenco.to_dict(orient="records")

    # Exibir fotos dos jogadores com link clicável
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
    st.error("❌ Time não encontrado. Selecione um time válido no menu lateral.")