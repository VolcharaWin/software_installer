# Имя выходного файла
TARGET = installer

# Главный Python файл
MAIN_SCRIPT = main.py

ICON = gup_icon.ico
# Дополнительные файлы
ADD_DATA = \
    styles.qss;. \
    socket_thread.py;. \
    checkinstall.py;. \
    gup_icon.ico;.

# Команда PyInstaller
PYINSTALLER = pyinstaller

# Флаги для PyInstaller
PYI_FLAGS = --noconfirm --onefile --noconsole --icon=$(ICON)

# Задача по умолчанию
all: build

# Сборка проекта
build:
	$(PYINSTALLER) $(PYI_FLAGS) --name $(TARGET) $(foreach file, $(ADD_DATA), --add-data "$(file)") $(MAIN_SCRIPT)

# Очистка файлов сборки
clean:
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist
	if exist *.spec del /q *.spec
	if exist __pycache__ rmdir /s /q __pycache__

# Очистка и пересборка
rebuild: clean build
