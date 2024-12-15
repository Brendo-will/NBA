import json
import streamlit as st
import pandas as pd
import os

# Configuração do Streamlit
st.set_page_config(page_title="Estatísticas de Jogadores da NBA", layout="wide")
st.title("🏀 Estatísticas de Jogadores da NBA")

# Nome do arquivo JSON na pasta raiz
arquivo_json = "Jogadores_Resultado_Completo.json"

# Mapeamento de siglas para nomes completos dos times
nomes_times = {
    "MIL": "Milwaukee Bucks",
    "DEN": "Denver Nuggets",
    "CHA": "Charlotte Hornets",
    "OKC": "Oklahoma City Thunder",
    "BOS": "Boston Celtics",
    "DAL": "Dallas Mavericks",
    "LAL": "Los Angeles Lakers",
    "MIN": "Minnesota Timberwolves",
    "SAC": "Sacramento Kings",
    "PHX": "Phoenix Suns",
    "NYK": "New York Knicks",
    "BKN": "Brooklyn Nets",
    "PHI": "Philadelphia 76ers",
    "MIA": "Miami Heat",
    "CLE": "Cleveland Cavaliers",
    "GSW": "Golden State Warriors",
    "CHI": "Chicago Bulls",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "WAS": "Washington Wizards",
    "ATL": "Atlanta Hawks",
    "NOP": "New Orleans Pelicans",
    "UTA": "Utah Jazz",
    "HOU": "Houston Rockets",
    "MEM": "Memphis Grizzlies",
    "POR": "Portland Trail Blazers",
    "LAC": "Los Angeles Clippers",
    "IND": "Indiana Pacers",
    "DET": "Detroit Pistons",
    "ORL": "Orlando Magic"
}


# Verificar se o arquivo existe
if os.path.exists(arquivo_json):
    try:
        # Carregar dados do JSON
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            jogadores_data = json.load(f)

        # Verificar se os campos necessários estão no JSON
        if not all(key in jogadores_data[0] for key in ['Time', 'Nome Completo']):
            st.error("O arquivo JSON não contém os campos necessários ('Time', 'Nome Completo').")
            st.stop()

        # Criar listas de times e status
        times_disponiveis = sorted(set(jogador['Time'] for jogador in jogadores_data))
        # Remover 'Game Dates' e 'Matchups' das estatísticas disponíveis
        status_disponiveis = [key for key in jogadores_data[0].keys() if key not in ['Time', 'Nome Completo', 'Game Dates', 'Matchups']]

        # Sidebar - Filtros
        st.sidebar.header("Filtros")
        time_selecionado = st.sidebar.selectbox("Escolha um time", nomes_times.keys(), format_func=lambda x: nomes_times[x])
        status_selecionado = st.sidebar.selectbox("Escolha uma estatística", status_disponiveis)

        # Determinar o valor máximo para o filtro baseado nos dados
        max_valor = max(
            max((valor for valor in jogador.get(status_selecionado, []) if isinstance(valor, (int, float))), default=0)
            for jogador in jogadores_data
        )
        valor_referencia = st.sidebar.number_input("Escolha um valor de referência", min_value=1, max_value=max_valor, value=5)

        # Filtrar jogadores do time selecionado
        jogadores_do_time = [jogador for jogador in jogadores_data if jogador['Time'] == time_selecionado]

        st.subheader(f"📊 Estatística Selecionada: {status_selecionado}")
        resultados = []

        # Exibir informações do jogador
        for jogador in jogadores_do_time:
            nome_jogador = jogador['Nome Completo']
            valores_status = jogador.get(status_selecionado, [])
            game_dates = jogador.get("Game Dates", [])
            matchups = jogador.get("Matchups", [])

            # Verificar se há dados suficientes
            if not valores_status or not all(isinstance(val, (int, float)) for val in valores_status):
                st.write(f"**{nome_jogador}** não possui dados suficientes para {status_selecionado}.")
                continue

            # Calcular média e contagem de partidas que bateram o valor de referência
            media_status = round(pd.Series(valores_status).mean(), 2)
            qtd_batidas = sum(1 for valor in valores_status if valor >= valor_referencia)

            # Caminho da foto do jogador
            caminho_imagem = f"fotos/{nome_jogador.lower().replace(' ', '-')}.png"
            if not os.path.exists(caminho_imagem):
                caminho_imagem = "https://via.placeholder.com/150"  # Imagem padrão

            # Exibir informações no Streamlit
            st.markdown("----")
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(caminho_imagem, width=150)
            with col2:
                st.subheader(nome_jogador)
                nome_time_completo = nomes_times.get(jogador['Time'], jogador['Time'])
                st.write(f"**Time:** {nome_time_completo}")
                st.write(f"**Média nos Últimos Jogos ({status_selecionado}):** {media_status}")
                st.write(f"**Partidas que Bateram o Valor {valor_referencia}:** {qtd_batidas}")

            # Exibir tabela com os valores dos últimos jogos
            st.write(f"**Últimos Jogos ({status_selecionado}):**")
            df_jogos = pd.DataFrame({
                "Game Date": game_dates,
                "Matchup": matchups,
                status_selecionado: valores_status
            })
            st.dataframe(df_jogos, use_container_width=True)

            # Salvar resultado na lista para referência
            resultados.append({
                "Jogador": nome_jogador,
                "Média": media_status,
                "Partidas que Bateram o Valor": qtd_batidas
            })

       
    except KeyError as e:
        st.error(f"Erro ao acessar campo no JSON: {e}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
else:
    st.error(f"O arquivo '{arquivo_json}' não foi encontrado na pasta raiz. Certifique-se de que o arquivo está no local correto.")
