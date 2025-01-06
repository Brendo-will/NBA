import streamlit as st
import pandas as pd
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import commonteamroster, playergamelog, teamgamelog
from PIL import Image
import os
import plotly.graph_objects as go

DEFAULT_IMAGE = "https://via.placeholder.com/150"
IMAGES_DIR = "fotos"
DEFAULT_LOGO = "https://via.placeholder.com/150"
LOGOS_DIR = "Logos"

# Função para obter dados dos times via API
@st.cache_data
def obter_dados_times():
    return teams.get_teams()

# Função para obter dados dos jogadores via API
@st.cache_data
def obter_dados_jogadores():
    return players.get_players()

# Função para obter o elenco atual de um time via API
@st.cache_data
def obter_elenco_time(team_id):
    roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
    return roster

# Função para obter as últimas 10 partidas de um jogador via API
@st.cache_data
def obter_ultimos_jogos(player_id):
    log = playergamelog.PlayerGameLog(player_id=player_id, season="2024-25").get_data_frames()[0]
    return log.head(10)

# Função para obter o histórico de jogos de um jogador para várias temporadas
@st.cache_data
def obter_historico_por_temporadas(player_id, temporadas):
    todos_jogos = []
    for temporada in temporadas:
        try:
            log = playergamelog.PlayerGameLog(player_id=player_id, season=temporada).get_data_frames()[0]
            todos_jogos.append(log)
        except Exception as e:
            st.write(f"Erro ao buscar dados para a temporada {temporada}: {e}")
    return pd.concat(todos_jogos, ignore_index=True) if todos_jogos else pd.DataFrame()

# Função para obter o log de jogos de um time via API
@st.cache_data
def obter_jogos_time(team_id):
    gamelog = teamgamelog.TeamGameLog(team_id=team_id, season="2024-25").get_data_frames()[0]
    return gamelog

# Função para carregar o logo do time
def carregar_logo_time(nome_time):
    nome_formatado = nome_time.lower().replace(" ", "_").replace("-", "_")
    caminho_logo = os.path.join(LOGOS_DIR, f"{nome_formatado}.png")
    st.write(f"Buscando logo em: {caminho_logo}")  # Linha de depuração
    if os.path.isfile(caminho_logo):
        return caminho_logo
    else:
        return DEFAULT_LOGO


# Função para carregar a foto do jogador
def carregar_foto_jogador(nome_completo):
    nome_formatado = nome_completo.lower().replace(" ", "-") + ".png"
    arquivos = os.listdir(IMAGES_DIR)
    for arquivo in arquivos:
        if arquivo.lower() == nome_formatado:
            return os.path.join(IMAGES_DIR, arquivo)
    return DEFAULT_IMAGE

# Função para calcular estatísticas de jogos
def calcular_estatisticas(jogos, casa=True):
    if casa:
        jogos_filtrados = jogos[jogos["MATCHUP"].str.contains("vs")]
    else:
        jogos_filtrados = jogos[jogos["MATCHUP"].str.contains("@")]

    vitorias = (jogos_filtrados["WL"] == "W").sum()
    derrotas = (jogos_filtrados["WL"] == "L").sum()
    total_jogos = vitorias + derrotas
    win_percentage = (vitorias / total_jogos * 100) if total_jogos > 0 else 0
    pontos_por_jogo = jogos_filtrados["PTS"].mean()
    rebotes_por_jogo = jogos_filtrados["REB"].mean()
    assistencias_por_jogo = jogos_filtrados["AST"].mean()

    return {
        "Vitórias": vitorias,
        "Derrotas": derrotas,
        "Win%": win_percentage,
        "Pontos por Jogo": pontos_por_jogo,
        "Rebotes": rebotes_por_jogo,
        "Assistências": assistencias_por_jogo,
    }

