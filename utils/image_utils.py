import os

LOGOS_DIR = "Logos"
IMAGES_DIR = "fotos"
DEFAULT_IMAGE = "https://via.placeholder.com/150"

def carregar_logo_time(nome_time):
    path = os.path.join(LOGOS_DIR, nome_time.replace(" ", "_") + ".png")
    return path if os.path.exists(path) else DEFAULT_IMAGE

def carregar_foto_jogador(nome_jogador):
    path = os.path.join(IMAGES_DIR, nome_jogador.replace(" ", "-") + ".png")
    return path if os.path.exists(path) else DEFAULT_IMAGE
