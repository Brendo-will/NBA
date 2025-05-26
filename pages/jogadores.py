import streamlit as st
from nba_api.stats.endpoints import playergamelog, commonteamroster
from nba_api.stats.static import teams
import datetime
import pandas as pd
import os
import base64

FOTOS_DIR = "fotos"

# Dicionário de tradução das estatísticas
TRADUCAO_METRICAS = {
    "PTS": "Pontos",
    "AST": "Assistências",
    "REB": "Rebotes",
    "STL": "Roubos de Bola",
    "BLK": "Bloqueios",
    "TOV": "Turnovers",
    "+/-": "Saldo de Pontos",
    "MIN": "Minutos por Jogo",
    "FG%": "Aproveitamento de Arremessos",
    "3P%": "Aproveitamento de 3 Pontos",
    "FT%": "Aproveitamento de Lances Livres",
    "eFG%": "Aproveitamento Efetivo",
    "USG%": "Taxa de Uso"
}

# Função para obter a temporada atual
def obter_temporada_atual():
    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month
    return f"{ano_atual-1}-{str(ano_atual)[2:]}" if mes_atual < 7 else f"{ano_atual}-{str(ano_atual+1)[2:]}"

# Função para obter o elenco de um time
def obter_elenco_time(team_id):
    try:
        elenco = commonteamroster.CommonTeamRoster(team_id=team_id, season=obter_temporada_atual()).get_data_frames()[0]
        return {row["PLAYER"]: row["PLAYER_ID"] for _, row in elenco.iterrows()}
    except Exception as e:
        return {}

# Função para obter estatísticas do jogador
def obter_estatisticas_jogador(player_id, season=None):
    if season is None:
        season = obter_temporada_atual()
    
    try:
        game_log = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season,
            season_type_all_star="Playoffs"  # ou "Regular Season", "PlayIn", etc.
        ).get_data_frames()[0]


        if game_log.empty:
            return None, None, f"Erro: Nenhum jogo encontrado para o jogador na temporada {season}."

        # Estatísticas médias
        stats = {
            "PTS": round(game_log["PTS"].mean(), 2),
            "AST": round(game_log["AST"].mean(), 2),
            "REB": round(game_log["REB"].mean(), 2),
            "STL": round(game_log["STL"].mean(), 2),
            "BLK": round(game_log["BLK"].mean(), 2),
            "TOV": round(game_log["TOV"].mean(), 2),
            "+/-": round(game_log["PLUS_MINUS"].mean(), 2),
            "MIN": round(game_log["MIN"].mean(), 2),
            "FG%": round(game_log["FG_PCT"].mean() * 100, 2),
            "3P%": round(game_log["FG3_PCT"].mean() * 100, 2),
            "FT%": round(game_log["FT_PCT"].mean() * 100, 2),
            "eFG%": round(((game_log["FGM"] + 0.5 * game_log["FG3M"]) / game_log["FGA"]).mean() * 100, 2),
            "USG%": round((game_log["FGA"] + 0.44 * game_log["FTA"] + game_log["TOV"]).mean(), 2)
        }

        return stats, game_log, None
    except Exception as e:
        return None, None, f"Erro ao buscar estatísticas: {e}"

# Função para verificar em quantos jogos o jogador superou sua média
def calcular_percentual_superacao(game_log, metrica, media):
    if metrica not in game_log.columns:
        return 0, 0, 0  # Retorna valores padrão se a métrica não for encontrada

    jogos_acima_da_media = game_log[game_log[metrica] > media].shape[0]
    total_jogos = game_log.shape[0]

    percentual = (jogos_acima_da_media / total_jogos) * 100 if total_jogos > 0 else 0
    return round(percentual, 2), jogos_acima_da_media, total_jogos

# Função para carregar a foto do jogador
def carregar_foto_jogador(nome_jogador):
    nome_formatado = nome_jogador.lower().replace(" ", "-") + ".png"
    caminho_foto = os.path.join(FOTOS_DIR, nome_formatado)

    if os.path.exists(caminho_foto):  
        with open(caminho_foto, "rb") as img_file:
            base64_str = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{base64_str}"
    
    return "https://via.placeholder.com/150"

