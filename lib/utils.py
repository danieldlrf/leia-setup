"""
utils.py

Funciones base compartidas por el resto de módulos (docker_utils,
node_utils, repo_utils, env_utils...). No depende de ningún otro
módulo del proyecto.
"""

import platform
import shutil
import subprocess


def is_windows() -> bool:
    """
    Devuelve True si el sistema operativo actual es Windows.
    """
    return platform.system() == 'Windows'


def command_exists(command: str) -> bool:
    """
    Comprueba si un ejecutable/comando existe en el PATH del sistema
    """
    return shutil.which(command) is not None


def run_command(command: str, stop_on_error: bool = True, cwd: str = None) -> str:
    """
    Ejecuta un comando de shell y devuelve su salida (stdout) como string.

    Si el comando falla (returncode != 0):
    - stop_on_error=True (por defecto): imprime el error y detiene
      el programa con una excepción.
    - stop_on_error=False: imprime un aviso pero deja continuar,
      devolviendo el stdout (probablemente vacío).
    """
    res = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)

    if res.returncode != 0:
        print(f"❌ Error ejecutando: {command}")
        print(res.stderr)
        if stop_on_error:
            raise RuntimeError(f"El comando falló: {command}")

    return res.stdout