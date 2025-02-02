import streamlit as st
from utils.api_utils import obter_dados_jogadores, obter_dados_times, obter_historico_por_temporadas
import plotly.graph_objects as go

st.header("📈 Análise Contra Adversário")

jogadores = obter_dados_jogadores()
times = obter_dados_times()

jogador_selecionado = st.selectbox("Escolha um jogador", jogadores, format_func=lambda x: x["full_name"])
adversario = st.selectbox("Escolha um adversário", times, format_func=lambda x: x["full_name"])

temporadas = ["2021-22", "2022-23", "2023-24", "2024-25"]
temporadas_selecionadas = st.multiselect("Selecione as temporadas", temporadas, default=temporadas)

if st.button("Analisar"):
    player_id = jogador_selecionado["id"]
    adversario_abbr = adversario["abbreviation"]
    historico = obter_historico_por_temporadas(player_id, temporadas_selecionadas)

    jogos = historico[historico["MATCHUP"].str.contains(adversario_abbr)]
    
    if not jogos.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=jogos["GAME_DATE"], y=jogos["PTS"], text=jogos["PTS"], textposition="outside"
        ))
        st.plotly_chart(fig)
        st.dataframe(jogos[["GAME_DATE", "MATCHUP", "PTS", "REB", "AST"]])
