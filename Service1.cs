using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.ServiceProcess;
using System.Text;
using System.Threading;
using Microsoft.Win32;

namespace InstallService
{
    public partial class Service1 : ServiceBase
    {
        private TcpListener _listener;
        private Thread _listenerThread;
        private readonly int _port = 9000; // Укажите порт для прослушивания

        public Service1()
        {
            InitializeComponent();
        }

        protected override void OnStart(string[] args)
        {
            _listenerThread = new Thread(StartListening);
            _listenerThread.Start();
        }

        protected override void OnStop()
        {
            _listener?.Stop();
            _listenerThread?.Abort();
        }

        private void StartListening()
        {
            _listener = new TcpListener(IPAddress.Any, _port);
            _listener.Start();
            WriteLog($"Service started. Listening on port {_port}");

            while (true)
            {
                try
                {
                    TcpClient client = _listener.AcceptTcpClient();
                    Thread clientThread = new Thread(HandleClient);
                    clientThread.Start(client);
                }
                catch (Exception ex)
                {
                    WriteLog($"Error in StartListening: {ex.Message}");
                }
            }
        }

        private void HandleClient(object clientObj)
        {
            TcpClient client = clientObj as TcpClient;
            NetworkStream stream = client.GetStream();

            try
            {
                // Чтение команды от клиента
                byte[] buffer = new byte[1024];
                int bytesRead = stream.Read(buffer, 0, buffer.Length);
                string request = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                WriteLog($"Received request: {request}");

                // Разбор команды
                string[] parts = request.Split(' ');
                if (parts.Length < 2 || parts[0] != "install")
                {
                    SendResponse(stream, "Invalid command. Use: install <program_name>");
                    return;
                }

                string programName = parts[1];
                // Логика установки
                bool success = InstallApplication(programName);
                if (success)
                {
                    SendResponse(stream, $"Программа '{programName}' установлена успешно.");
                }
                else
                {
                    SendResponse(stream, $"Не удалось установить программу '{programName}'. Проверьте записи логов.");
                }
            }
            catch (Exception ex)
            {
                WriteLog($"Error in HandleClient: {ex.Message}");
                SendResponse(stream, $"Error: {ex.Message}");
            }
            finally
            {
                stream.Close();
                client.Close();
            }
        }
        private bool InstallApplication(string programName)
        {
            try
            {
                string argument = "/S";
                // Список программ и их путей к установщикам
                var installers = new System.Collections.Generic.Dictionary<string, string>
        {
            { "notepad++", @"\\filearch\Отдел технической поддержки\AppInstallerSoftware\npp.8.7.Installer.x64.exe" },
            { "chrome", @"\\filearch\Отдел технической поддержки\AppInstallerSoftware\ChromeStandaloneSetup64.exe" },
            { "yandex", @"\\filearch\Отдел технической поддержки\AppInstallerSoftware\Yandex.exe" },
            { "1c", @"\\filearch\Отдел технической поддержки\AppInstallerSoftware\8.3.24.1667\setup.exe" },
            { "firefox", @"\\filearch\Отдел технической поддержки\AppInstallerSoftware\firefox.exe" }
        };

                if (!installers.ContainsKey(programName.ToLower()))
                {
                    WriteLog($"Program '{programName}' not found in the installers list.");
                    return false;
                }

                string installerPath = installers[programName.ToLower()];
                if (!File.Exists(installerPath))
                {
                    WriteLog($"Installer not found: {installerPath}");
                    return false;
                }
                if (programName.ToLower() == "yandex") argument = "/silent";
                // Настройка процесса с передачей окружения пользователя
                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = installerPath,
                    Arguments = argument, // Аргумент для тихой установки (может меняться для разных установщиков)
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                // Добавление переменных окружения текущего пользователя
                startInfo.EnvironmentVariables["USERPROFILE"] = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                startInfo.EnvironmentVariables["APPDATA"] = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
                startInfo.EnvironmentVariables["LOCALAPPDATA"] = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
                startInfo.EnvironmentVariables["TEMP"] = Path.GetTempPath();
                startInfo.EnvironmentVariables["TMP"] = Path.GetTempPath();

                WriteLog($"Starting installation: {installerPath}");
                using (Process process = Process.Start(startInfo))
                {
                    if (process.WaitForExit(240000)) // Ожидание 4 минуты
                    {
                        if (process.ExitCode == 0)
                        {
                            WriteLog($"Installation completed successfully: {programName}");
                            return true;
                        }
                        else if (programName.ToLower() == "yandex" && (process.ExitCode == 3 || process.ExitCode == 1))
                        {
                            // Игнорируем коды выхода 1 и 3 для Yandex
                            WriteLog($"Installation completed successfully for Yandex Browser with ignored exit code {process.ExitCode}");
                            return true;
                        }
                        else
                        {
                            WriteLog($"Installation failed with exit code {process.ExitCode}: {programName}");
                            return false;
                        }
                    }
                    else
                    {
                        // Если процесс не завершился за 30 секунд, принудительно завершаем его
                        WriteLog($"Installation timed out for '{programName}', killing process.");
                        process.Kill();
                        process.WaitForExit(); // Убедимся, что процесс завершился
                        return false;
                    }
                }
            }
            catch (Exception ex)
            {
                WriteLog($"Error during installation of '{programName}': {ex.Message}");
                return false;
            }
        }



        private void SendResponse(NetworkStream stream, string message)
        {
            byte[] response = Encoding.UTF8.GetBytes(message);
            stream.Write(response, 0, response.Length);
        }

        private void WriteLog(string message)
        {
            // Определяем путь к директории программы
            string appDirectory = AppDomain.CurrentDomain.BaseDirectory;

            // Путь к лог-файлу
            string logPath = Path.Combine(appDirectory, "service.log");

            // Создаем директорию, если она не существует
            Directory.CreateDirectory(appDirectory);

            // Записываем сообщение в лог
            File.AppendAllText(logPath, $"{DateTime.Now}: {message}{Environment.NewLine}");
        }
    }
}
