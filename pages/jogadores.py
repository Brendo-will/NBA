import streamlit as st
from utils.api_utils import obter_dados_times, obter_elenco_time, obter_ultimos_jogos
from utils.image_utils import carregar_foto_jogador
from nba_api.stats.endpoints import playergamelog
import plotly.graph_objects as go
from utils.api_utils import obter_dados_jogadores, obter_dados_times, obter_historico_por_temporadas
import base64
import os

FOTOS_DIR = "fotos"

def carregar_foto_jogador(nome_jogador):
    nome_formatado = nome_jogador.lower().replace(" ", "-") + ".png"
    caminho_foto = os.path.join(FOTOS_DIR, nome_formatado)

    if os.path.exists(caminho_foto):  # Confirma se o arquivo existe
        with open(caminho_foto, "rb") as img_file:
            base64_str = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{base64_str}"
    
    # Se a imagem não for encontrada, use um placeholder online
    return "https://via.placeholder.com/150"

def calcular_porcentagem_pontos_jogador(player_id, season):
    """
    Calcula a porcentagem de pontos de 2 e 3 pontos de um jogador.
    """
    try:
        player_log = playergamelog.PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]
        
        player_log['PTS_2P'] = (player_log['FGM'] - player_log['FG3M']) * 2  # Pontos de 2 pontos
        player_log['PTS_3P'] = player_log['FG3M'] * 3  # Pontos de 3 pontos
        
        total_points = player_log['PTS'].sum()
        pts_2p = player_log['PTS_2P'].sum()
        pts_3p = player_log['PTS_3P'].sum()
        
        perc_2p = (pts_2p / total_points) * 100 if total_points > 0 else 0
        perc_3p = (pts_3p / total_points) * 100 if total_points > 0 else 0
        
        return perc_2p, perc_3p
    except Exception as e:
        st.write(f"Erro ao calcular porcentagens: {e}")
        return 0, 0

def pagina_jogadores():
    st.header("👨‍🦰 Estatísticas dos Jogadores")
    
    # Capturar os parâmetros de consulta
    query_params = st.query_params
    team_name = query_params.get("team", [""])[0]
    player_name = query_params.get("player", [""])[0]


    with st.spinner("Carregando dados dos times..."):
        dados_times = obter_dados_times()

    if not dados_times:
        st.error("Não foi possível carregar os dados dos times.")
        return

    # Selecionar o time com base no parâmetro de consulta
    time_selecionado = st.selectbox("Escolha um time", dados_times, format_func=lambda x: x['full_name'], index=[x['full_name'] for x in dados_times].index(team_name) if team_name in [x['full_name'] for x in dados_times] else 0)

    if time_selecionado:
        with st.spinner(f"Carregando elenco do time {time_selecionado['full_name']}..."):
            equipe_id = time_selecionado["id"]
            time_nome = time_selecionado["full_name"]
            elenco = obter_elenco_time(equipe_id)
            jogadores = {jogador['PLAYER']: jogador['PLAYER_ID'] for _, jogador in elenco.iterrows()}

        # Selecionar o jogador com base no parâmetro de consulta
        jogador_selecionado = st.selectbox("Selecione um jogador", list(jogadores.keys()), index=list(jogadores.keys()).index(player_name) if player_name in jogadores.keys() else 0)

        if jogador_selecionado:
            with st.spinner(f"Carregando dados do jogador {jogador_selecionado}..."):
                player_id = jogadores[jogador_selecionado]
                ultimos_jogos = obter_ultimos_jogos(player_id)

            st.markdown(f"### Estatísticas de {jogador_selecionado} - Últimas 10 Partidas")
             
            col1, col2 = st.columns([1, 3])
            with col1:
                foto = carregar_foto_jogador(jogador_selecionado)
                st.markdown(f'<img src="{foto}" width="150">', unsafe_allow_html=True)

            with col2:
                st.write(f"**Time:** {time_nome}")

                # Seletor de temporadas para estatísticas gerais do jogador
                temporadas = ["2021-22", "2022-23", "2023-24", "2024-25"]
                temporadas_selecionadas = st.multiselect(
                    "Selecione as temporadas", temporadas, default=temporadas, key="temporadas_estatisticas"
                )

                perc_2p, perc_3p = calcular_porcentagem_pontos_jogador(player_id, temporadas_selecionadas)
                st.write(f"🔢 **Porcentagem de pontos de 2 pontos:** {perc_2p:.2f}%")
                st.write(f"🎯 **Porcentagem de pontos de 3 pontos:** {perc_3p:.2f}%")  

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

        else:
            st.write("O elenco deste time não está disponível.")     

if __name__ == "__main__":
    pagina_jogadores()
