import streamlit as st
import pandas as pd
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import commonteamroster, playergamelog, teamgamelog, leaguegamefinder
from PIL import Image
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# Configurações de diretório
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGOS_DIR = os.path.join(BASE_DIR, "Logos")
IMAGES_DIR = os.path.join(BASE_DIR, "fotos")

# URLs de imagens padrão
DEFAULT_IMAGE = "https://via.placeholder.com/150"
DEFAULT_LOGO = "https://via.placeholder.com/150"

# Função para obter dados dos times via API
@st.cache_data
def obter_dados_times():
    try:
        return teams.get_teams()
    except Exception as e:
        st.error(f"Erro ao obter dados dos times: {e}")
        return []

# Função para obter dados dos jogadores via API
@st.cache_data
def obter_dados_jogadores():
    try:
        return players.get_players()
    except Exception as e:
        st.error(f"Erro ao obter dados dos jogadores: {e}")
        return []

# Função para obter o elenco atual de um time via API
@st.cache_data
def obter_elenco_time(team_id):
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
        return roster
    except Exception as e:
        st.error(f"Erro ao obter elenco do time: {e}")
        return pd.DataFrame()

# Função para obter as últimas 10 partidas de um jogador via API
@st.cache_data
def obter_ultimos_jogos(player_id):
    try:
        log = playergamelog.PlayerGameLog(player_id=player_id, season="2024-25").get_data_frames()[0]
        return log.head(10)
    except Exception as e:
        st.error(f"Erro ao obter últimos jogos do jogador: {e}")
        return pd.DataFrame()

# Função para obter o histórico de jogos de um jogador para várias temporadas
@st.cache_data
def obter_historico_por_temporadas(player_id, temporadas):
    todos_jogos = []
    for temporada in temporadas:
        try:
            log = playergamelog.PlayerGameLog(player_id=player_id, season=temporada).get_data_frames()[0]
            todos_jogos.append(log)
        except Exception as e:
            st.warning(f"Erro ao buscar dados para a temporada {temporada}: {e}")
    return pd.concat(todos_jogos, ignore_index=True) if todos_jogos else pd.DataFrame()

# Função para obter o log de jogos de um time via API
@st.cache_data
def obter_jogos_time(team_id):
    try:
        gamelog = teamgamelog.TeamGameLog(team_id=team_id, season="2024-25").get_data_frames()[0]
        return gamelog
    except Exception as e:
        st.error(f"Erro ao obter jogos do time: {e}")
        return pd.DataFrame()

# Função para carregar o logo do time
def carregar_logo_time(nome_time):
    nome_formatado = nome_time.strip().upper().replace(" ", "_").replace("-", "_")
    for ext in [".png", ".jpg"]:
        logo_path = os.path.join(LOGOS_DIR, f"{nome_formatado}{ext}")
        if os.path.exists(logo_path):
            return logo_path
    st.warning(f"Logo não encontrado para o time: {nome_time}")
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

# Função para calcular a porcentagem de pontos de 2 e 3 pontos de um jogador
def calcular_porcentagem_pontos_jogador(player_id, season):
    player_log = playergamelog.PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]
    
    # Calcular pontos de 2 e 3 pontos
    player_log['PTS_2P'] = (player_log['FGM'] - player_log['FG3M']) * 2  # Pontos de 2 pontos
    player_log['PTS_3P'] = player_log['FG3M'] * 3  # Pontos de 3 pontos
    
    # Calcular porcentagens
    total_points = player_log['PTS'].sum()
    pts_2p = player_log['PTS_2P'].sum()
    pts_3p = player_log['PTS_3P'].sum()
    
    perc_2p = (pts_2p / total_points) * 100 if total_points > 0 else 0
    perc_3p = (pts_3p / total_points) * 100 if total_points > 0 else 0
    
    return perc_2p, perc_3p

# Função para calcular a porcentagem de pontos concedidos no garrafão e de 3 pontos pelo time adversário
def calcular_porcentagem_pontos_adversario(team_id, season):
    team_log = teamgamelog.TeamGameLog(team_id=team_id, season=season).get_data_frames()[0]
    
    # Calcular pontos concedidos de 2 e 3 pontos
    team_log['PTS_CONCEDIDOS_2P'] = (team_log['OPP_FGM'] - team_log['OPP_FG3M']) * 2  # Pontos de 2 pontos concedidos
    team_log['PTS_CONCEDIDOS_3P'] = team_log['OPP_FG3M'] * 3  # Pontos de 3 pontos concedidos
    
    # Calcular porcentagens
    total_points_conceded = team_log['OPP_PTS'].sum()
    pts_conceded_2p = team_log['PTS_CONCEDIDOS_2P'].sum()
    pts_conceded_3p = team_log['PTS_CONCEDIDOS_3P'].sum()
    
    perc_conceded_2p = (pts_conceded_2p / total_points_conceded) * 100 if total_points_conceded > 0 else 0
    perc_conceded_3p = (pts_conceded_3p / total_points_conceded) * 100 if total_points_conceded > 0 else 0
    
    return perc_conceded_2p, perc_conceded_3p

