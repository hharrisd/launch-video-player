import subprocess
import os
import time
import tomllib
import logging
import contextlib

logging.basicConfig(format="%(levelname)s | %(asctime)s | %(message)s")


def load_config_file() -> dict:
    """Load configuration from toml file and return it as a dictionary.

    Returns:
        config (dict): Configuration dictionary
    """
    try:
        with open("config.toml", mode="rb") as fp:
            return tomllib.load(fp)
    except FileNotFoundError:
        logging.error("El archivo de configuración no está creado")
        exit()


def validate_config_paths(config: dict) -> bool:
    """Check if the paths in the config files are valid
    Args:
        config (dict): Configuration dictionary

    Returns:
        True if the paths are valid, False otherwise
    """

    required_keys = ['vlc_path', 'media_path', 'playlist_path']
    for key in required_keys:
        if key not in config:
            logging.error(f"La clave '{key}' no está presente en el archivo de configuración.")
            return False

    # Verificar si las rutas son válidas
    for key, path in config.items():
        if key.endswith('_path') and not os.path.exists(path):
            logging.error(f"La ruta especificada para '{key}' no existe. Ruta: {path}")
            return False

    return True


@contextlib.contextmanager
def in_dir(path: str) -> None:
    """Context manager that yields a given directory path and
    changes to the current working directory at the end of the context
    Args:
        path (str): Directory path
    """
    current_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(current_dir)


def get_files_paths(path: str) -> list[str]:
    """Get the absolute paths of the files in the given path
        Args:
            path (str): Directory path

        Returns:
            A list of the absolute paths of the files in the given path
        """
    with in_dir(path):
        project_files = os.listdir()
        abs_paths = [os.path.abspath(f) for f in project_files if os.path.isfile(f)]
    return abs_paths


def configure_path_for_playlist(path: str) -> str:
    """Configure the path for the playlist format
    Args:
        path (str): absolute path of the file
    Returns:
        A string with the required playlist format
    """
    _, tail = os.path.split(path)
    return f"#EXTINF:3,{tail}\nfile://{path}\n\n"


def write_playlist_file(playlist_path: str, paths_list: list[str]) -> None:
    """Write the playlist file with the given path_list
    Args:
        playlist_path (str): absolute path of the playlist directory
        paths_list (list): List of file paths
    """
    with open(f'{playlist_path}/playlist.m3u', mode='w', encoding='utf-8') as file:
        file.write("#EXTM3U \n")
        for path in paths_list:
            file.write(configure_path_for_playlist(path))


def execute_player(player_path: str, playlist_path: str) -> None:
    command = [player_path, "--fullscreen", "--loop", "--no-video-title-show", "-Z", 'playlist.m3u']
    with in_dir(playlist_path):
        proceso_vlc = subprocess.Popen(command)

        while True:
            if proceso_vlc.poll() is not None:
                logging.warning("VLC se ha cerrado inesperadamente. Reiniciando la reproducción...")
                proceso_vlc = subprocess.Popen(command)
            time.sleep(5)


def main() -> None:
    config = load_config_file()
    if not validate_config_paths(config):
        exit(1)
    paths = get_files_paths(config['media_path'])
    write_playlist_file(config['playlist_path'], paths)
    execute_player(config['vlc_path'], config['playlist_path'])


if __name__ == "__main__":
    main()
