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