# Função para obter os jogos dos próximos 7 dias
@st.cache_data
@st.cache_data
def obter_proximos_jogos():
    try:
        # URL da API da NBA que retorna o calendário da temporada 2024-25
        url = 'https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2024/league/00_full_schedule.json'
        response = requests.get(url)
        data = response.json()

        jogos_futuros = []
        hoje = datetime.now()

        # Percorre os dados da API e filtra os jogos futuros
        for mes in data['lscd']:  # Lista de meses
            for jogo in mes['mscd']['g']:  # Lista de jogos no mês
                data_jogo = datetime.strptime(jogo['gdte'], '%Y-%m-%d')
                if data_jogo >= hoje:  # Pegamos apenas os jogos que ainda não aconteceram
                    jogos_futuros.append({
                        'Data': data_jogo.strftime('%d/%m/%Y'),  # Formato de data ajustado
                        'Confronto': f"{jogo['v']['tn']} @ {jogo['h']['tn']}",
                        'Time Visitante': jogo['v']['tn'],
                        'Time da Casa': jogo['h']['tn']
                    })

        # Converte a lista para DataFrame
        proximos_jogos_df = pd.DataFrame(jogos_futuros)

        return proximos_jogos_df

    except Exception as e:
        st.error(f"Erro ao obter os próximos jogos: {e}")
        return pd.DataFrame(columns=["Data", "Confronto", "Time Visitante", "Time da Casa"])

# Página 4: Próximos Jogos
def pagina_proximos_jogos():
    st.header("📅 Próximos Jogos da NBA")
    with st.spinner("Carregando os próximos jogos..."):
        proximos_jogos = obter_proximos_jogos()

    if not proximos_jogos.empty:
        st.subheader("Jogos dos Próximos Dias")
        st.dataframe(proximos_jogos)
    else:
        st.write("Nenhum jogo encontrado para os próximos dias.")



# Página 1: Estatísticas de Times
def pagina_times():
    st.header("📊 Estatísticas dos Times")
    with st.spinner("Carregando dados dos times..."):
        dados_times = obter_dados_times()

    if not dados_times:
        st.error("Não foi possível carregar os dados dos times.")
        return

    # Selecionar dois times
    time_selecionado_1 = st.selectbox("Escolha o primeiro time", dados_times, format_func=lambda x: x['full_name'], key="time1")
    time_selecionado_2 = st.selectbox("Escolha o segundo time", dados_times, format_func=lambda x: x['full_name'], key="time2")

    if time_selecionado_1 and time_selecionado_2:
        # Dados do primeiro time
        with st.spinner(f"Carregando dados do time {time_selecionado_1['full_name']}..."):
            team_id_1 = time_selecionado_1["id"]
            jogos_1 = obter_jogos_time(team_id_1)
            estatisticas_casa_1 = calcular_estatisticas(jogos_1, casa=True)
            estatisticas_fora_1 = calcular_estatisticas(jogos_1, casa=False)

        # Dados do segundo time
        with st.spinner(f"Carregando dados do time {time_selecionado_2['full_name']}..."):
            team_id_2 = time_selecionado_2["id"]
            jogos_2 = obter_jogos_time(team_id_2)
            estatisticas_casa_2 = calcular_estatisticas(jogos_2, casa=True)
            estatisticas_fora_2 = calcular_estatisticas(jogos_2, casa=False)

        # Layout lado a lado
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"📊 {time_selecionado_1['full_name']}")
            logo_path_1 = carregar_logo_time(time_selecionado_1["full_name"])
            st.image(logo_path_1, width=150)

            st.markdown("### 🏟️ Jogos em Casa")
            for key, value in estatisticas_casa_1.items():
                st.write(f"**{key}:** {value:.2f}" if isinstance(value, float) else f"**{key}:** {value}")

            st.markdown("### ✈️ Jogos Fora de Casa")
            for key, value in estatisticas_fora_1.items():
                st.write(f"**{key}:** {value:.2f}" if isinstance(value, float) else f"**{key}:** {value}")

        with col2:
            st.subheader(f"📊 {time_selecionado_2['full_name']}")
            logo_path_2 = carregar_logo_time(time_selecionado_2["full_name"])
            st.image(logo_path_2, width=150)

            st.markdown("### ✈️ Jogos Fora de Casa")
            for key, value in estatisticas_fora_2.items():
                st.write(f"**{key}:** {value:.2f}" if isinstance(value, float) else f"**{key}:** {value}")

            st.markdown("### 🏟️ Jogos em Casa")
            for key, value in estatisticas_casa_2.items():
                st.write(f"**{key}:** {value:.2f}" if isinstance(value, float) else f"**{key}:** {value}")

