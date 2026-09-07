"""
env_utils.py

Se encarga de:
- Renombrar .env.example a .env en cada repo
- Parsear config/values.env (con prefijos REPO_VARIABLE) y aplicar
  esos valores concretos dentro del .env de cada repo
"""

import os
from lib import repo_utils



def _prefix_from_repo_name(repo_name: str) -> str:
    """
    Convierte "leia-workbench-backend" -> "WORKBENCH_BACKEND".
    """
    list_name = repo_name.split("-")[1:]
    return "_".join(list_name).upper()


def _rename_env_example(repo_path: str):
    """
    Renombra .env.example a .env dentro de la carpeta del repo,
    si .env.example existe y .env todavía no.
    """
    env = os.path.join(repo_path, ".env.example")
    env_new = os.path.join(repo_path, ".env")
    if os.path.exists(env):
        os.replace(env, env_new)
    else:
        print(f"⚠️ No se encontró .env.example en {repo_path} (puede que ya esté renombrado).")


def rename_all_envs(config_path: str = "config/config.yaml"):
    """
    Aplica _rename_env_example() a todos los repos.
    Mismo patrón que clone_all_repos() en repo_utils.py.
    """
    download_path = repo_utils._get_download_path(config_path)
    for repo in repo_utils._load_repos(config_path):
        repo_path = repo_utils._repo_path(download_path, repo["name"])
        _rename_env_example(repo_path)
    


def _parse_values_env(values_env_path: str) -> dict[str, dict[str, str]]:
    """
    Lee config/values.env y devuelve un diccionario anidado:
    {
        "WORKBENCH_BACKEND": {
            "OPENAI_API_KEY": "sk-proj-...",
            "MONGO_URI": "mongodb://localhost:27017/workbench"
        },
        "DESIGNER_BACKEND": {
            "MONGO_URI": "mongodb://localhost:27017/designer"
        }
    }
    """
    res = dict()
    with open(values_env_path, "r", encoding="utf-8") as file:
        resString = ""
        for line in file:
            clean_line = line.strip()

            if not clean_line:
                continue
            if clean_line.startswith("#"): 
                resString = clean_line.replace("#", "")
                if resString not in res:
                    res[resString] = {}
                continue

            key = clean_line.split("=", 1)[0].replace(resString + "_", "")
            res[resString][key] = clean_line.split("=", 1)[1]

    return res
  

def _apply_values_to_env_file(env_path: str, values: dict[str, str]):
    """
    Abre el .env de un repo concreto y sustituye SOLO las variables
    indicadas en `values` (las demás líneas del .env se quedan
    intactas, tal como estaban en el .env.example original).
    """
    new_env = []
    with open(env_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines: 
            clean_line = line.strip()
            
            if not clean_line or clean_line.startswith("#"): 
                new_env.append(line)
                continue

            if  clean_line.split("=",1)[0] in values : 
                new_line = clean_line + "=" + values[clean_line.split("=",1)[0]]
                new_env.append(new_line + "\n")
            else: 
                new_env.append(line)

    with open(env_path, "w", encoding="utf-8") as file:
        file.writelines(new_env)


def apply_all_env_values(config_path: str = "config/config.yaml", values_env_path: str = "config/values.env"):
    """
    Orquestador: para cada repo, si su prefijo aparece en el
    diccionario devuelto por _parse_values_env(), aplica esos
    valores a su .env real.
    """
    repos = repo_utils._load_repos(config_path)
    dir = repo_utils._get_download_path(config_path)
    env = _parse_values_env(values_env_path)
    for repo in repos: 
        if _prefix_from_repo_name(repo["name"]) in env:
            _apply_values_to_env_file( os.path.join(os.path.join(dir, repo["name"]), ".env"), env[_prefix_from_repo_name(repo["name"])])
        else: 
            continue
