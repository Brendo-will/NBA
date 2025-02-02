import pandas as pd
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import commonteamroster, playergamelog, teamgamelog

def obter_dados_times():
    return teams.get_teams()

def obter_dados_jogadores():
    return players.get_players()

def obter_elenco_time(team_id):
    return commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]

def obter_ultimos_jogos(player_id):
    return playergamelog.PlayerGameLog(player_id=player_id, season="2024-25").get_data_frames()[0]

def obter_historico_por_temporadas(player_id, temporadas):
    historico = []
    for temporada in temporadas:
        try:
            log = playergamelog.PlayerGameLog(player_id=player_id, season=temporada).get_data_frames()[0]
            historico.append(log)
        except:
            pass
    return pd.concat(historico, ignore_index=True) if historico else pd.DataFrame()

def obter_jogos_time(team_id):
    return teamgamelog.TeamGameLog(team_id=team_id, season="2024-25").get_data_frames()[0]