# Página 2: Estatísticas dos Jogadores
def pagina_jogadores():
    st.header("👨‍🦰 Estatísticas dos Jogadores")
    with st.spinner("Carregando dados dos times..."):
        dados_times = obter_dados_times()

    if not dados_times:
        st.error("Não foi possível carregar os dados dos times.")
        return

    time_selecionado = st.selectbox("Escolha um time", dados_times, format_func=lambda x: x['full_name'])

    if time_selecionado:
        with st.spinner(f"Carregando elenco do time {time_selecionado['full_name']}..."):
            equipe_id = time_selecionado["id"]
            time_nome = time_selecionado["full_name"]
            elenco = obter_elenco_time(equipe_id)
            jogadores = {jogador['PLAYER']: jogador['PLAYER_ID'] for _, jogador in elenco.iterrows()}

        jogador_selecionado = st.selectbox("Selecione um jogador", list(jogadores.keys()))
        if jogador_selecionado:
            with st.spinner(f"Carregando dados do jogador {jogador_selecionado}..."):
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
        team_id = adversario['id']
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

                # Nova Seção: Análise de Porcentagem de Pontos
                st.subheader("📊 Análise de Porcentagem de Pontos")
                
                @st.cache_data
                def calcular_porcentagem_pontos_adversario(team_id, season):
                    try:
                        team_log = teamgamelog.TeamGameLog(team_id=team_id, season=season).get_data_frames()[0]

                        # Calculando pontos concedidos no garrafão e de 3 pontos
                        team_log['PTS_3P_CONCEDIDOS'] = team_log['FG3M'] * 3  # Total de pontos do adversário vindo de 3 pontos
                        team_log['PTS_2P_CONCEDIDOS'] = (team_log['FGM'] - team_log['FG3M']) * 2  # Total de pontos de 2 pontos

                        # Calculando a porcentagem
                        total_points_conceded = team_log['PTS'].sum()
                        if total_points_conceded > 0:
                            perc_conceded_2p = (team_log['PTS_2P_CONCEDIDOS'].sum() / total_points_conceded) * 100
                            perc_conceded_3p = (team_log['PTS_3P_CONCEDIDOS'].sum() / total_points_conceded) * 100
                        else:
                            perc_conceded_2p, perc_conceded_3p = 0, 0

                        return perc_conceded_2p, perc_conceded_3p

                    except Exception as e:
                        st.error(f"Erro ao calcular estatísticas do adversário: {e}")
                        return 0, 0


                # Calcular porcentagens do jogador
                perc_2p_jogador, perc_3p_jogador = calcular_porcentagem_pontos_jogador(player_id, temporadas_selecionadas[0])
                st.write(f"**Porcentagem de pontos de 2 pontos do jogador:** {perc_2p_jogador:.2f}%")
                st.write(f"**Porcentagem de pontos de 3 pontos do jogador:** {perc_3p_jogador:.2f}%")

                # Calcular porcentagens do time adversário
                perc_conceded_2p_adversario, perc_conceded_3p_adversario = calcular_porcentagem_pontos_adversario(team_id, temporadas_selecionadas[0])
                st.write(f"**Porcentagem de pontos de 2 pontos concedidos pelo adversário:** {perc_conceded_2p_adversario:.2f}%")
                st.write(f"**Porcentagem de pontos de 3 pontos concedidos pelo adversário:** {perc_conceded_3p_adversario:.2f}%")

                # Comparação
                if perc_2p_jogador > perc_conceded_2p_adversario:
                    st.success("✅ O jogador pontua mais no garrafão do que o time adversário costuma conceder.")
                else:
                    st.warning("⚠️ O time adversário é eficiente em defender o garrafão contra esse jogador.")

                if perc_3p_jogador > perc_conceded_3p_adversario:
                    st.success("✅ O jogador pontua mais de 3 pontos do que o time adversário costuma conceder.")
                else:
                    st.warning("⚠️ O time adversário é eficiente em defender arremessos de 3 pontos contra esse jogador.")

            else:
                st.write(f"Nenhum jogo encontrado de {jogador_selecionado['full_name']} contra {adversario['full_name']}.")

# Navegação entre páginas
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Escolha uma página", ["Times", "Jogadores", "Análise Contra Adversário", "Próximos Jogos"])

if pagina == "Times":
    pagina_times()
elif pagina == "Jogadores":
    pagina_jogadores()
elif pagina == "Análise Contra Adversário":
    pagina_analise_contra_adversario()
elif pagina == "Próximos Jogos":
    pagina_proximos_jogos()
