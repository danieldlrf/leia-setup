"""
repo_utils.py

Se encarga de:
- Clonar los repos de leia definidos en config/config.yaml
- Cambiar a la rama indicada (develop)
- Instalar dependencias (npm ci)
- Arrancar cada repo en modo dev (npm run dev)
"""

import os
from lib import utils
import yaml
import subprocess
import json
import sys

def _load_repos(config_path: str) -> list[dict]:
    """
    Lee config/config.yaml y devuelve la lista bajo la clave `repos`.
    """
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["repos"]


def _get_download_path(config_path: str) -> str:
    """
    Lee config/config.yaml y devuelve la carpeta base de descarga.
    """
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["download_path"]


def _repo_path(download_path: str, repo_name: str) -> str:
    """
    Construye la ruta local de un repo concreto.
    """
    return os.path.join(download_path, repo_name)


def _is_repo_cloned(repo_path: str) -> bool:
    """
    Comprueba si un repo ya está clonado en esa ruta.
    """
    return os.path.isdir(os.path.join(repo_path, ".git"))


def clone_repo(repo: dict, download_path: str):
    """
    Clona un repo si no está ya clonado.
    """
    repo_path = _repo_path(download_path, repo["name"])
    if _is_repo_cloned(repo_path):
        print(f"✔ {repo['name']} ya está descargado.")
    else:
        utils.run_command(f'git clone {repo["url"]}', cwd=download_path)


def clone_all_repos(config_path: str = "config/config.yaml"):
    """
    Clona todos los repos definidos en el yaml.
    """
    download_path = _get_download_path(config_path)
    for repo in _load_repos(config_path):
        clone_repo(repo, download_path)



def checkout_branch(repo: dict, download_path: str):
    """
    Hace checkout de la rama indicada en el campo `branch` del repo.
    """
    repo_path = _repo_path(download_path, repo["name"])
    utils.run_command(repo["branch"], cwd=repo_path)


def checkout_all_repos(config_path: str = "config/config.yaml"):
    """
    Aplica checkout_branch() a todos los repos del yaml.
    """
    download_path = _get_download_path(config_path)
    for repo in _load_repos(config_path):
        checkout_branch(repo, download_path)
    

def install_dependencies(repo: dict, download_path: str):
    """
    Instala las dependencias del repo usando el comando del campo
    `dependencies_instal` (ej: "npm ci").
    """
    repo_path = _repo_path(download_path, repo["name"])
    utils.run_command(repo["dependencies_instal"], cwd=repo_path)


def install_dependencies_all(config_path: str = "config/config.yaml"):
    """
    Aplica install_dependencies() a todos los repos del yaml.
    """
    download_path = _get_download_path(config_path)
    for repo in _load_repos(config_path):
        install_dependencies(repo, download_path)


def run_dev(repo: dict, download_path: str):
    """
    Arranca el repo en modo desarrollo usando `run_command`
    (ej: "npm run dev").
    """
    repo_path = _repo_path(download_path, repo["name"])
    log_path = os.path.join(repo_path, "dev.log")
    with open(log_path, "w") as log_file:
        subprocess.Popen(
            repo["run_command"],
            shell=True,
            cwd=repo_path,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )


def run_dev_all(config_path: str = "config/config.yaml"):
    """
    Lanza run_dev() para TODOS los repos, cada uno en su propio
    proceso en paralelo (todos corriendo el "npm run dev" a la vez).
    """
    download_path = _get_download_path(config_path)
    for repo in _load_repos(config_path):
        run_dev(repo, download_path)


def generate_vscode_tasks(config_path: str = "config/config.yaml"):
    """
    Genera un tasks.json con:
    - Una tarea "dev: <repo>" por cada repo del yaml
    - Una tarea "start-repos" que agrupa todas las anteriores
    - Una tarea "docker-services" que arranca los contenedores
    - Una tarea maestra "🚀 Levantar todo LEIA" que ejecuta
      docker-services y LUEGO start-repos, en ese orden

    El fichero se genera en <download_path>/.vscode/tasks.json,
    junto a los repos clonados (no junto al script de Python).
    """
    download_path = _get_download_path(config_path)
    repos = _load_repos(config_path)

    with open(config_path, "r", encoding="utf-8") as file:
        docker_services = yaml.safe_load(file)["docker"]

    repo_tasks = []
    repo_labels = []
    for repo in repos:
        repo_path = _repo_path(download_path, repo["name"])
        label = f"dev: {repo['name']}"
        repo_labels.append(label)
        repo_tasks.append({
            "label": label,
            "type": "shell",
            "command": repo["run_command"],
            "options": {"cwd": repo_path},
            "presentation": {"panel": "dedicated", "reveal": "silent"},
            "problemMatcher": []
        })

    free_ports_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "free_ports.py")
    )
    docker_start_commands = "; ".join(serv["run"] for serv in docker_services)
    docker_command = f'"{sys.executable}" "{free_ports_script}" && {docker_start_commands}'

    docker_task = {
        "label": "docker-services",
        "type": "shell",
        "command": docker_command,
        "presentation": {"panel": "dedicated", "reveal": "silent"},
        "problemMatcher": []
    }

    start_repos_task = {
        "label": "start-repos",
        "dependsOn": repo_labels,
        "problemMatcher": []
    }

    master_task = {
        "label": "🚀 Levantar todo LEIA",
        "dependsOn": ["docker-services", "start-repos"],
        "dependsOrder": "sequence",
        "problemMatcher": []
    }

    all_tasks = repo_tasks + [docker_task, start_repos_task, master_task]
    tasks_json = {"version": "2.0.0", "tasks": all_tasks}

    output_dir = os.path.join(download_path, ".vscode")
    output_path = os.path.join(output_dir, "tasks.json")

    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(tasks_json, file, indent=2)

    print(f"✔ tasks.json generado en {output_path}")