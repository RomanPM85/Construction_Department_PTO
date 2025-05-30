Создание полноценного VPN-сервера на Python с Flask - это сложная задача, так как Flask - это веб-фреймворк, а VPN требует работы на более низком уровне сети. Однако, я покажу вам несколько подходов: от простого прокси-сервера до более продвинутых решений.

## 1. Простой HTTP/HTTPS прокси-сервер на Flask

```python
from flask import Flask, request, Response
import requests
from urllib.parse import urlparse
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Конфигурация
ALLOWED_DOMAINS = []  # Пустой список = все домены разрешены
BLOCK_DOMAINS = ['example-blocked.com']

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    # Получаем целевой URL из параметров
    target_url = request.args.get('url')
    
    if not target_url:
        return "Укажите URL в параметре ?url=", 400
    
    # Проверка доменов
    parsed_url = urlparse(target_url)
    domain = parsed_url.netloc
    
    if domain in BLOCK_DOMAINS:
        return f"Домен {domain} заблокирован", 403
    
    if ALLOWED_DOMAINS and domain not in ALLOWED_DOMAINS:
        return f"Домен {domain} не в списке разрешенных", 403
    
    try:
        # Подготавливаем заголовки
        headers = {key: value for key, value in request.headers if key != 'Host'}
        
        # Выполняем запрос
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True
        )
        
        # Подготавливаем ответ
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in response.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        # Возвращаем ответ
        return Response(
            response.iter_content(chunk_size=10240),
            status=response.status_code,
            headers=headers
        )
        
    except Exception as e:
        logging.error(f"Ошибка при проксировании: {str(e)}")
        return f"Ошибка прокси: {str(e)}", 500

@app.route('/status')
def status():
    return {"status": "Прокси-сервер работает", "version": "1.0"}

if __name__ == '__main__':
    print("Прокси-сервер запущен на http://localhost:5000")
    print("Использование: http://localhost:5000/?url=https://example.com")
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## 2. SOCKS5 прокси-сервер (более близко к VPN)

```python
import socket
import threading
import select
import struct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SOCKS5Server:
    def __init__(self, host='0.0.0.0', port=1080):
        self.host = host
        self.port = port
        self.username = "user"  # Для аутентификации
        self.password = "pass"
        
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        
        logger.info(f"SOCKS5 сервер запущен на {self.host}:{self.port}")
        
        while True:
            client, addr = server.accept()
            logger.info(f"Новое подключение от {addr}")
            threading.Thread(target=self.handle_client, args=(client,)).start()
    
    def handle_client(self, client):
        try:
            # Фаза приветствия
            version, nmethods = struct.unpack("!BB", client.recv(2))
            methods = client.recv(nmethods)
            
            # Отправляем метод аутентификации (0x02 = username/password)
            client.send(b"\x05\x02")
            
            # Получаем аутентификационные данные
            version = client.recv(1)
            username_len = struct.unpack("!B", client.recv(1))[0]
            username = client.recv(username_len).decode()
            password_len = struct.unpack("!B", client.recv(1))[0]
            password = client.recv(password_len).decode()
            
            # Проверяем учетные данные
            if username == self.username and password == self.password:
                client.send(b"\x01\x00")  # Успех
            else:
                client.send(b"\x01\x01")  # Ошибка
                client.close()
                return
            
            # Получаем запрос на соединение
            version, cmd, _, address_type = struct.unpack("!BBBB", client.recv(4))
            
            if address_type == 1:  # IPv4
                addr = socket.inet_ntoa(client.recv(4))
            elif address_type == 3:  # Доменное имя
                addr_len = struct.unpack("!B", client.recv(1))[0]
                addr = client.recv(addr_len).decode()
            else:
                client.close()
                return
            
            port = struct.unpack("!H", client.recv(2))[0]
            
            logger.info(f"Запрос соединения к {addr}:{port}")
            
            # Устанавливаем соединение с целевым сервером
            if cmd == 1:  # CONNECT
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((addr, port))
                
                # Отправляем успешный ответ
                reply = b"\x05\x00\x00\x01"
                reply += socket.inet_aton("0.0.0.0") + struct.pack("!H", 0)
                client.send(reply)
                
                # Проксируем данные
                self.proxy_data(client, remote)
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            client.close()
    
    def proxy_data(self, client, remote):
        while True:
            r, w, e = select.select([client, remote], [], [])
            
            if client in r:
                data = client.recv(4096)
                if not data:
                    break
                remote.send(data)
            
            if remote in r:
                data = remote.recv(4096)
                if not data:
                    break
                client.send(data)
        
        client.close()
        remote.close()

