import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pytz
from nba_api.stats.static import teams
from nba_api.stats.endpoints import ScoreboardV2
from requests.exceptions import ReadTimeout, ConnectionError
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    LeagueStandingsV3,
    WinProbabilityPBP,
    PlayoffPicture,
    VideoDetails,
    VideoEvents
)
# Configuração da página
st.set_page_config(page_title="NBA Dashboard", layout="wide")

# Diretório de logos
LOGOS_DIR = "Logos"

# Função para obter estatísticas por jogo
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

# 🔹 Obtendo dados da NBA
st.title("🏀 NBA Dashboard - Estatísticas da Temporada 2024-25")
st.write("Selecione abaixo a métrica para ordenar os times e veja os melhores desempenhos da temporada.")

ranking_geral = obter_dados_por_jogo()

if ranking_geral is not None:
    # 🔹 Adicionar um seletor para escolher a métrica de ordenação
    metrica_opcoes = {
        "Vitórias": "W",
        "Pontos por Jogo": "PTS",
        "Rebotes por Jogo": "REB",
        "Assistências por Jogo": "AST",
        "Roubos de Bola por Jogo": "STL",
        "Bloqueios por Jogo": "BLK",
        "Turnovers por Jogo": "TOV",
        "Aproveitamento de Arremessos": "FG_PCT",
        "Aproveitamento de 3 Pontos": "FG3_PCT",
        "Aproveitamento de Lance Livre": "FT_PCT",
        "Saldo de Pontos": "PLUS_MINUS"
    }

    metrica_escolhida = st.selectbox(
        "📊 Escolha uma estatística para ordenar:",
        list(metrica_opcoes.keys()),
        index=0
    )

    # 🔹 Adicionar um slider para limitar o número de times exibidos
    num_times = st.slider("📌 Quantidade de times a exibir:", 5, len(ranking_geral), 10)

    # 🔹 Ordenar os times pela métrica selecionada
    ranking_ordenado = ranking_geral.sort_values(by=metrica_opcoes[metrica_escolhida], ascending=False).head(num_times)

    # 🔹 Exibir a tabela filtrada
    st.subheader(f"🏆 Top {num_times} Times - {metrica_escolhida}")
    st.dataframe(ranking_ordenado)

# 🔹 Criar um dicionário com os nomes dos times baseados no ID
def carregar_nomes_times():
    lista_times = teams.get_teams()
    return {team["id"]: team["full_name"] for team in lista_times}

# Dicionário global dos times
NOMES_TIMES = carregar_nomes_times()

# 🔹 Função para converter o horário da NBA (ET) para o horário de Brasília (BRT)
def converter_horario_nba_para_brasil(horario_et):
    try:
        # Converter string "6:00 pm ET" para datetime
        hora_et = datetime.strptime(horario_et.replace(" ET", ""), "%I:%M %p")

        # Ajustar fuso horário (ET + 2 horas para BRT)
        hora_brasil = hora_et + pd.Timedelta(hours=2)

        return hora_brasil.strftime("%H:%M %p")  # Retorna formato legível (ex: 20:00 PM)
    
    except Exception:
        return "Horário inválido"  # Em caso de erro

# 🔹 Função para obter os jogos e depurar a resposta da API
def obter_jogos_do_dia():
    try:
        # Ajustar para o fuso horário da NBA (Eastern Time)
        est = pytz.timezone("US/Eastern")
        data_atual_est = datetime.now(est).strftime("%Y-%m-%d")

        with st.spinner(f"⏳ Buscando jogos para {data_atual_est}..."):
            scoreboard = ScoreboardV2(game_date=data_atual_est)
            df_lista = scoreboard.get_data_frames()

            # Verificar se alguma resposta foi retornada
            if not df_lista:
                st.error("⚠️ Nenhum dado retornado pela API!")
                return None
            
            df = df_lista[0]  # Pegar o primeiro DataFrame retornado

           

            # 🔹 Verificar os status dos jogos
            if "GAME_STATUS_TEXT" in df.columns:
                df["Casa"] = df["HOME_TEAM_ID"].map(NOMES_TIMES)
                df["Visitante"] = df["VISITOR_TEAM_ID"].map(NOMES_TIMES)

                # Aplicar conversão do horário ET para BRT
                df["HORÁRIO_BRASIL"] = df["GAME_STATUS_TEXT"].apply(converter_horario_nba_para_brasil)

                # st.write("📌 Status dos Jogos Retornados:")
                # st.dataframe(df[["Casa", "Visitante", "HORÁRIO_BRASIL", "GAME_STATUS_TEXT"]])

                # Filtrar jogos agendados ou em andamento
                jogos_agendados = df[df["GAME_STATUS_TEXT"].str.contains("Scheduled|Pre|pm ET|am ET", na=False)]
                return jogos_agendados

            else:
                st.error("❌ `GAME_STATUS_TEXT` não encontrado na resposta da API.")
                return None

    except Exception as e:
        st.error(f"Erro ao obter jogos do dia: {e}")
        return None


# 🔹 Obter os dados
jogos_agendados = obter_jogos_do_dia()

# 🔹 Exibir Jogos Agendados
st.subheader("📅 Jogos do dia")
if jogos_agendados is not None and not jogos_agendados.empty:
    st.dataframe(jogos_agendados[["Casa", "Visitante", "HORÁRIO_BRASIL"]])
else:
    st.write("📌 Nenhum jogo agendado encontrado na API.")