def get_jogadores_time(team_id):
        elenco = obter_elenco_time(team_id)
        return [{"id": pid, "nome": nome} for nome, pid in elenco.items()]
# Interface do Streamlit
def pagina_jogadores():
    st.header("🏀 Análise Estatística de Jogadores para Apostas")

    # Obtém lista de times
    lista_times = teams.get_teams()
    dict_times = {team["full_name"]: team["id"] for team in lista_times}

    # Escolha do time e jogador lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        time_selecionado = st.selectbox("Escolha um time", list(dict_times.keys()))
        team_id = dict_times[time_selecionado]

    # Obtém elenco do time selecionado
    with st.spinner(f"Carregando elenco do {time_selecionado}..."):
        elenco = obter_elenco_time(team_id)

    if not elenco:
        st.error("Erro ao carregar o elenco do time.")
        return

    with col2:
        jogador_selecionado = st.selectbox("Selecione um jogador", list(elenco.keys()))
        player_id = elenco[jogador_selecionado]

    # Obtém estatísticas do jogador selecionado
    with st.spinner(f"Buscando estatísticas de {jogador_selecionado}..."):
        stats, game_log, erro = obter_estatisticas_jogador(player_id)

    if erro:
        st.error(erro)
        return

    # Exibir foto do jogador e médias ao lado
    col1, col2 = st.columns([1, 3])
    with col1:
        foto = carregar_foto_jogador(jogador_selecionado)
        st.markdown(f'<img src="{foto}" width="150">', unsafe_allow_html=True)

    with col2:
        st.subheader(f"📊 Estatísticas Médias de {jogador_selecionado}")
        df_stats = pd.DataFrame(stats.items(), columns=["Estatística", "Valor"])
        df_stats["Estatística"] = df_stats["Estatística"].map(TRADUCAO_METRICAS)
        st.table(df_stats)

    # Criar colunas para dividir a exibição das estatísticas e dos últimos jogos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Média e Análise")
        metrica_selecionada = st.selectbox("Escolha uma métrica", list(TRADUCAO_METRICAS.keys()))
        media_metrica = stats[metrica_selecionada]
        percentual, jogos_acima, total_jogos = calcular_percentual_superacao(game_log, metrica_selecionada, media_metrica)
        st.write(f"🏀 **{jogador_selecionado} superou sua média de {TRADUCAO_METRICAS[metrica_selecionada]} ({media_metrica}) em {jogos_acima} de {total_jogos} jogos ({percentual}%).**")

    with col2:
        st.subheader("📅 Últimos Jogos")
        df_jogos = game_log[["GAME_DATE", "MATCHUP", metrica_selecionada]].rename(
            columns={"GAME_DATE": "Data", "MATCHUP": "Confronto", metrica_selecionada: TRADUCAO_METRICAS[metrica_selecionada]}
        ).round(2)
        st.dataframe(df_jogos)


    # Últimos 10 jogos
    ultimos_10_jogos = game_log.head(10)
    valores_metrica = ultimos_10_jogos[metrica_selecionada]

    # Checar se ele fez pelo menos X pontos em todos os jogos
    limite = st.number_input(f"Valor mínimo desejado para {TRADUCAO_METRICAS[metrica_selecionada]}", min_value=0, value=15)

    todos_acima = (valores_metrica >= limite).all()
    maior_valor = valores_metrica.max()

    st.write(f"📌 Nos últimos 10 jogos, o maior valor de **{TRADUCAO_METRICAS[metrica_selecionada]}** foi **{maior_valor}**.")

    if todos_acima:
        st.success(f"✅ {jogador_selecionado} fez **pelo menos {limite} {TRADUCAO_METRICAS[metrica_selecionada]}** em **todos os últimos 10 jogos**.")
    else:
        abaixo = valores_metrica[valores_metrica < limite].count()
        st.warning(f"⚠️ {jogador_selecionado} não atingiu **{limite} {TRADUCAO_METRICAS[metrica_selecionada]}** em {abaixo} dos últimos 10 jogos.")

    # Função utilitária para apostas: retorna uma lista de jogadores com id e nome
    

if __name__ == "__main__":
    pagina_jogadores()
