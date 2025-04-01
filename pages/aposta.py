import streamlit as st
import sys
import os
import time
import json
import queue
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurações globais
NBA_API_TIMEOUT = 60  # Timeout aumentado para 60 segundos
MAX_RETRIES = 5       # Número máximo de tentativas aumentado
CACHE_DIR = Path("nba_cache")
CACHE_DIR.mkdir(exist_ok=True)
background_results = queue.Queue()

# Configuração de sessão com retry robusto
def create_nba_session():
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504, 522, 524],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=10,
        pool_maxsize=10
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Adiciona o caminho do diretório pai para acessar os módulos customizados
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.jogadores import get_jogadores_time, obter_temporada_atual
from pages.times import get_jogos_do_dia
from nba_api.stats.endpoints import PlayerGameLog, TeamGameLog
from nba_api.stats.library.http import NBAStatsHTTP

# Classe HTTP customizada com tratamento robusto de erros
# Classe HTTP customizada com tratamento robusto de erros
class RobustNBAStatsHTTP(NBAStatsHTTP):
    def __init__(self):
        super().__init__()
        self._session = create_nba_session()
        self._timeout = NBA_API_TIMEOUT
    
    def send_api_request(self, *args, **kwargs):
        kwargs['timeout'] = self._timeout
        try:
            response = super().send_api_request(*args, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            st.warning(f"Erro na requisição à API NBA: {str(e)}")
            raise

# Aplica a configuração customizada
PlayerGameLog._nba_stats_http = RobustNBAStatsHTTP()
TeamGameLog._nba_stats_http = RobustNBAStatsHTTP()

# --- Decorators e Funções Auxiliares ---
def with_loading(func):
    """Decorator para mostrar spinner durante operações demoradas"""
    def wrapper(*args, **kwargs):
        with st.spinner("Carregando dados..."):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                st.error(f"Erro durante a operação: {str(e)}")
                return None
    return wrapper

def get_cache_filename(endpoint, params):
    """Gera nome de arquivo único para cache baseado nos parâmetros"""
    param_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()))
    return CACHE_DIR / f"{endpoint}_{param_str}.json"

def clean_old_cache(max_age_days=7):
    """Remove arquivos de cache antigos"""
    now = time.time()
    for cache_file in CACHE_DIR.glob("*.json"):
        file_age = now - cache_file.stat().st_mtime
        if file_age > max_age_days * 86400:
            try:
                cache_file.unlink()
            except:
                pass

# --- Funções Principais com Cache e Tratamento de Erros ---
def safe_api_call(func, params):
    """Executa chamada à API com tratamento robusto de erros"""
    try:
        return func(params)
    except requests.exceptions.Timeout:
        st.warning("Timeout ao acessar a API NBA. Tentando novamente...")
        time.sleep(2)  # Backoff simples
        try:
            return func(params)
        except Exception as e:
            st.error(f"Falha após retentativa: {str(e)}")
            return None
    except Exception as e:
        st.error(f"Erro inesperado na API: {str(e)}")
        return None

def cached_api_call(endpoint, func, params, expire_hours=24):
    """Executa chamada à API com cache persistente"""
    cache_file = get_cache_filename(endpoint, params)
    
    # Tenta ler do cache se existir e for recente
    if cache_file.exists():
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age < expire_hours * 3600:
            try:
                with open(cache_file, "r", encoding='utf-8') as f:
                    cached_data = json.load(f)
                    if cached_data:  # Verifica se o cache não está vazio
                        return cached_data
            except Exception as e:
                st.warning(f"Erro ao ler cache: {str(e)}")
    
    # Se não tiver cache válido, faz a chamada à API
    result = safe_api_call(func, params)
    
    if result is not None:
        # Salva no cache
        try:
            with open(cache_file, "w", encoding='utf-8') as f:
                json.dump(result, f)
        except Exception as e:
            st.warning(f"Erro ao salvar cache: {str(e)}")
    
    return result

@lru_cache(maxsize=256)
def cached_player_log(player_id):
    """Obtém log do jogador com cache"""
    def fetch_data(params):
        try:
            return PlayerGameLog(
                player_id=params['player_id'],
                season=obter_temporada_atual(),
                timeout=NBA_API_TIMEOUT
            ).get_data_frames()[0].head(10).to_dict("records")
        except Exception as e:
            st.warning(f"Erro ao buscar dados do jogador {params['player_id']}: {str(e)}")
            return None
    
    return cached_api_call(
        endpoint="player_log",
        func=fetch_data,
        params={"player_id": player_id}
    )

