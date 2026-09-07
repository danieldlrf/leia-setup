# setup.py 

import importlib
import subprocess
import sys


def ensure_pyyaml_installed():
    """
    Comprueba si PyYAML está instalado; si no, lo instala con pip
    antes de que el resto del programa intente importarlo.
    """
    try:
        importlib.import_module("yaml")
    except ModuleNotFoundError:
        print("📦 PyYAML no está instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml"], check=True)
        print("✔ PyYAML instalado correctamente.")

ensure_pyyaml_installed()

from lib import docker_utils, node_utils, repo_utils, env_utils


#VARS:
config_path = "config/config.yaml"
values_env_path = "config/values.env"
node_version = "22"

def main():
    
    docker_utils.ensure_docker_installed()  
    docker_utils.offer_mongodb_compass() 
    docker_utils.free_required_ports(config_path)
    docker_utils.start_services(config_path)    
    
    node_utils.ensure_nvm_installed()
    node_utils.ensure_node_installed(node_version)

    repo_utils.clone_all_repos(config_path)
    repo_utils.checkout_all_repos(config_path)
    repo_utils.install_dependencies_all(config_path)

    env_utils.rename_all_envs(config_path)
    env_utils.apply_all_env_values(config_path, values_env_path)

    repo_utils.generate_vscode_tasks(config_path)

if __name__ == "__main__":
    main()
