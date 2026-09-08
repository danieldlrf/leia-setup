"""
docker_utils.py

Se encarga de:
- Comprobar/instalar Docker (Engine en Linux, Docker Desktop en Windows)
- Ofrecer instalar MongoDB Compass (opcional)
- Levantar los servicios docker definidos en config/config.yaml
"""

from lib import repo_utils, utils
import yaml

def is_docker_installed() -> bool:
    """
    Comprueba si docker ya está instalado en el sistema.
    """
    return utils.command_exists("docker") 
        

def install_docker():
    """
    Instala Docker si no está presente.
    """
    _print_docker_instructions()

    while not is_docker_installed():
        input("Press Enter when Docker was installed...")
        if not is_docker_installed():
            print("Todavía no detecto Docker instalado. Revisa los pasos e inténtalo de nuevo.\n")

    print("✔ Docker detectado correctamente.")

def ensure_docker_installed():
    if not is_docker_installed():
        install_docker()   
    else:
        print("✔ Docker ya está instalado.")

def _print_docker_instructions():
    """
    Imprime pasos de instalación según el SO.
    """
    if utils.is_windows():
        print("1º Entra en la tienda de Microsoft\n")
        print('2º Busca "Docker Desktop" e instalalo\n')
        print("3º Abre la aplicacion y realiza la configuracion inicial")
        print("⚠️Posibles problemas: no tener WSL activo o necesitas reiniciar el ordenador\n")
    else: 
        print('1º Ejecuta en una terminal "curl -fsSL https://get.docker.com | sudo sh" ')
        print('2º Añade tu usuario al grupo docker "sudo usermod -aG docker $USER" ')
        print('3º . Cierra sesión y vuelve a entrar para que el cambio de grupo surta efecto')
        print('4. Verifica que el servicio está arrancado: "sudo systemctl start docker" "sudo systemctl enable docker"')
        print("Mas info: https://docs.docker.com/engine/install/")

def offer_mongodb_compass():
    """
    Pregunta si quiere instalar MongoDB Compass (cliente GUI de Mongo).
    """
    res = input("Es recomendable instalar la herramienta MongoDB Compass, ¿deseas instalarla? y / n").strip()
    while res != "y" and res != "n":
        res = input("Es recomendable instalar la herramienta MongoDB Compass, ¿deseas instalarla? y / n").strip()
    if res == "y": 
        if utils.is_windows():
            utils.run_command("winget install -e --id MongoDB.Compass.Community --silent --accept-package-agreements --accept-source-agreements", stop_on_error=False)
        else: 
            print("1º Abre esta página en tu navegador: https://www.mongodb.com/try/download/compass \n")
            print("2º Selecciona tu sistema operativo (Linux) y el tipo de paquete segun tu distro")
            print('3º Descarga el paquete y ábrelo con el gestor de paquetes de tu sistema, o instálalo desde terminal: "sudo apt install ./<archivo>.deb"')
            print('4º Una vez instalado, podrás abrir MongoDB Compass desde el menú de aplicaciones, o ejecutando en terminal: "mongodb-compass"')
            input("Presiona Enter cuando hayas terminado de instalar MongoDB Compass...")

    elif res == "n":
        pass

def _load_docker_services(config_path: str) -> list[dict]:
    """
    Lee config/repos.yaml y devuelve la lista bajo la clave `docker`
    """
    with open(config_path, "r", encoding="utf-8") as file:
        docker_services = yaml.safe_load(file)["docker"]
        return docker_services


def _is_container_running(name: str) -> bool:
    """
    Comprueba si ya existe/está corriendo un contenedor con ese nombre.
    """
    res = utils.run_command(f"docker ps -a --filter name={name} --format {{{{.Names}}}}", stop_on_error=False)
    return name in res


def start_services(config_path: str = "config/config.yaml"):
    """
    Para cada servicio en la sección `docker` del yaml:
    - Si el contenedor ya existe -> lo arranca con el comando `run`
    - Si no existe -> lo crea con el comando `download`
    """
    download_path = repo_utils._get_download_path(config_path)  
    for serv in _load_docker_services(config_path):
        if _is_container_running(serv["name"]):
            comando = serv["run"]
        else:
            comando = serv["download"]

        comando = comando.replace("{download_path}", download_path)
        utils.run_command(comando)

def _find_container_using_port(port: int) -> str | None:
    """
    Busca si hay un contenedor Docker (cualquiera) usando ese puerto,
    y devuelve su nombre si lo encuentra (string vacío si no hay ninguno).
    """
    salida = utils.run_command(
        f'docker ps --filter "publish={port}" --format {{{{.Names}}}}',
        stop_on_error=False
    )
    return salida.strip()

def _find_pid_using_port(port: int) -> str:
    """
    Busca el PID del proceso que está usando un puerto concreto.
    Devuelve el PID como string, o "" si el puerto está libre.
    """
    if utils.is_windows():
        salida = utils.run_command(f"netstat -ano | findstr :{port}", stop_on_error=False)
    else:
        salida = utils.run_command(f"lsof -t -i:{port}", stop_on_error=False)

    if not salida.strip():
        return ""

    return salida.split()[-1]

def _kill_process(container: str):
    """
    Mata el proceso.
    """
    utils.run_command(f"docker stop {container}", stop_on_error=False)

def _kill_pid(pid: str):
    """
    Mata el proceso (no-Docker) con ese PID.
    """
    if utils.is_windows():
        return utils.run_command(f"taskkill /PID {pid} /F", stop_on_error=False)
    else:
        return utils.run_command(f"kill -9 {pid}", stop_on_error=False)


def free_required_ports(config_path: str = "config/config.yaml"):
    """
    Para cada servicio docker del yaml, comprueba si su(s) puerto(s)
    ya están ocupados por OTRO proceso, y si es así, pregunta al
    usuario si quiere matarlo para liberar el puerto.
    """
    for serv in _load_docker_services(config_path):
        for port in serv["ports"]:
            container = _find_container_using_port(port)
            if container != "":
                print(f"⚠️ El puerto {port} (necesario para '{serv['name']}') está ocupado por el contenedor {container}.")
                res = input(f"¿Quieres parar el contenedor {container} para liberar el puerto {port}? (y/n): ").strip()
                while res != "y" and res != "n":
                    res = input(f"Respuesta no válida. ¿Parar el contenedor {container}? (y/n): ").strip()

                if res == "y":
                    _kill_process(container)
                    print(f"✔ Contenedor {container} detenido. Puerto {port} liberado.")
                else:
                    print(f"Saltando. El puerto {port} sigue ocupado, '{serv['name']}' podría fallar al arrancar.")
            else:
                pid = _find_pid_using_port(port)
                if pid != "":
                    print(f"⚠️ El puerto {port} (necesario para '{serv['name']}') está ocupado por el proceso PID {pid}.")
                    res = input(f"¿Quieres matar el proceso {pid} para liberar el puerto {port}? (y/n): ").strip()
                    while res != "y" and res != "n":
                        res = input(f"Respuesta no válida. ¿Matar el proceso {pid}? (y/n): ").strip()

                    if res == "y":
                        _kill_pid(pid)
                        print(f"✔ Proceso {pid} finalizado. Puerto {port} liberado.")
                    else:
                        print(f"Saltando. El puerto {port} sigue ocupado, '{serv['name']}' podría fallar al arrancar.")