@lru_cache(maxsize=32)
def cached_team_log(team_id):
    """Obtém log do time com cache"""
    def fetch_data(params):
        try:
            return TeamGameLog(
                team_id=params['team_id'],
                timeout=NBA_API_TIMEOUT
            ).get_data_frames()[0].head(10).to_dict("records")
        except Exception as e:
            st.warning(f"Erro ao buscar dados do time {params['team_id']}: {str(e)}")
            return None
    
    return cached_api_call(
        endpoint="team_log",
        func=fetch_data,
        params={"team_id": team_id}
    )

# --- Funções de Dados com Fallback ---
@with_loading
def safe_get_jogos_do_dia():
    """Obtém jogos do dia com tratamento de erro"""
    try:
        return get_jogos_do_dia()
    except Exception as e:
        st.error(f"Erro ao buscar jogos do dia: {str(e)}")
        # Tenta retornar dados de cache se disponível
        cache_file = CACHE_DIR / "last_games.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []

@with_loading
def safe_get_jogadores_time(team_id):
    """Obtém jogadores do time com tratamento de erro"""
    try:
        return get_jogadores_time(team_id)
    except Exception as e:
        st.error(f"Erro ao buscar jogadores do time {team_id}: {str(e)}")
        return []

# --- Pré-carregamento em Segundo Plano ---
def preload_data_in_background():
    """Carrega dados antecipadamente em segundo plano"""
    def worker():
        try:
            # Salva os jogos do dia primeiro
            jogos = safe_get_jogos_do_dia()
            if jogos:
                with open(CACHE_DIR / "last_games.json", "w", encoding='utf-8') as f:
                    json.dump(jogos, f)
                
                for jogo in jogos:
                    # Pré-carrega dados dos times
                    cached_team_log(jogo['team1_id'])
                    cached_team_log(jogo['team2_id'])
                    
                    # Pré-carrega dados dos jogadores (limitado para evitar timeout)
                    for team_id in [jogo['team1_id'], jogo['team2_id']]:
                        jogadores = safe_get_jogadores_time(team_id)[:8]  # Limita a 8 jogadores por time
                        for jogador in jogadores:
                            cached_player_log(jogador["id"])
            
            background_results.put(("success", "Dados pré-carregados com sucesso!"))
        except Exception as e:
            background_results.put(("error", f"Erro no pré-carregamento: {str(e)}"))
    
    Thread(target=worker, daemon=True).start()

# --- Funções de Análise ---
@with_loading
def analisar_time(jogadores):
    """Analisa estatísticas dos jogadores de um time"""
    def processar(jogador):
        try:
            data = cached_player_log(jogador["id"])
            if not data:
                return None
            
            df = pd.DataFrame(data)
            return {
                "Jogador": jogador["nome"],
                "15+ Pontos": df[df["PTS"] >= 15].shape[0],
                "3+ Assistências": df[df["AST"] >= 3].shape[0],
                "5+ Rebotes": df[df["REB"] >= 5].shape[0],
                "Últimos 10 Jogos": len(data)
            }
        except Exception as e:
            st.warning(f"Erro ao processar {jogador['nome']}: {str(e)}")
            return None
    
    resultados = []
    with ThreadPoolExecutor(max_workers=4) as executor:  # Limita workers para evitar sobrecarga
        futures = {executor.submit(processar, jogador): jogador for jogador in jogadores[:12]}  # Limita a 12 jogadores
        
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    resultados.append(result)
            except Exception as e:
                st.warning(f"Erro no processamento: {str(e)}")
    
    return sorted(resultados, key=lambda x: x["15+ Pontos"], reverse=True) if resultados else []

@with_loading
def pontuacao_minima(team_id):
    """Obtém pontuação mínima do time nos últimos 10 jogos"""
    data = cached_team_log(team_id)
    if not data:
        return None
    try:
        df = pd.DataFrame(data)
        return df["PTS"].min()
    except Exception as e:
        st.warning(f"Erro ao calcular pontuação mínima: {str(e)}")
        return None

# --- Interface do Usuário ---
st.set_page_config(page_title="NBA Betting Analyzer", layout="wide")
st.title("🏀 NBA Betting Analyzer Pro")