# Запуск SOCKS5 сервера
if __name__ == "__main__":
    server = SOCKS5Server(port=1080)
    server.start()
```

## 3. Простой VPN-подобный туннель с шифрованием

```python
import socket
import threading
import ssl
import os
from cryptography.fernet import Fernet
import json
import base64

class SecureTunnelServer:
    def __init__(self, host='0.0.0.0', port=8443):
        self.host = host
        self.port = port
        self.clients = {}
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
    def generate_ssl_context(self):
        """Создаем SSL контекст для безопасного соединения"""
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Генерируем самоподписанный сертификат (для продакшена используйте настоящий)
        if not os.path.exists('server.pem'):
            os.system('openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes -subj "/CN=localhost"')
        
        context.load_cert_chain('server.pem')
        return context
    
    def start(self):
        context = self.generate_ssl_context()
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen(5)
            
            with context.wrap_socket(sock, server_side=True) as ssock:
                print(f"Secure Tunnel Server запущен на {self.host}:{self.port}")
                print(f"Ключ шифрования: {self.encryption_key.decode()}")
                
                while True:
                    client_socket, addr = ssock.accept()
                    print(f"Новое подключение от {addr}")
                    threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, addr)
                    ).start()
    
    def handle_client(self, client_socket, addr):
        try:
            # Аутентификация клиента
            auth_data = client_socket.recv(1024)
            auth_info = json.loads(self.cipher.decrypt(auth_data).decode())
            
            if auth_info.get('username') and auth_info.get('password'):
                # Простая проверка (в реальности используйте безопасное хранение паролей)
                if self.authenticate(auth_info['username'], auth_info['password']):
                    client_socket.send(self.cipher.encrypt(b"AUTH_OK"))
                    self.clients[addr] = {
                        'socket': client_socket,
                        'username': auth_info['username']
                    }
                    self.tunnel_traffic(client_socket, addr)
                else:
                    client_socket.send(self.cipher.encrypt(b"AUTH_FAILED"))
                    client_socket.close()
            
        except Exception as e:
            print(f"Ошибка с клиентом {addr}: {e}")
        finally:
            if addr in self.clients:
                del self.clients[addr]
            client_socket.close()
    
    def authenticate(self, username, password):
        # Простая проверка (используйте хеширование паролей в продакшене)
        valid_users = {
            'admin': 'secure_password',
            'user': 'user_password'
        }
        return valid_users.get(username) == password
    
    def tunnel_traffic(self, client_socket, addr):
        """Обработка туннелированного трафика"""
        while True:
            try:
                # Получаем зашифрованные данные от клиента
                encrypted_data = client_socket.recv(4096)
                if not encrypted_data:
                    break
                
                # Расшифровываем
                data = self.cipher.decrypt(encrypted_data)
                request = json.loads(data.decode())
                
                # Обрабатываем запрос
                if request['type'] == 'HTTP':
                    response = self.handle_http_request(request['data'])
                    encrypted_response = self.cipher.encrypt(response.encode())
                    client_socket.send(encrypted_response)
                
            except Exception as e:
                print(f"Ошибка туннеля: {e}")
                break
    
    def handle_http_request(self, request_data):
        """Обработка HTTP запросов через туннель"""
        # Здесь можно реализовать проксирование HTTP запросов
        return json.dumps({
            'status': 'OK',
            'data': 'Response data'
        })

