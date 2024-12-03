from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import json

def scrape_nba_leaders():
    # Configuração do WebDriver com WebDriver Manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    try:
        # Acesse o site da NBA
        url = "https://www.nba.com/stats/leaders"
        driver.get(url)
        time.sleep(5)
        
        # Localize o elemento <select> pelo XPath
        dropdown = driver.find_element(By.XPATH, "//select[option[text()='All']]")
        
        # Use a classe Select para interagir com o elemento <select>
        select = Select(dropdown)
        
        # Selecionar a opção "All"
        select.select_by_visible_text("All")
        print("Opção 'All' selecionada com sucesso!")
    
        time.sleep(5)
        
        # Localize a tabela de líderes
        table = driver.find_element(By.CLASS_NAME, "Crom_table__p1iZz")
        
        # Extrair cabeçalhos da tabela
        headers = [header.text for header in table.find_elements(By.XPATH, ".//thead/tr/th")]

        # Adicionar uma coluna "Profile Link" para os links dos jogadores
        headers.append("Profile Link")

        # Extrair linhas da tabela
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        data = []
        for row in rows:
            cols = row.find_elements(By.XPATH, ".//td")
            row_data = [col.text for col in cols]

            # Adicionar o link do jogador
            player_link_element = row.find_element(By.XPATH, ".//a")
            player_link = player_link_element.get_attribute("href")
            row_data.append(player_link)

            data.append(row_data)
        
        # Criar DataFrame com os dados
        df = pd.DataFrame(data, columns=headers)
        print(df)

        # # Salvar em um arquivo Excel
        # df.to_excel("Jogadores.xlsx", index=False)
        # print("Dados salvos em 'Jogadores.xlsx'.")
         # Salvar em um arquivo JSON
        json_data = df.to_dict(orient="records")  # Converte para lista de dicionários
        with open("Jogadores.json", "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        print("Dados salvos em 'Jogadores.json'.")

    finally:
        # Fechar o navegador
        driver.quit()

if __name__ == "__main__":
    scrape_nba_leaders()
