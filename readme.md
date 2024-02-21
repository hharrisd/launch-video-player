# Launch Video Player
Creates a playlist based on files on a media directory and launch VLC media player

## Steps

1. Run the command: ``` git config --global core.autocrlf true  # Windows Users```
2. Clone the repository: `git clone https://github.com/hharrisd/launch-video-player.git`
3. Create a file `config.toml` following the example file `config.toml.example`
4. Create the folders indicated in the config file and configure the paths in `config.toml`
5. Run the application with the command: `python main.py`

## Command to generate executable app
```shell
pyinstaller --noconsole --onefile --windowed app.py  
```