# Página 1: Estatísticas de Times
def pagina_times():
    st.header("📊 Estatísticas dos Times")
    dados_times = obter_dados_times()
    time_selecionado = st.selectbox("Escolha um time", dados_times, format_func=lambda x: x['full_name'])

    if time_selecionado:
        team_id = time_selecionado["id"]
        jogos = obter_jogos_time(team_id)
        estatisticas_casa = calcular_estatisticas(jogos, casa=True)
        estatisticas_fora = calcular_estatisticas(jogos, casa=False)

        col_logo, col_casa, col_fora = st.columns([1, 2, 2])
        with col_logo:
            logo_path = carregar_logo_time(time_selecionado["full_name"])
            st.image(logo_path, width=150)

        with col_casa:
            st.markdown("### 🏟️ Jogos em Casa")
            for key, value in estatisticas_casa.items():
                st.write(f"**{key}:** {value:.2f}" if isinstance(value, float) else f"**{key}:** {value}")

        with col_fora:
            st.markdown("### ✈️ Jogos Fora de Casa")
            for key, value in estatisticas_fora.items():
                st.write(f"**{key}:** {value:.2f}" if isinstance(value, float) else f"**{key}:** {value}")

# Página 2: Estatísticas dos Jogadores
def pagina_jogadores():
    st.header("👨‍🦰 Estatísticas dos Jogadores")
    dados_times = obter_dados_times()
    time_selecionado = st.selectbox("Escolha um time", dados_times, format_func=lambda x: x['full_name'])

    if time_selecionado:
        equipe_id = time_selecionado["id"]
        time_nome = time_selecionado["full_name"]
        elenco = obter_elenco_time(equipe_id)
        jogadores = {jogador['PLAYER']: jogador['PLAYER_ID'] for _, jogador in elenco.iterrows()}

        jogador_selecionado = st.selectbox("Selecione um jogador", list(jogadores.keys()))
        if jogador_selecionado:
            player_id = jogadores[jogador_selecionado]
            ultimos_jogos = obter_ultimos_jogos(player_id)

            st.markdown(f"### Estatísticas de {jogador_selecionado} - Últimas 10 Partidas")
            col1, col2 = st.columns([1, 3])
            with col1:
                foto = carregar_foto_jogador(jogador_selecionado)
                st.image(foto, width=150)
            with col2:
                st.write(f"**Time:** {time_nome}")

            if not ultimos_jogos.empty:
                metricas = {
                    "PTS": "Pontos",
                    "AST": "Assistências",
                    "REB": "Rebotes",
                    "STL": "Roubos de Bola",
                    "BLK": "Bloqueios",
                    "TOV": "Turnovers",
                    "PF": "Faltas Pessoais"
                }
                metrica_selecionada = st.selectbox("Selecione a métrica para o gráfico", options=metricas.keys(), format_func=lambda x: metricas[x])
                valor_referencia = st.slider(f"Escolha o limite de {metricas[metrica_selecionada]}", 1, 50, 10)

                ultimos_jogos["Cor"] = ["green" if valor >= valor_referencia else "red" for valor in ultimos_jogos[metrica_selecionada]]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=ultimos_jogos["MATCHUP"],
                    y=ultimos_jogos[metrica_selecionada],
                    text=ultimos_jogos[metrica_selecionada],
                    marker_color=ultimos_jogos["Cor"],
                    textposition="outside"
                ))
                fig.update_layout(
                    title=f"{metricas[metrica_selecionada]} de {jogador_selecionado} nas Últimas 10 Partidas (Limite: {valor_referencia})",
                    xaxis_title="Partidas",
                    yaxis_title=metricas[metrica_selecionada],
                    template="plotly_dark"
                )
                st.plotly_chart(fig)

                st.dataframe(ultimos_jogos[["GAME_DATE", "MATCHUP", metrica_selecionada]].rename(
                    columns={
                        "GAME_DATE": "Data",
                        "MATCHUP": "Confronto",
                        metrica_selecionada: metricas[metrica_selecionada]
                    }
                ))
            else:
                st.write("Nenhuma estatística encontrada para este jogador.")

