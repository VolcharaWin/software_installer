import os
import time  # Для добавления задержки
from PyQt6.QtCore import QThread, pyqtSignal

class CheckInstalledProgramsThread(QThread):
    """Поток для проверки установленных программ."""
    finished = pyqtSignal()

    def __init__(self, programs):
        super().__init__()
        self.programs = programs

    def run(self):
        """Проверка каждой программы на установку с задержкой."""
        time.sleep(5)  # Задержка 5 секунд для эмуляции проверки
        for program in self.programs:
            program.is_installed = self.is_program_installed(program.name)
        self.finished.emit()

    def is_program_installed(self, program_name):
        """Проверка установки программы."""
        if program_name.lower() == 'yandex':
            return self.is_yandex_installed()
        else:
            return self.is_program_installed_by_shortcut(program_name)

    def is_yandex_installed(self):
        yandex_folder_path = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Yandex', 'YandexBrowser'
        )
        browser_executable_path = os.path.join(
            yandex_folder_path, 'Application', 'browser.exe'
        )

        # Проверяем, существует ли папка и файл browser.exe
        return os.path.exists(yandex_folder_path) and os.path.isfile(browser_executable_path)

    def is_program_installed_by_shortcut(self, program_name):
        if (program_name == "1C"):
            return False
        shortcut_dirs = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.join(os.environ.get('APPDATA', ''), r"Microsoft\Windows\Start Menu\Programs"),
        ]
        for shortcut_dir in shortcut_dirs:
            if not os.path.exists(shortcut_dir):
                continue
            for root, dirs, files in os.walk(shortcut_dir):
                for file in files:
                    if file.lower().endswith('.lnk'):
                        shortcut_name = os.path.splitext(file)[0].lower()
                        if program_name.lower() in shortcut_name:
                            return True
        return False
