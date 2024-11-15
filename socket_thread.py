from PyQt6.QtCore import QThread, pyqtSignal
import socket
class SocketThread(QThread):
    """Поток для обработки соединения с сервером."""
    response_received = pyqtSignal(str)

    def __init__(self, host, port, command):
        super().__init__()
        self.host = host
        self.port = port
        self.command = command

    def run(self):
        """Отправка команды и получение ответа от сервера."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(self.command.encode('utf-8'))

                response = s.recv(1024).decode('utf-8')
                self.response_received.emit(response)
        except Exception as e:
            self.response_received.emit(f"Ошибка: {str(e)}")