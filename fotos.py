import json
import requests
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import os

# Carregar os dados do arquivo JSON
with open('Jogadores.json', 'r', encoding='utf-8') as f:
    jogadores_data = json.load(f)

# Criar pasta para salvar as fotos
os.makedirs("fotos", exist_ok=True)

# Configurar o Selenium para otimização
def iniciar_driver():
    options = Options()
    # options.add_argument("--headless")  # Sem interface gráfica
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Função para salvar a foto do jogador
def salvar_foto(url, nome_jogador):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            filepath = f"fotos/{nome_jogador}.png"
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Foto salva: {filepath}")
        else:
            print(f"Erro ao baixar a foto de {nome_jogador}: {response.status_code}")
    except Exception as e:
        print(f"Erro ao salvar a foto de {nome_jogador}: {e}")

# Função para processar um único jogador (focado apenas na foto)
def processar_jogador(jogador):
    driver = iniciar_driver()
    try:
        # Extrair ID e nome do jogador
        player_id = jogador['Profile Link'].split("/")[-2]
        player_name = jogador['PLAYER'].lower().replace(" ", "-")
        link = f"https://www.nba.com/player/{player_id}/{player_name}/profile"

        # Acessar o link
        driver.get(link)

        # Esperar pela imagem do jogador
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "PlayerImage_image__wH_YX"))
        )

        # Extrair URL da foto
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        image_element = soup.find('img', class_="PlayerImage_image__wH_YX")
        if image_element:
            image_url = image_element['src']
            salvar_foto(image_url, player_name)
        else:
            print(f"Foto não encontrada para {jogador['PLAYER']}")
    except Exception as e:
        print(f"Erro ao processar {jogador['PLAYER']}: {e}")
    finally:
        driver.quit()

# Paralelismo para processar jogadores
def processar_jogadores(jogadores_data):
    with ThreadPoolExecutor(max_workers=4) as executor:  # Ajuste max_workers conforme necessário
        executor.map(processar_jogador, jogadores_data)

# Processar jogadores (somente fotos)
print("Iniciando download das fotos...")
processar_jogadores(jogadores_data)
print("Download concluído. As fotos estão na pasta 'fotos'.")
