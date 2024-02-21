import contextlib
import logging
import os
import pathlib
import subprocess
from tkinter.filedialog import askdirectory, askopenfilename
from sys import platform

import ttkbootstrap as ttk
from ttkbootstrap.constants import *


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


class LaunchPlayer(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=15)
        self.pack(fill=BOTH, expand=YES)

        master.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # application variables
        _path = pathlib.Path().absolute().as_posix()
        self.media_path = ttk.StringVar(value=_path)
        self.vlc_path = ttk.StringVar(value=None)
        self.metadata_path = ttk.StringVar(value=None)
        self.vlc_process = None

        # header and labelframe option container
        option_text = "Indique las rutas antes de iniciar el reproductor"
        self.option_lf = ttk.Labelframe(self, text=option_text, padding=15)
        self.option_lf.pack(fill=X, expand=YES, anchor=N)

        self.preload_cached_paths()
        self.create_vlc_path_row()
        self.create_media_path_row()
        self.create_actions_row()

    def create_media_path_row(self):
        """Add path row to labelframe"""
        media_path_row = ttk.Frame(self.option_lf)
        media_path_row.pack(fill=X, expand=YES, pady=15)
        media_path_lbl = ttk.Label(media_path_row, text="Ruta Media", width=8)
        media_path_lbl.pack(side=LEFT, padx=(15, 0))
        media_path_ent = ttk.Entry(media_path_row, textvariable=self.media_path)
        media_path_ent.pack(side=LEFT, fill=X, expand=YES, padx=5)
        media_browse_btn = ttk.Button(
            master=media_path_row,
            text="Navegar",
            command=self.on_browse_media,
            width=8
        )
        media_browse_btn.pack(side=LEFT, padx=5)

    def create_vlc_path_row(self):
        """Add path row to labelframe"""
        vlc_path_row = ttk.Frame(self.option_lf)
        vlc_path_row.pack(fill=X, expand=YES)
        vlc_path_lbl = ttk.Label(vlc_path_row, text="Ruta VLC", width=8)
        vlc_path_lbl.pack(side=LEFT, padx=(15, 0))
        vlc_path_ent = ttk.Entry(vlc_path_row, textvariable=self.vlc_path)
        vlc_path_ent.pack(side=LEFT, fill=X, expand=YES, padx=5)
        vlc_browse_btn = ttk.Button(
            master=vlc_path_row,
            text="Navegar",
            command=self.on_browse_file,
            width=8
        )
        vlc_browse_btn.pack(side=LEFT, padx=5)

    def create_actions_row(self):
        """Add path row to labelframe"""
        actions_row = ttk.Frame(self.option_lf)
        actions_row.pack(fill=X, expand=YES, pady=15)

        launch_btn = ttk.Button(
            master=actions_row,
            text="Iniciar",
            command=self.on_launch_player,
            width=8,
            bootstyle=SUCCESS,
        )
        launch_btn.pack(side=LEFT, padx=5)

        stop_btn = ttk.Button(
            master=actions_row,
            text="Detener",
            command=self.on_stop_player,
            width=8,
            bootstyle=DANGER
        )
        stop_btn.pack(side=LEFT, padx=5)

    def on_browse_media(self):
        """Callback for directory browse"""
        path = askdirectory(title="Navegar directorio")
        if path:
            self.media_path.set(path)

    def on_browse_file(self):
        """Callback for directory browse"""
        path = askopenfilename(title="Navegar archivo")
        if path:
            self.vlc_path.set(path)

    def validate_paths(self):
        # Verificar si las rutas son válidas
        paths = {'VlcPath': self.vlc_path, 'media_path': self.media_path}
        for key, path in paths.items():
            if not os.path.exists(path.get()):
                logging.error(f"La ruta especificada para '{key}' no existe. Ruta: {path.get()}")
                return False

        return True

    def on_launch_player(self):
        if not self.validate_paths():
            logging.error("Error al lanzar el reproductor")

        self.write_playlist_file()
        self.execute_player()
        self.cache_paths()

    def on_stop_player(self):
        if self.vlc_process:
            self.vlc_process.kill()

    def on_window_close(self):
        self.on_stop_player()
        self.master.destroy()

    def get_files_paths(self) -> list[str]:
        """Get the absolute paths of the files in the given path
            Args:
                path (str): Directory path

            Returns:
                A list of the absolute paths of the files in the given path
            """
        with (in_dir(self.media_path.get())):
            project_files = os.listdir()
            abs_paths = []
            for f in project_files:
                if os.path.isfile(f) and not f.endswith('.m3u') and not f.startswith('.'):
                    abs_paths.append(os.path.abspath(f))

        return abs_paths

    @staticmethod
    def configure_playlist_format(path: str) -> str:
        """Configure the path for the playlist format
        Args:
            path (str): absolute path of the file
        Returns:
            A string with the required playlist format
        """
        _, tail = os.path.split(path)
        file_prefix = "" if platform == "win32" else "file://"
        return f"#EXTINF:3,{tail}\n{file_prefix}{path}\n\n"

    def get_or_create_metadata_folder(self):
        directory = "_metadata"
        path = os.path.join(self.media_path.get(), directory)
        if not os.path.exists(path):
            os.mkdir(path)

        self.metadata_path.set(path)
        return path

    def write_playlist_file(self) -> None:
        """Write the playlist file with the given path list"""
        playlist_path = os.path.join(self.get_or_create_metadata_folder(), 'playlist.m3u')
        with open(playlist_path, mode='w', encoding='utf-8') as file:
            file.write("#EXTM3U \n")
            for path in self.get_files_paths():
                file.write(self.configure_playlist_format(path))

    def execute_player(self) -> None:
        # Command Line Help: https://wiki.videolan.org/VLC_command-line_help/
        command = [self.vlc_path.get(), "--fullscreen", "--loop", "--no-video-title-show", "-Z", "-q", 'playlist.m3u']
        with in_dir(self.metadata_path.get()):
            self.on_stop_player()
            self.vlc_process = subprocess.Popen(command)

    def cache_paths(self) -> None:
        dir_user = os.path.expanduser("~")
        paths_file = os.path.join(dir_user, "lauch_mediaplayer_cached_paths.txt")
        with open(paths_file, "w") as file:
            file.write(f"{self.vlc_path.get()}|{self.media_path.get()}|{self.metadata_path}")

    def preload_cached_paths(self):
        cache_file = os.path.join(os.path.expanduser("~"), "lauch_mediaplayer_cached_paths.txt")
        if os.path.exists(cache_file):
            with open(cache_file, "r") as file:
                content = file.read()
            paths = content.split("|")

            if paths and len(paths) == 3:
                self.vlc_path.set(paths[0])
                self.media_path.set(paths[1])
                self.metadata_path.set(paths[2])


if __name__ == '__main__':
    app = ttk.Window("Generar Playlist", "superhero")
    LaunchPlayer(app)
    app.mainloop()