# Estilos CSS customizados
st.markdown("""
    <style>
        .stDataFrame { font-size: 14px; }
        .stAlert { font-size: 16px; }
        .stProgress > div > div > div > div {
            background-color: #1db954;
        }
        .st-bb { background-color: #f0f2f6; }
        .st-at { background-color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# Executa limpeza de cache e pré-carregamento
if 'last_cache_clean' not in st.session_state:
    clean_old_cache()
    st.session_state.last_cache_clean = time.time()
    preload_data_in_background()
    st.session_state.preload_started = True

# Mostra status do pré-carregamento
if not background_results.empty():
    status, message = background_results.get()
    if status == "success":
        st.sidebar.success(message)
    else:
        st.sidebar.error(message)

# Seleção de jogo
jogos = safe_get_jogos_do_dia()

if not jogos:
    st.warning("Não foi possível carregar os jogos do dia. Tente novamente mais tarde.")
    st.stop()

opcoes = {
    f"{j['team1_nome']} 🆚 {j['team2_nome']}": (j['team1_id'], j['team2_id'])
    for j in jogos
}

jogo_escolhido = st.selectbox(
    "Escolha um jogo do dia:",
    list(opcoes.keys()),
    index=0 if opcoes else None
)

if jogo_escolhido:
    team1_id, team2_id = opcoes[jogo_escolhido]
    
    with st.expander("🔍 Estatísticas Detalhadas", expanded=True):
        tab1, tab2 = st.tabs(["📊 Comparação de Times", "👥 Estatísticas dos Jogadores"])
        
        with tab1:
            st.subheader(f"📈 Performance Recente")
            col1, col2 = st.columns(2)
            
            with col1:
                pts_min = pontuacao_minima(team1_id)
                st.metric(
                    label=f"{jogo_escolhido.split(' 🆚 ')[0]} - Mínimo",
                    value=f"{pts_min if pts_min is not None else 'N/A'} pts",
                    help="Menor pontuação nos últimos 10 jogos"
                )
            
            with col2:
                pts_min = pontuacao_minima(team2_id)
                st.metric(
                    label=f"{jogo_escolhido.split(' 🆚 ')[1]} - Mínimo",
                    value=f"{pts_min if pts_min is not None else 'N/A'} pts",
                    help="Menor pontuação nos últimos 10 jogos"
                )
        
        with tab2:
            st.subheader("👥 Estatísticas dos Jogadores (Últimos 10 Jogos)")
            jogadores_time1 = safe_get_jogadores_time(team1_id)
            jogadores_time2 = safe_get_jogadores_time(team2_id)
            
            if not jogadores_time1 and not jogadores_time2:
                st.warning("Não foi possível carregar dados dos jogadores.")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"### 🏠 {jogo_escolhido.split(' 🆚 ')[0]}")
                    df_time1 = analisar_time(jogadores_time1)
                    if df_time1:
                        st.dataframe(
                            df_time1,
                            column_config={
                                "15+ Pontos": st.column_config.ProgressColumn(
                                    "15+ PTS", format="%d", min_value=0, max_value=10
                                ),
                                "3+ Assistências": st.column_config.ProgressColumn(
                                    "3+ AST", format="%d", min_value=0, max_value=10
                                ),
                                "5+ Rebotes": st.column_config.ProgressColumn(
                                    "5+ REB", format="%d", min_value=0, max_value=10
                                )
                            }
                        )
                    else:
                        st.warning("Dados não disponíveis para o time da casa.")
                
                with col2:
                    st.markdown(f"### ✈️ {jogo_escolhido.split(' 🆚 ')[1]}")
                    df_time2 = analisar_time(jogadores_time2)
                    if df_time2:
                        st.dataframe(
                            df_time2,
                            column_config={
                                "15+ Pontos": st.column_config.ProgressColumn(
                                    "15+ PTS", format="%d", min_value=0, max_value=10
                                ),
                                "3+ Assistências": st.column_config.ProgressColumn(
                                    "3+ AST", format="%d", min_value=0, max_value=10
                                ),
                                "5+ Rebotes": st.column_config.ProgressColumn(
                                    "5+ REB", format="%d", min_value=0, max_value=10
                                )
                            }
                        )
                    else:
                        st.warning("Dados não disponíveis para o time visitante.")

# Gerenciamento de Cache
with st.sidebar:
    st.header("⚙️ Configurações")
    
    if st.button("🔄 Atualizar Todos os Dados", help="Força atualização de todos os dados da API"):
        clean_old_cache(max_age_days=0)
        preload_data_in_background()
        st.rerun()
    
    if st.button("🧹 Limpar Cache", help="Remove todos os dados em cache"):
        clean_old_cache(max_age_days=0)
        st.success("Cache limpo com sucesso!")
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
    st.markdown("ℹ️ **Status do Sistema:**")
    st.markdown(f"- Timeout da API: {NBA_API_TIMEOUT}s")
    st.markdown(f"- Máximo de tentativas: {MAX_RETRIES}")
    st.markdown("- Dados atualizados automaticamente")
    
    st.markdown("---")
    st.info("""
    **Dicas de Uso:**
    - Clique nos cabeçalhos para ordenar as tabelas
    - Passe o mouse sobre as colunas para ver explicações
    - Dados são armazenados em cache por 24 horas
    - Use o botão 'Atualizar' para forçar busca de novos dados
    """)

# Nota de rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("📅 Última atualização: " + time.strftime("%d/%m/%Y %H:%M:%S"))