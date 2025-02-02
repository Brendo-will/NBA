import streamlit as st
import pandas as pd
import os
import base64
from nba_api.stats.endpoints import leaguedashteamstats

st.set_page_config(page_title="NBA Dashboard", layout="wide")

LOGOS_DIR = "Logos"

# Função para converter imagens para Base64 (para exibir corretamente no HTML)
def carregar_logo_base64(nome_time):
    nome_formatado = nome_time.lower().replace(" ", "_") + ".png"
    caminho_logo = os.path.join(LOGOS_DIR, nome_formatado)

    if os.path.exists(caminho_logo):
        with open(caminho_logo, "rb") as img_file:
            base64_str = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{base64_str}"
    return None

# Função para obter os dados médios por jogo da temporada atual
def obter_dados_por_jogo():
    ranking = leaguedashteamstats.LeagueDashTeamStats(
        season="2024-25", 
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame"
    ).get_data_frames()[0]

    # Selecionar as colunas relevantes
    colunas_desejadas = [
        "TEAM_NAME", "GP", "W", "L", "MIN", "PTS", 
        "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", 
        "FT_PCT", "OREB", "DREB", "REB", "AST", "TOV", "STL", 
        "BLK", "BLKA", "PF", "PFD", "PLUS_MINUS"
    ]
    colunas_disponiveis = [col for col in colunas_desejadas if col in ranking.columns]

    df = ranking[colunas_disponiveis].reset_index(drop=True)

    # Ordenar pelo número de vitórias
    df = df.sort_values(by="W", ascending=False)

    return df


# Layout principal
st.title("🏀 NBA Dashboard - Estatísticas Médias por Jogo - Temporada 2024-25")

# Obtendo os dados médios por jogo
ranking_geral = obter_dados_por_jogo()

# Criando uma nova coluna para armazenar os logos em Base64
ranking_geral["Logo_Base64"] = ranking_geral["TEAM_NAME"].apply(carregar_logo_base64)

# Criando a tabela com HTML e CSS
st.markdown("""
<style>
    .fixed-table {
        width: 100%;
        border-collapse: collapse;
    }
    .fixed-table thead {
        position: sticky;
        top: 0;
        background-color: white;
        z-index: 1;
    }
    .fixed-table th {
        background-color: #f4f4f4;
        text-align: center;
        padding: 8px;
    }
    .fixed-table td {
        text-align: center;
        padding: 8px;
    }
    .team-name {
        text-align: left;
    }
    img {
        vertical-align: middle;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Criando a tabela no formato correto (com links clicáveis)
tabela_html = "<table class='fixed-table'><thead><tr>"
tabela_html += "<th>#</th><th>TEAM</th><th>GP</th><th>W</th><th>L</th><th>MIN</th><th>PTS</th>"
tabela_html += "<th>FGM</th><th>FGA</th><th>FG%</th><th>3PM</th><th>3PA</th><th>3P%</th><th>FTM</th><th>FTA</th>"
tabela_html += "<th>FT%</th><th>OREB</th><th>DREB</th><th>REB</th><th>AST</th><th>TOV</th><th>STL</th>"
tabela_html += "<th>BLK</th><th>BLKA</th><th>PF</th><th>PFD</th><th>+/-</th></tr></thead><tbody>"

# Populando a tabela com os dados
for i, row in ranking_geral.iterrows():
    # Criando links para o logo e o nome do time
    team_link = f"/team_page?team={row['TEAM_NAME']}"
    logo_html = f'<a href="{team_link}" target="_blank"><img src="{row["Logo_Base64"]}" width="25"></a>' if row["Logo_Base64"] else ""
    name_html = f'<a href="{team_link}" target="_blank">{row["TEAM_NAME"]}</a>'

    tabela_html += "<tr>"
    tabela_html += f"<td>{i+1}</td>"
    tabela_html += f'<td class="team-name">{logo_html} {name_html}</td>'
    tabela_html += "".join([f"<td>{row[col] if col in ranking_geral.columns else '-'}</td>" for col in [
        "GP", "W", "L", "MIN", "PTS", "FGM", "FGA", "FG_PCT",
        "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB",
        "AST", "TOV", "STL", "BLK", "BLKA", "PF", "PFD", "PLUS_MINUS"
    ]])
    tabela_html += "</tr>"

tabela_html += "</tbody></table>"

# Exibir a tabela
st.markdown(tabela_html, unsafe_allow_html=True)