# Клиентская часть
class SecureTunnelClient:
    def __init__(self, server_host, server_port, encryption_key):
        self.server_host = server_host
        self.server_port = server_port
        self.cipher = Fernet(encryption_key)
        
    def connect(self, username, password):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((self.server_host, self.server_port)) as sock:
            with context.wrap_socket(sock, server_hostname=self.server_host) as ssock:
                # Аутентификация
                auth_data = json.dumps({
                    'username': username,
                    'password': password
                }).encode()
                
                ssock.send(self.cipher.encrypt(auth_data))
                response = self.cipher.decrypt(ssock.recv(1024))
                
                if response == b"AUTH_OK":
                    print("Успешная аутентификация!")
                    return ssock
                else:
                    print("Ошибка аутентификации!")
                    return None

# Запуск сервера
if __name__ == "__main__":
    server = SecureTunnelServer()
    server.start()
```

## 4. Интеграция с Flask для веб-интерфейса управления

````artifact
id: flask-vpn-manager
name: Flask VPN Manager
type: code.python
content: |-
  from flask import Flask, render_template, request, jsonify, session
  from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
  import sqlite3
  import hashlib
  import secrets
  import datetime
  import json
  import threading
  from dataclasses import dataclass
  import subprocess
  import psutil

  app = Flask(__name__)
  app.secret_key = secrets.token_hex(32)

  # Конфигурация
  login_manager = LoginManager()
  login_manager.init_app(app)
  login_manager.login_view = 'login'

  # База данных
  def init_db():
      conn = sqlite3.connect('vpn_server.db')
      c = conn.cursor()
      
      # Таблица пользователей
      c.execute('''CREATE TABLE IF NOT EXISTS users
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
      
      # Таблица VPN подключений
      c.execute('''CREATE TABLE IF NOT EXISTS connections
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ip_address TEXT,
                    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    disconnected_at TIMESTAMP,
                    bytes_sent INTEGER DEFAULT 0,
                    bytes_received INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id))''')
      
      # Таблица конфигураций
      c.execute('''CREATE TABLE IF NOT EXISTS configs
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    config_name TEXT,
                    config_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id))''')
      
      conn.commit()
      conn.close()

  @dataclass
  class User(UserMixin):
      id: int
      username: str
      email: str
      is_admin: bool

  @login_manager.user_loader
  def load_user(user_id):
      conn = sqlite3.connect('vpn_server.db')
      c = conn.cursor()
      c.execute("SELECT id, username, email, is_admin FROM users WHERE id = ?", (user_id,))
      user_data = c.fetchone()
      conn.close()
      
      if user_data:
          return User(*user_data)
      return None

  class VPNManager:
      def __init__(self):
          self.active_connections = {}
          self.server_status = "stopped"
          self.stats = {
              'total_connections': 0,
              'bytes_transferred': 0,
              'uptime': 0
          }
      
      def get_system_stats(self):
          """Получение статистики системы"""
          return {
              'cpu_usage': psutil.cpu_percent(interval=1),
              'memory_usage': psutil.virtual_memory().percent,
              'network_io': psutil.net_io_counters()._asdict(),
              'active_connections': len(self.active_connections),
              'server_status': self.server_status
          }
      
      def generate_client_config(self, user_id, config_name):
          """Генерация конфигурации для клиента"""
          config = {
              'server': 'your-server-ip',
              'port': 1194,
              'protocol': 'udp',
              'cipher': 'AES-256-CBC',
              'auth': 'SHA256',
              'client_cert': self._generate_certificate(user_id),
              'ca_cert': self._get_ca_certificate()
          }
          
          # Сохраняем конфигурацию в БД
          conn = sqlite3.connect('vpn_server.db')
          c = conn.cursor()
          c.execute("INSERT INTO configs (user_id, config_name, config_data) VALUES (?, ?, ?)",
                    (user_id, config_name, json.dumps(config)))
          conn.commit()
          conn.close()
          
          return config
      
      def _generate_certificate(self, user_id):
          """Генерация сертификата для пользователя"""
          # В реальности здесь должна быть генерация настоящего сертификата
          return f"-----BEGIN CERTIFICATE-----\nMOCK_CERTIFICATE_FOR_USER_{user_id}\n-----END CERTIFICATE-----"
      
      def _get_ca_certificate(self):
          """Получение CA сертификата"""
          return "-----BEGIN CERTIFICATE-----\nMOCK_CA_CERTIFICATE\n-----END CERTIFICATE-----"

  vpn_manager = VPNManager()

  # Маршруты Flask
  @app.route('/')
  @login_required
  def dashboard():
      stats = vpn_manager.get_system_stats()
      
      # Получаем последние подключения
      conn = sqlite3.connect('vpn_server.db')
      c = conn.cursor()
      c.execute("""SELECT u.username, c.ip_address, c.connected_at, c.bytes_sent, c.bytes_received
                   FROM connections c
                   JOIN users u ON c.user_id = u.id
                   ORDER BY c.connected_at DESC
                   LIMIT 10""")
      recent_connections = c.fetchall()
      conn.close()
      
      return render_template('dashboard.html', 
                           stats=stats, 
                           connections=recent_connections)

  @app.route('/api/stats')
  @login_required
  def api_stats():
      return jsonify(vpn_manager.get_system_stats())

  @app.route('/api/connections')
  @login_required
  def api_connections():
      return jsonify(vpn_manager.active_connections)

  @app.route('/users')
  @login_required
  def users():
      if not current_user.is_admin:
          return "Access denied", 403
      
      conn = sqlite3.connect('vpn_server.db')
      c = conn.cursor()
      c.execute("SELECT id, username, email, created_at FROM users")
      users = c.fetchall()
      conn.close()
      
      return render_template('users.html', users=users)

  @app.route('/generate_config', methods=['POST'])
  @login_required
  def generate_config():
      config_name = request.form.get('config_name', 'default')
      config = vpn_manager.generate_client_config(current_user.id, config_name)
      
      # Генерируем .ovpn файл
      ovpn_content = f"""client
  dev tun
  proto {config['protocol']}
  remote {config['server']} {config['port']}
  resolv-retry infinite
  nobind
  persist-key
  persist-tun
  cipher {config['cipher']}
  auth {config['auth']}
  verb 3

  <ca>
  {config['ca_cert']}
  </ca>

  <cert>
  {config['client_cert']}
  </cert>
  """
      
      return jsonify({
          'status': 'success',
          'config': ovpn_content,
          'filename': f'{config_name}.ovpn'
      })

  @app.route('/server/start', methods=['POST'])
  @login_required
  def start_server():
      if not current_user.is_admin:
          return jsonify({'error': 'Access denied'}), 403
      
      # Здесь должен быть код запуска VPN сервера
      vpn_manager.server_status = "running"
      return jsonify({'status': 'success', 'message': 'VPN server started'})

  @app.route('/server/stop', methods=['POST'])
  @login_required
  def stop_server():
      if not current_user.is_admin:
          return jsonify({'error': 'Access denied'}), 403
      
      vpn_manager.server_status = "stopped"
      return jsonify({'status': 'success', 'message': 'VPN server stopped'})

  # HTML шаблоны (в реальном проекте должны быть в папке templates)
  dashboard_html = """
  <!DOCTYPE html>
  <html>
  <head>
      <title>VPN Server Dashboard</title>
      <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
          .stat-card { background: #f0f0f0; padding: 20px; border-radius: 8px; }
          .stat-value { font-size: 2em; font-weight: bold; color: #333; }
          .stat-label { color: #666; margin-top: 5px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
          .status-running { color: green; }
          .status-stopped { color: red; }
          button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
          button:hover { background: #0056b3; }
      </style>
  </head>
  <body>
      <h1>VPN Server Dashboard</h1>
      
      <div class="stats">
          <div class="stat-card">
              <div class="stat-value">{{ stats.cpu_usage }}%</div>
              <div class="stat-label">CPU Usage</div>
          </div>
          <div class="stat-card">
              <div class="stat-value">{{ stats.memory_usage }}%</div>
              <div class="stat-label">Memory Usage</div>
          </div>
          <div class="stat-card">
              <div class="stat-value">{{ stats.active_connections }}</div>
              <div class="stat-label">Active Connections</div>
          </div>
          <div class="stat-card">
              <div class="stat-value class="{{ 'status-running' if stats.server_status == 'running' else 'status-stopped' }}">
                  {{ stats.server_status }}
              </div>
              <div class="stat-label">Server Status</div>
          </div>
      </div>
      
      <h2>Recent Connections</h2>
      <table>
          <thead>
              <tr>
                  <th>Username</th>
                  <th>IP Address</th>
                  <th>Connected At</th>
                  <th>Bytes Sent</th>
                  <th>Bytes Received</th>
              </tr>
          </thead>
          <tbody>
              {% for conn in connections %}
              <tr>
                  <td>{{ conn[0] }}</td>
                  <td>{{ conn[1] }}</td>
                  <td>{{ conn[2] }}</td>
                  <td>{{ conn[3] }}</td>
                  <td>{{ conn[4] }}</td>
              </tr>
              {% endfor %}
          </tbody>
      </table>
      
      <div style="margin-top: 30px;">
          <button onclick="generateConfig()">Generate Client Config</button>
          <button onclick="toggleServer()">Toggle Server</button>
      </div>
      
      <script>
          function generateConfig() {
              fetch('/generate_config', { method: 'POST' })
                  .then(response => response.json())
                  .then(data => {
                      if (data.status === 'success') {
                          // Скачиваем конфигурацию
                          const blob = new Blob([data.config], { type: 'text/plain' });
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = data.filename;
                          a.click();
                      }
                  });
          }
          
          function toggleServer() {
              const action = '{{ stats.server_status }}' === 'running' ? 'stop' : 'start';
              fetch(`/server/${action}`, { method: 'POST' })
                  .then(response => response.json())
                  .then(data => {
                      alert(data.message);
                      location.reload();
                  });
          }
          
          // Обновление статистики каждые 5 секунд
          setInterval(() => {
              fetch('/api/stats')
                  .then(response => response.json())
                  .then(data => {
                      // Обновляем UI
                      console.log(data);
                  });
          }, 5000);
      </script>
  </body>
  </html>
  """

  if __name__ == '__main__':
      init_db()
      app.run(host='0.0.0.0', port=5000, debug=True)
````

## Важные замечания:

1. **Безопасность**: Приведенные примеры - это упрощенные демонстрации. Для production используйте:
   - Настоящие SSL сертификаты
   - Безопасное хранение паролей (bcrypt, argon2)
   - Правильную обработку ошибок
   - Логирование и мониторинг

2. **Производительность**: Python не самый быстрый язык для VPN. Для production рассмотрите:
   - OpenVPN
   - WireGuard
   - StrongSwan

3. **Альтернативы**: Вместо создания VPN с нуля, можно использовать Python для управления существующими VPN решениями:
   ```python
   import subprocess
   
   # Управление OpenVPN
   subprocess.run(['openvpn', '--config', 'server.conf'])
   
   # Управление WireGuard
   subprocess.run(['wg-quick', 'up', 'wg0'])
   ```

4. **Законодательство**: Убедитесь, что использование VPN разрешено в вашей юрисдикции.

Какой подход вас больше интересует? Могу подробнее рассказать о конкретной реализации.