# Página 3: Análise Contra Adversário
# Página 3: Análise Contra Adversário
def pagina_analise_contra_adversario():
    st.header("📈 Análise Contra Adversário")
    
    jogadores = obter_dados_jogadores()
    jogador_selecionado = st.selectbox("Escolha um jogador", jogadores, format_func=lambda x: x['full_name'])
    times = obter_dados_times()
    adversario = st.selectbox("Escolha um adversário", times, format_func=lambda x: x['full_name'])

    temporadas = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
    temporadas_selecionadas = st.multiselect("Selecione as temporadas", temporadas, default=temporadas)

    if jogador_selecionado and adversario and temporadas_selecionadas:
        player_id = jogador_selecionado['id']
        adversario_abbr = adversario['abbreviation']

        if st.button("Analisar"):
            # Buscar histórico de jogos do jogador nas temporadas selecionadas
            historico = obter_historico_por_temporadas(player_id, temporadas_selecionadas)

            # Filtrar jogos contra o adversário
            jogos_contra_adversario = historico[historico['MATCHUP'].str.contains(adversario_abbr, case=False, na=False)]
            jogos_contra_adversario = jogos_contra_adversario.head(15)  # Selecionar os últimos 15 jogos

            if not jogos_contra_adversario.empty:
                st.subheader(f"Últimos 15 Jogos de {jogador_selecionado['full_name']} Contra {adversario['full_name']}")

                # Exibir tabela
                st.dataframe(jogos_contra_adversario[["GAME_DATE", "MATCHUP", "PTS", "REB", "AST"]].rename(
                    columns={
                        "GAME_DATE": "Data",
                        "MATCHUP": "Confronto",
                        "PTS": "Pontos",
                        "REB": "Rebotes",
                        "AST": "Assistências"
                    }
                ))

                # Gráfico de Pontos
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=jogos_contra_adversario["GAME_DATE"],
                    y=jogos_contra_adversario["PTS"],
                    text=jogos_contra_adversario["PTS"],
                    textposition="outside",
                    name="Pontos"
                ))
                fig.update_layout(
                    title=f"Pontuação de {jogador_selecionado['full_name']} Contra {adversario['full_name']}",
                    xaxis_title="Data",
                    yaxis_title="Pontos",
                    template="plotly_dark"
                )
                st.plotly_chart(fig)

                # Gráfico de Rebotes
                fig_rebotes = go.Figure()
                fig_rebotes.add_trace(go.Bar(
                    x=jogos_contra_adversario["GAME_DATE"],
                    y=jogos_contra_adversario["REB"],
                    text=jogos_contra_adversario["REB"],
                    textposition="outside",
                    name="Rebotes"
                ))
                fig_rebotes.update_layout(
                    title=f"Rebotes de {jogador_selecionado['full_name']} Contra {adversario['full_name']}",
                    xaxis_title="Data",
                    yaxis_title="Rebotes",
                    template="plotly_dark"
                )
                st.plotly_chart(fig_rebotes)

                # Gráfico de Assistências
                fig_assist = go.Figure()
                fig_assist.add_trace(go.Bar(
                    x=jogos_contra_adversario["GAME_DATE"],
                    y=jogos_contra_adversario["AST"],
                    text=jogos_contra_adversario["AST"],
                    textposition="outside",
                    name="Assistências"
                ))
                fig_assist.update_layout(
                    title=f"Assistências de {jogador_selecionado['full_name']} Contra {adversario['full_name']}",
                    xaxis_title="Data",
                    yaxis_title="Assistências",
                    template="plotly_dark"
                )
                st.plotly_chart(fig_assist)
            else:
                st.write(f"Nenhum jogo encontrado de {jogador_selecionado['full_name']} contra {adversario['full_name']}.")


# Navegação entre páginas
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Escolha uma página", ["Times", "Jogadores", "Análise Contra Adversário"])

if pagina == "Times":
    pagina_times()
elif pagina == "Jogadores":
    pagina_jogadores()
elif pagina == "Análise Contra Adversário":
    pagina_analise_contra_adversario()
