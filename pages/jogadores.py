import streamlit as st
from utils.api_utils import obter_dados_times, obter_elenco_time, obter_ultimos_jogos
from utils.image_utils import carregar_foto_jogador
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import leagueleaders
import plotly.graph_objects as go
import base64
import os

FOTOS_DIR = "fotos"

def obter_posicao_no_ranking(nome_jogador, estatistica, season="2023-24"):
    try:
        leaders = leagueleaders.LeagueLeaders(season=season, stat_category_abbreviation=estatistica).get_data_frames()[0]
        leaders["RANK"] = leaders.index + 1  # Adiciona a posição no ranking
        
        jogador_info = leaders[leaders["PLAYER"] == nome_jogador]
        if not jogador_info.empty:
            return jogador_info["RANK"].values[0]
        return None
    except Exception as e:
        return f"Erro ao buscar ranking: {e}"

def carregar_foto_jogador(nome_jogador):
    nome_formatado = nome_jogador.lower().replace(" ", "-") + ".png"
    caminho_foto = os.path.join(FOTOS_DIR, nome_formatado)

    if os.path.exists(caminho_foto):  
        with open(caminho_foto, "rb") as img_file:
            base64_str = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{base64_str}"
    
    return "https://via.placeholder.com/150"

def pagina_jogadores():
    st.header("👨‍🦰 Estatísticas dos Jogadores")

    query_params = st.query_params
    team_name = query_params.get("team", [""])[0]
    player_name = query_params.get("player", [""])[0]

    with st.spinner("Carregando dados dos times..."):
        dados_times = obter_dados_times()

    if not dados_times:
        st.error("Não foi possível carregar os dados dos times.")
        return

    col1, col2 = st.columns(2)

    with col1:
        time_selecionado = st.selectbox(
            "Escolha um time", 
            dados_times, 
            format_func=lambda x: x['full_name'], 
            index=[x['full_name'] for x in dados_times].index(team_name) if team_name in [x['full_name'] for x in dados_times] else 0
        )

    if time_selecionado:
        with st.spinner(f"Carregando elenco do time {time_selecionado['full_name']}..."):
            equipe_id = time_selecionado["id"]
            time_nome = time_selecionado["full_name"]
            elenco = obter_elenco_time(equipe_id)
            jogadores = {jogador['PLAYER']: jogador['PLAYER_ID'] for _, jogador in elenco.iterrows()}

        with col2:
            jogador_selecionado = st.selectbox(
                "Selecione um jogador", 
                list(jogadores.keys()), 
                index=list(jogadores.keys()).index(player_name) if player_name in jogadores.keys() else 0
            )

        if jogador_selecionado:
            with st.spinner(f"Carregando dados do jogador {jogador_selecionado}..."):
                player_id = jogadores[jogador_selecionado]
                ultimos_jogos = obter_ultimos_jogos(player_id)

            st.markdown(f"### Estatísticas de {jogador_selecionado}")

            col1, col2 = st.columns([1, 3])
            with col1:
                foto = carregar_foto_jogador(jogador_selecionado)
                st.markdown(f'<img src="{foto}" width="150">', unsafe_allow_html=True)

            with col2:
                st.write(f"**Time:** {time_nome}")

            # Seleção de estatísticas
            metricas = {
                "PTS": "Pontos",
                "AST": "Assistências",
                "REB": "Rebotes",
                "STL": "Roubos de Bola",
                "BLK": "Bloqueios",
                "TOV": "Turnovers",
                "PF": "Faltas Pessoais"
            }
            metrica_selecionada = st.selectbox(
                "Selecione a métrica para o gráfico", 
                options=metricas.keys(), 
                format_func=lambda x: metricas[x]
            )

            # Obter posição do jogador no ranking da estatística escolhida
            with st.spinner(f"Buscando ranking de {jogador_selecionado} em {metricas[metrica_selecionada]}..."):
                posicao_ranking = obter_posicao_no_ranking(jogador_selecionado, metrica_selecionada)

            if posicao_ranking:
                st.write(f"📊 **Posição no ranking de {metricas[metrica_selecionada]}:** {posicao_ranking}º")
            else:
                st.write("🔍 Jogador não encontrado no ranking.")

            # Mostrar estatísticas gráficas
            if not ultimos_jogos.empty:
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
                    title=f"{metricas[metrica_selecionada]} de {jogador_selecionado}",
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
