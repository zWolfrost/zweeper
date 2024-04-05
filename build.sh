pyinstaller zweeper.py -y -F --noconsole \
--add-data="./minesweeper.otf:." \
--paths="./venv/lib/python3.10/site-packages" \
--icon="./icon.ico"