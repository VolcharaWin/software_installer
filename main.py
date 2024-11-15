import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QMainWindow, \
    QHBoxLayout, QApplication, QLineEdit, QCheckBox, QListWidget, QListWidgetItem, QMessageBox
from checkinstall import CheckInstalledProgramsThread
from socket_thread import SocketThread

# Функция для загрузки стилей
def load_stylesheet(file_name):
    """Загружаем файл со стилями и применяем его."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_path, file_name)
    with open(file_path, 'r') as f:
        stylesheet = f.read()
    return stylesheet
class Program:
    """Класс для представления программы для установки."""

    def __init__(self, name):
        self.name = name
        self.checkbox = None
        self.is_installed = False  # Добавлено для отслеживания статуса установки

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(self.resource_path("gup_icon.ico")))
        self.install_queue = []  # Очередь программ для установки
        self.is_installing = False  # Флаг, чтобы отслеживать, идёт ли установка
        self.current_program = None  # Текущая устанавливаемая программа

        # Список программ для установки
        self.programs = [
            Program("Notepad++"),
            Program("Chrome"),
            Program("Yandex"),
            Program("1C"),
            Program("Firefox")
        ]

        self.init_ui()

        # Показываем загрузочный экран
        self.show_loading_overlay()

        # Запускаем проверку установленных программ в отдельном потоке
        self.check_thread = CheckInstalledProgramsThread(self.programs)
        self.check_thread.finished.connect(self.on_check_finished)
        self.check_thread.start()

    def resource_path(self, relative_path):
        """Возвращает абсолютный путь к ресурсу (работает для PyInstaller и разработки)."""
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def init_ui(self):
        """Инициализация элементов интерфейса."""
        self.setWindowTitle("Программа установки")

        # Кнопка для начала установки
        self.install_button = QPushButton("Установить")
        self.install_button.setFixedSize(150, 50)
        self.install_button.clicked.connect(self.start_installation)

        # Лейбл для отображения статуса установки
        self.installation_label = QLabel()

        # Поле для поиска программ
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Поиск...")
        self.search_bar.textChanged.connect(self.filter_list)

        # Чекбокс для выбора всех программ
        self.select_all_checkbox = QCheckBox("Выбрать все", self)
        self.select_all_checkbox.stateChanged.connect(self.select_all)

        # Список программ с чекбоксами
        self.program_list_widget = QListWidget(self)
        # Программы будут добавлены после проверки установленных

        # Layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.select_all_checkbox)
        top_layout.addWidget(self.search_bar)

        bot_layout = QHBoxLayout()
        bot_layout.addWidget(self.installation_label, alignment=Qt.AlignmentFlag.AlignCenter)
        bot_layout.addWidget(self.install_button, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.program_list_widget)
        main_layout.addLayout(bot_layout)

        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.resize(800, 600)

    def show_loading_overlay(self):
        """Показать экран загрузки."""
        self.overlay = QWidget(self)
        self.overlay.setObjectName("loadingOverlay")
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Текст загрузки
        self.loading_label = QLabel("Происходит проверка установленных приложений", self.overlay)
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Расположение текста в центре
        layout = QVBoxLayout(self.overlay)
        layout.addStretch()
        layout.addWidget(self.loading_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.overlay.show()

    def on_check_finished(self):
        """Обработчик завершения проверки установленных программ."""
        self.overlay.hide()
        self.add_programs_to_list()  # Теперь можем добавить программы в список

    def resizeEvent(self, event):
        """Обеспечивает корректное изменение размера оверлея при изменении окна."""
        super().resizeEvent(event)
        if hasattr(self, 'overlay') and self.overlay.isVisible():
            self.overlay.setGeometry(0, 0, self.width(), self.height())

    def add_programs_to_list(self):
        """Добавление программ в список с чекбоксами."""
        # Проверяем, есть ли уже чекбоксы, и сохраняем их состояния
        checkbox_states = {
            program.name: program.checkbox.isChecked() if program.checkbox else False
            for program in self.programs
        }

        self.program_list_widget.clear()

        # Сортировка программ: установленные внизу
        self.programs.sort(key=lambda p: p.is_installed)

        for program in self.programs:
            item_widget = QWidget()
            layout = QHBoxLayout()

            checkbox = QCheckBox(program.name)
            program.checkbox = checkbox  # Сохраняем ссылку на чекбокс

            # Восстанавливаем состояние чекбокса
            if program.name in checkbox_states:
                checkbox.setChecked(checkbox_states[program.name])

            # Блокируем чекбоксы для установленных программ
            if program.is_installed and program.name != "1C":
                checkbox.setEnabled(False)
            else:
                checkbox.setEnabled(True)

            layout.addWidget(checkbox)
            item_widget.setLayout(layout)

            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.program_list_widget.addItem(list_item)
            self.program_list_widget.setItemWidget(list_item, item_widget)

    def filter_list(self):
        """Фильтрация программ по введенному тексту."""
        filter_text = self.search_bar.text().lower()
        for i in range(self.program_list_widget.count()):
            item = self.program_list_widget.item(i)
            program_name = self.program_list_widget.itemWidget(item).findChild(QCheckBox).text().lower()
            item.setHidden(filter_text not in program_name)

    def select_all(self):
        """Выбор или снятие выбора всех программ."""
        select_all = self.select_all_checkbox.isChecked()
        for program in self.programs:
            if not program.is_installed:
                program.checkbox.setChecked(select_all)

    def start_installation(self):
        """Инициализация очереди установки."""
        # Формируем очередь программ
        self.install_queue = [program for program in self.programs if program.checkbox.isChecked()]

        if not self.install_queue:
            QMessageBox.warning(self, "Ошибка", "Не выбрана ни одна программа для установки.")
            return

        # Блокируем кнопку установки
        self.install_button.setEnabled(False)
        self.installation_label.setText("Идёт установка...")
        self.is_installing = True
        # Запускаем установку первой программы из очереди
        self.process_next_installation()

    def process_next_installation(self):
        """Устанавливаем следующую программу из очереди."""
        if not self.install_queue:
            # Если очередь пуста, разблокируем кнопку
            self.installation_label.setText("Установка завершена.")
            self.install_button.setEnabled(True)
            self.is_installing = False
            return

        # Берём следующую программу из очереди
        self.current_program = self.install_queue.pop(0)
        self.installation_label.setText(f"Идёт установка: {self.current_program.name}")
        self.send_command(self.current_program.name)

    def send_command(self, program_name):
        """Отправка команды на сервер."""
        host = '127.0.0.1'  # IP-адрес сервера
        port = 9000  # Порт сервера

        command = f"install {program_name}"
        self.socket_thread = SocketThread(host, port, command)
        self.socket_thread.response_received.connect(self.handle_response)
        self.socket_thread.start()

    def handle_response(self, response):
        """Обработка ответа от сервера."""
        QMessageBox.information(self, "Ответ от сервера", response)

        # Обновляем статус программы
        if "установлена успешно" in response.lower():
            self.current_program.is_installed = True
            self.add_programs_to_list()  # Обновляем список программ

        # Переходим к следующей программе из очереди
        self.process_next_installation()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Загружаем и применяем стили
    app.setStyleSheet(load_stylesheet("styles.qss"))  # Укажите путь к вашему файлу стилей

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
