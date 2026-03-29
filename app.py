import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pytz
from nba_api.stats.static import teams
from nba_api.stats.endpoints import ScoreboardV2
from requests.exceptions import ReadTimeout, ConnectionError
from nba_api.stats.endpoints import leaguedashteamstats

# Configuração da página
st.set_page_config(page_title="NBA Dashboard", layout="wide")

st.markdown("""
    <style>
        .nav-container {
            display: flex;
            justify-content: center;
            gap: 2rem;
            padding: 1rem;
            background-color: #0E1117;
            margin-bottom: 2rem;
        }
        .nav-container button {
            background-color: #262730;
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .nav-container button:hover {
            background-color: #373A40;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🏀 NBA Estatisticas</h1>", unsafe_allow_html=True)

menu = st.radio(
    "Navegação",
    ["Top 10", "Jogos do dia"],
    horizontal=True,
    label_visibility="collapsed"
)

if menu == "Top 10":
    def obter_dados_por_jogo(retries=3, timeout=45):
        for tentativa in range(retries):
            try:
                with st.spinner("📊 Buscando estatísticas de times..."):
                    ranking = leaguedashteamstats.LeagueDashTeamStats(
                        season="2024-25",
                        season_type_all_star="Regular Season",
                        per_mode_detailed="PerGame"
                    ).get_data_frames()[0]

                colunas_desejadas = [
                    "TEAM_NAME", "GP", "W", "L", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FG_PCT", "FG3_PCT", "FT_PCT", "PLUS_MINUS"
                ]
                df = ranking[colunas_desejadas].reset_index(drop=True)

                return df

            except ReadTimeout:
                st.warning(f"Tentativa {tentativa + 1}/{retries}: Tempo limite excedido. Tentando novamente...")
                time.sleep(5)

            except ConnectionError:
                st.error("Erro de conexão. Verifique sua internet e tente novamente.")
                return None

        st.error("❌ Falha ao obter dados após várias tentativas.")
        return None

    ranking_geral = obter_dados_por_jogo()

    if ranking_geral is not None:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 🏆 Top 10 Vitórias")
            df_vitorias = ranking_geral.sort_values(by="W", ascending=False).head(10)
            df_vitorias = df_vitorias.rename(columns={"TEAM_NAME": "Times", "W": "Vitórias", "L": "Derrotas"}).reset_index(drop=True)
            st.dataframe(df_vitorias[["Times", "Vitórias", "Derrotas"]], hide_index=True)

        with col2:
            st.markdown("### 🔥 Top 10 Rebotes")
            df_rebotes = ranking_geral.sort_values(by="REB", ascending=False).head(10)
            df_rebotes = df_rebotes.rename(columns={"TEAM_NAME": "Times", "REB": "Rebotes"}).reset_index(drop=True)
            st.dataframe(df_rebotes[["Times", "Rebotes"]], hide_index=True)

        with col3:
            st.markdown("### 🎯 Top 10 Assistências")
            df_assistencias = ranking_geral.sort_values(by="AST", ascending=False).head(10)
            df_assistencias = df_assistencias.rename(columns={"TEAM_NAME": "Times", "AST": "Assistências"}).reset_index(drop=True)
            st.dataframe(df_assistencias[["Times", "Assistências"]], hide_index=True)

        col4, col5, col6 = st.columns(3)

        with col4:
            st.markdown("### 🏀 Top 10 Pontos")
            df_pontos = ranking_geral.sort_values(by="PTS", ascending=False).head(10)
            df_pontos = df_pontos.rename(columns={"TEAM_NAME": "Times", "PTS": "Pontos"}).reset_index(drop=True)
            st.dataframe(df_pontos[["Times", "Pontos"]], hide_index=True)

        with col5:
            st.markdown("### 🛡️ Top 10 Roubos")
            df_roubos = ranking_geral.sort_values(by="STL", ascending=False).head(10)
            df_roubos = df_roubos.rename(columns={"TEAM_NAME": "Times", "STL": "Roubos"}).reset_index(drop=True)
            st.dataframe(df_roubos[["Times", "Roubos"]], hide_index=True)

        with col6:
            st.markdown("### ⛔ Top 10 Bloqueios")
            df_bloqueios = ranking_geral.sort_values(by="BLK", ascending=False).head(10)
            df_bloqueios = df_bloqueios.rename(columns={"TEAM_NAME": "Times", "BLK": "Bloqueios"}).reset_index(drop=True)
            st.dataframe(df_bloqueios[["Times", "Bloqueios"]], hide_index=True)

elif menu == "Jogos do dia":
    def carregar_nomes_times():
        lista_times = teams.get_teams()
        return {team["id"]: team["full_name"] for team in lista_times}

    NOMES_TIMES = carregar_nomes_times()

    def converter_horario_nba_para_brasil(horario_et):
        try:
            hora_et = datetime.strptime(horario_et.replace(" ET", ""), "%I:%M %p")
            hora_brasil = hora_et + pd.Timedelta(hours=2)
            return hora_brasil.strftime("%H:%M %p")
        except Exception:
            return "Horário inválido"

    st.subheader("📅 Escolha a data do jogo")
    data_selecionada = st.date_input("Selecione uma data", datetime.now()).strftime("%Y-%m-%d")

    def obter_jogos_por_data(data_escolhida):
        try:
            with st.spinner(f"⏳ Buscando jogos para {data_escolhida}..."):
                scoreboard = ScoreboardV2(game_date=data_escolhida)
                df_lista = scoreboard.get_data_frames()

                if not df_lista:
                    st.error("⚠️ Nenhum dado retornado pela API!")
                    return None
                
                df = df_lista[0]

                if "GAME_STATUS_TEXT" in df.columns:
                    df["Casa"] = df["HOME_TEAM_ID"].map(NOMES_TIMES)
                    df["Visitante"] = df["VISITOR_TEAM_ID"].map(NOMES_TIMES)
                    df["HORÁRIO_BRASIL"] = df["GAME_STATUS_TEXT"].apply(converter_horario_nba_para_brasil)

                    jogos_agendados = df[df["GAME_STATUS_TEXT"].str.contains("Scheduled|Pre|pm ET|am ET", na=False)]
                    return jogos_agendados

                else:
                    st.error("❌ `GAME_STATUS_TEXT` não encontrado na resposta da API.")
                    return None

        except Exception as e:
            st.error(f"Erro ao obter jogos do dia: {e}")
            return None

    jogos_agendados = obter_jogos_por_data(data_selecionada)

    st.subheader(f"📅 Jogos do dia {data_selecionada}")
    if jogos_agendados is not None and not jogos_agendados.empty:
        st.dataframe(jogos_agendados[["Casa", "Visitante", "HORÁRIO_BRASIL"]])
    else:
        st.write("📌 Nenhum jogo encontrado para essa data.")
