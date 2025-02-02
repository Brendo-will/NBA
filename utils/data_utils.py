# utils/data_utils.py
import pandas as pd

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
