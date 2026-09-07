# free_ports.py
"""
Script de entrada para que VS Code (o cualquier shell) pueda invocar
la liberación de puertos sin necesidad de saber nada de Python más
allá de "ejecuta este fichero".
"""
import os
from lib import docker_utils

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.yaml")

if __name__ == "__main__":
    docker_utils.free_required_ports(CONFIG_PATH)