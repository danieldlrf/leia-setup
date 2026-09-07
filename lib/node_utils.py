"""
node_utils.py

Se encarga de:
- Comprobar/instalar nvm (nvm-sh en Linux, nvm-windows en Windows)
- Instalar y activar la versión de Node especificada en config/config.yaml
"""

from lib import utils
import yaml
import os

NVM_SOURCE = 'source ~/.nvm/nvm.sh'

def is_nvm_installed() -> bool:
    """
    Comprueba si nvm ya está instalado.
    """
    if utils.is_windows():
        return utils.command_exists("nvm")
    else :
        return os.path.isdir(os.path.expanduser("~/.nvm"))


def install_nvm():
    """
    Muestra instrucciones de instalación de nvm según el SO y espera
    confirmación, re-comprobando con is_nvm_installed().
    """
    if utils.is_windows():
        utils.run_command(
            "winget install -e --id CoreyButler.NVMforWindows --silent --accept-package-agreements --accept-source-agreements",
            stop_on_error=False
        )
        print("✔ NVM instalado. Puede que necesites abrir una terminal nueva para que se detecte.")
    else:
        utils.run_command(
            "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash"
        )
        print("✔ NVM instalado.")


def ensure_nvm_installed():
    """
    Orquestador: si nvm no está instalado, lanza install_nvm().
    """
    if not is_nvm_installed():
        install_nvm()   
    else:
        print("✔ NVM ya está instalado.")


def is_node_version_installed(version: str) -> bool:
    """
    Comprueba si una versión concreta de Node ya está
    instalada vía nvm.
    """
    if utils.is_windows():
        res = utils.run_command("nvm list", stop_on_error=False)
    else: 
        res = utils.run_command(f'bash -ic "{NVM_SOURCE} && nvm list"', stop_on_error=False)

    return version in res


def install_node(version: str):
    """
    Instala y activa (nvm use) la versión de Node indicada.
    """
    if utils.is_windows():
        utils.run_command(f"nvm install {version}")
        utils.run_command(f"nvm use {version}")
    else: 
        utils.run_command(f'bash -ic "{NVM_SOURCE} && nvm install {version} && nvm use {version}"')


def ensure_node_installed(version: str):
    """
    llama a ensure_nvm_installed() primero, y luego,
    si la versión de Node pedida no está instalada, la instala.
    """
    ensure_nvm_installed()
    if not is_node_version_installed(version):
        install_node(version)   
    else:
        print(f"✔ Node {version} ya está instalado.")