import json
import os
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Carregar os dados do arquivo JSON
with open('Jogadores.json', 'r', encoding='utf-8') as f:
    jogadores_data = json.load(f)

# Criar pasta para salvar as fotos
os.makedirs("fotos", exist_ok=True)

# Configurar o Selenium para otimização
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")  # Sem interface gráfica
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Remover o argumento 'path' para compatibilidade
    driver_path = ChromeDriverManager().install()
    return webdriver.Chrome(service=Service(driver_path), options=options)


# Função para processar um único jogador
# Função para processar um único jogador
def processar_jogador(jogador):
    driver = iniciar_driver()  # Inicia um novo driver para cada thread
    try:
        # Extrair ID e nome do jogador
        player_id = jogador['Profile Link'].split("/")[-2]
        player_name = jogador['PLAYER'].lower().replace(" ", "-")
        link = f"https://www.nba.com/player/{player_id}/{player_name}/profile"

        # Acessar o link
        driver.get(link)

        # Fechar pop-up, se houver
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "close-button"))
            ).click()
        except TimeoutException:
            pass  # Nenhum pop-up

        # Esperar pela tabela de estatísticas
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "MockStatsTable_statsTable__V_Skx"))
        )

        # Extrair informações com BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('div', class_='MockStatsTable_statsTable__V_Skx')
        pontos, rebotes, assistencias, tres_pontos, roubos, bloqueios, turnovers = [], [], [], [], [], [], []
        game_dates, matchups = [], []  # Novas listas para Game Date e Matchup

        if table:
            rows = table.find('table').find_all('tr')[1:6]  # Últimos 5 jogos
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 16:  # Garantir que há colunas suficientes
                    game_dates.append(cols[0].text.strip())        # Game Date
                    matchups.append(cols[1].text.strip())          # Matchup
                    pontos.append(int(cols[4].text.strip()))       # Pontos
                    rebotes.append(int(cols[16].text.strip()))     # Rebotes
                    assistencias.append(int(cols[17].text.strip())) # Assistências
                    tres_pontos.append(int(cols[8].text.strip()))   # Três Pontos
                    roubos.append(int(cols[18].text.strip()))       # Roubos
                    bloqueios.append(int(cols[19].text.strip()))    # Bloqueios
                    turnovers.append(int(cols[20].text.strip()))    # Turnovers

        # Retornar os resultados processados
        return {
            'Nome Completo': jogador['PLAYER'],
            'Time': jogador['TEAM'],
            'Game Dates': game_dates,          # Incluído Game Dates
            'Matchups': matchups,              # Incluído Matchups
            'Últimos Pontos': pontos,
            'Últimos Rebotes': rebotes,
            'Últimas Assistências': assistencias,
            'Últimos Três Pontos': tres_pontos,
            'Últimos Roubos': roubos,
            'Últimos Bloqueios': bloqueios,
            'Últimos Turnovers': turnovers,
            'Pontos + Rebotes': [p + r for p, r in zip(pontos, rebotes)],
            'Pontos + Assistências': [p + a for p, a in zip(pontos, assistencias)],
            'Pontos + Rebotes + Assistências': [p + r + a for p, r, a in zip(pontos, rebotes, assistencias)],
        }
    except Exception as e:
        print(f"Erro ao processar {jogador['PLAYER']}: {e}")
    finally:
        driver.quit()
    return None


# Paralelismo para processar jogadores
def processar_jogadores(jogadores_data):
    with ThreadPoolExecutor(max_workers=4) as executor:  # Ajuste `max_workers` conforme a capacidade da máquina
        resultados = list(executor.map(processar_jogador, jogadores_data))
    return [r for r in resultados if r is not None]  # Filtrar jogadores processados com sucesso

# Carregar ou inicializar cache
cache_file = "Jogadores_Resultado_Completo.json"
if os.path.exists(cache_file):
    with open(cache_file, 'r', encoding='utf-8') as f:
        cache = json.load(f)
else:
    cache = []

# Jogadores que já foram processados
jogadores_processados = {jogador['Nome Completo'] for jogador in cache}

# Filtrar jogadores não processados
jogadores_a_processar = [jogador for jogador in jogadores_data if jogador['PLAYER'] not in jogadores_processados]

# Processar jogadores
resultados = processar_jogadores(jogadores_a_processar)

# Atualizar o cache
cache.extend(resultados)

# Salvar os resultados no arquivo JSON
with open(cache_file, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=4)

print("Dados salvos em 'Jogadores_Resultado_Completo.json'.")
