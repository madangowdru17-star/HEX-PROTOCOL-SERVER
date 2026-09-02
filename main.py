import os
import json
import secrets
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sqlite3
from contextlib import contextmanager
import copy

app = FastAPI(title="HEX Protocol System", version="6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "hexadmin2024"

# Use /tmp for Railway persistent storage
DB_PATH = "/tmp/hex_config.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        # Config table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT,
                updated_at TIMESTAMP
            )
        """)
        # Insert default if not exists
        conn.execute("""
            INSERT OR IGNORE INTO config (id, data, updated_at) 
            VALUES (1, ?, ?)
        """, (json.dumps(DEFAULT_CONFIG), datetime.now().isoformat()))
        
        # API Keys table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                name TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        # Logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                timestamp TIMESTAMP,
                details TEXT
            )
        """)
        conn.commit()

# Default config
DEFAULT_CONFIG = {
    "maintenance": True,
    "root_maintenance": False,
    "nonroot_maintenance": False,
    "freefire_maintenance": False,
    "freefire_max_maintenance": False,
    
    "master_key": "HEXPROXY999",
    "master_key_expiry": "2026-12-31T23:59:59.000000",
    
    "login_name": "HEX PROXY XOS V6",
    "app_name": "🚨 LAUDA CRACK HOGA? 😂 BAHANCHOD, DADDY'S HERE — HEX 😘 KID, GO FUCK YOUR MOTHER"
    
    "maintenance_message": "We are performing scheduled maintenance. Please join our Telegram for updates.",
    "telegram_link": "https://t.me/+_s4OBzblpi0zNzE1",
    "get_key_link": "https://t.me/+_s4OBzblpi0zNzE1",
    
    "logo_url": "https://i.ibb.co/Wpcb6Ydy/IMG-20260313-030403-360.jpg",
    "shizuku_logo_url": "https://i.ibb.co/JRjy2ZpC/20260808-044938.png",
    "freefire_logo_url": "https://i.ibb.co/nsqT2bjJ/Garena-Free-Fire-Icon.jpg",
    "freefire_max_logo_url": "https://i.ibb.co/Wv5pthbL/unnamed.webp",
    
    "api_base_url": "https://hex-protocol-server-production.up.railway.app",
    
    "update_available": False,
    "update_version": "2.1.0",
    "update_changelog": "- Fixed AimBot\n- Added new features\n- Performance improvements",
    "update_url": "https://github.com/madangowdru17-star/Apk/raw/refs/heads/main/generated_sign.apk",
    
    "assets_version": "9.9",
    "assets": [
        {
            "name": "bg.mp4",
            "url": "https://github.com/madangowdru17-star/Assistant/raw/refs/heads/main/bg.mp4"
        }
    ],
    
    "freefire_buttons": [
        {
            "id": "ff_AMSILENT_LOCATION",
            "name": "AMSILENT_LOCATION",
            "url": "https://raw.githubusercontent.com/madangowdru17-star/Assistant/refs/heads/main/localconfig.json",
            "urlKeyTxt": "https://raw.githubusercontent.com/madangowdru17-star/Assistant/refs/heads/main/key.txt",
            "enabled": True,
            "maintenance": False,
            "persist": True
        },
        {
            "id": "ff_drag",
            "name": "Chest HS 95%-Sensi",
            "url": "https://raw.githubusercontent.com/madangowdru17-star/Assistant/refs/heads/main/localconfig.json",
            "urlKeyTxt": "",
            "enabled": True,
            "maintenance": False,
            "persist": False
        }
    ],
    
    "freefire_max_buttons": [
        {
            "id": "max_drag_safe",
            "name": "DRAG HS 85% SAFE",
            "url": "https://raw.githubusercontent.com/madangowdru17-star/HS-ANTENA/refs/heads/main/localconfig.json",
            "urlKeyTxt": "",
            "enabled": True,
            "maintenance": False,
            "persist": False
        }
    ],
    
    "root_libs": []
}

# Initialize DB
init_db()

def load_config():
    """Load config from DATABASE - not file"""
    try:
        with get_db() as conn:
            row = conn.execute("SELECT data FROM config WHERE id = 1").fetchone()
            if row:
                return json.loads(row["data"])
            else:
                # Insert default
                conn.execute(
                    "INSERT OR REPLACE INTO config (id, data, updated_at) VALUES (1, ?, ?)",
                    (json.dumps(DEFAULT_CONFIG), datetime.now().isoformat())
                )
                conn.commit()
                return copy.deepcopy(DEFAULT_CONFIG)
    except Exception as e:
        print(f"Load error: {e}")
        return copy.deepcopy(DEFAULT_CONFIG)

def save_config(config):
    """Save config to DATABASE - not file"""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO config (id, data, updated_at) VALUES (1, ?, ?)",
                (json.dumps(config), datetime.now().isoformat())
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False

def log_action(action, details=""):
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO audit_log (action, timestamp, details) VALUES (?, ?, ?)",
                (action, datetime.now().isoformat(), details)
            )
            conn.commit()
    except:
        pass

def generate_api_key():
    return "HEX-" + secrets.token_hex(16).upper()

def create_api_key(name, expires_days=30):
    key = generate_api_key()
    created_at = datetime.now()
    expires_at = created_at + timedelta(days=expires_days) if expires_days > 0 else None
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO api_keys (key, name, created_at, expires_at, is_active, usage_count) VALUES (?, ?, ?, ?, 1, 0)",
            (key, name, created_at.isoformat(), expires_at.isoformat() if expires_at else None)
        )
        conn.commit()
    
    return key

# Simple HTML with working JS
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>HEX Protocol Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; color: #333; }
        .header { background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; text-align: center; color: white; }
        .nav { display: flex; flex-wrap: wrap; gap: 5px; padding: 10px; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .nav button { padding: 10px 20px; background: #f0f0f0; color: #333; border: none; cursor: pointer; border-radius: 5px; }
        .nav button.active { background: #667eea; color: white; }
        .content { padding: 20px; max-width: 1000px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h2 { color: #667eea; margin-bottom: 15px; }
        input, textarea, select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background: #667eea; color: white; border: none; cursor: pointer; border-radius: 5px; margin: 5px; }
        button.danger { background: #ff4444; }
        button.success { background: #00c851; }
        .toggle-container { display: flex; align-items: center; gap: 10px; margin: 15px 0; }
        .toggle { position: relative; width: 50px; height: 25px; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #ccc; transition: .4s; border-radius: 25px; }
        .slider:before { position: absolute; content: ""; height: 19px; width: 19px; left: 3px; bottom: 3px; background: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background: #00c851; }
        input:checked + .slider:before { transform: translateX(25px); }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
        .badge-green { background: #d4edda; color: #155724; }
        .badge-red { background: #f8d7da; color: #721c24; }
        .hidden { display: none; }
        .api-key { font-family: monospace; background: #f0f0f0; padding: 5px 10px; border-radius: 3px; }
        .toast { position: fixed; top: 20px; right: 20px; padding: 15px 25px; border-radius: 5px; color: white; z-index: 1000; }
        .toast-success { background: #00c851; }
        .toast-error { background: #ff4444; }
    </style>
</head>
<body>
    <div class="header">
        <h1>HEX Protocol Admin</h1>
        <p>Control Center v6.0</p>
    </div>
    
    <div class="nav">
        <button class="active" onclick="showTab('dashboard', this)">Dashboard</button>
        <button onclick="showTab('general', this)">General</button>
        <button onclick="showTab('maintenance', this)">Maintenance</button>
        <button onclick="showTab('apikeys', this)">API Keys</button>
    </div>
    
    <div class="content">
        <div id="dashboard" class="tab">
            <div class="card">
                <h2>System Status</h2>
                <p>Maintenance: <span id="maint-status" class="badge badge-green">OFF</span></p>
                <p>App Name: <span id="app-name">-</span></p>
                <p>API Keys: <span id="key-count">0</span></p>
            </div>
        </div>
        
        <div id="general" class="tab hidden">
            <div class="card">
                <h2>General Settings</h2>
                <label>App Name</label>
                <input type="text" id="app_name">
                <label>Login Name</label>
                <input type="text" id="login_name">
                <label>Telegram Link</label>
                <input type="text" id="telegram_link">
                <label>Maintenance Message</label>
                <textarea id="maintenance_message"></textarea>
                <br>
                <button class="success" onclick="saveGeneral()">SAVE</button>
            </div>
        </div>
        
        <div id="maintenance" class="tab hidden">
            <div class="card">
                <h2>Maintenance Control</h2>
                <p style="color: green; margin-bottom: 10px;">Changes save automatically!</p>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="maintenance" onchange="saveMaintenance()">
                        <span class="slider"></span>
                    </label>
                    <strong>Global Maintenance</strong>
                </div>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="root_maintenance" onchange="saveMaintenance()">
                        <span class="slider"></span>
                    </label>
                    <strong>Root Maintenance</strong>
                </div>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="nonroot_maintenance" onchange="saveMaintenance()">
                        <span class="slider"></span>
                    </label>
                    <strong>Non-Root Maintenance</strong>
                </div>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="freefire_maintenance" onchange="saveMaintenance()">
                        <span class="slider"></span>
                    </label>
                    <strong>Free Fire Maintenance</strong>
                </div>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="freefire_max_maintenance" onchange="saveMaintenance()">
                        <span class="slider"></span>
                    </label>
                    <strong>Free Fire MAX Maintenance</strong>
                </div>
            </div>
        </div>
        
        <div id="apikeys" class="tab hidden">
            <div class="card">
                <h2>API Key Management</h2>
                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                    <input type="text" id="key-name" placeholder="Key Name" style="flex: 1;">
                    <select id="key-expiry" style="width: 150px;">
                        <option value="7">7 Days</option>
                        <option value="30" selected>30 Days</option>
                        <option value="90">90 Days</option>
                        <option value="0">Never</option>
                    </select>
                    <button class="success" onclick="generateKey()">GENERATE</button>
                </div>
                <div id="keys-list"></div>
            </div>
        </div>
    </div>
    
    <script>
        let config = null;
        
        async function loadConfig() {
            try {
                const res = await fetch('/api/admin/config');
                config = await res.json();
                updateUI();
            } catch(e) {
                console.error('Error:', e);
            }
        }
        
        async function saveConfig() {
            try {
                const res = await fetch('/api/admin/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });
                const data = await res.json();
                if (data.success) {
                    showToast('SAVED!', 'success');
                } else {
                    showToast('FAILED!', 'error');
                }
            } catch(e) {
                showToast('ERROR: ' + e.message, 'error');
            }
        }
        
        function updateUI() {
            if (!config) return;
            
            // Dashboard
            document.getElementById('maint-status').textContent = config.maintenance ? 'ON' : 'OFF';
            document.getElementById('maint-status').className = 'badge ' + (config.maintenance ? 'badge-red' : 'badge-green');
            document.getElementById('app-name').textContent = config.app_name || '-';
            
            // General
            document.getElementById('app_name').value = config.app_name || '';
            document.getElementById('login_name').value = config.login_name || '';
            document.getElementById('telegram_link').value = config.telegram_link || '';
            document.getElementById('maintenance_message').value = config.maintenance_message || '';
            
            // Maintenance - CRITICAL FIX
            document.getElementById('maintenance').checked = config.maintenance === true;
            document.getElementById('root_maintenance').checked = config.root_maintenance === true;
            document.getElementById('nonroot_maintenance').checked = config.nonroot_maintenance === true;
            document.getElementById('freefire_maintenance').checked = config.freefire_maintenance === true;
            document.getElementById('freefire_max_maintenance').checked = config.freefire_max_maintenance === true;
        }
        
        function showTab(name, btn) {
            document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden'));
            document.getElementById(name).classList.remove('hidden');
            document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (name === 'apikeys') loadKeys();
        }
        
        async function saveGeneral() {
            config.app_name = document.getElementById('app_name').value;
            config.login_name = document.getElementById('login_name').value;
            config.telegram_link = document.getElementById('telegram_link').value;
            config.maintenance_message = document.getElementById('maintenance_message').value;
            await saveConfig();
        }
        
        async function saveMaintenance() {
            config.maintenance = document.getElementById('maintenance').checked;
            config.root_maintenance = document.getElementById('root_maintenance').checked;
            config.nonroot_maintenance = document.getElementById('nonroot_maintenance').checked;
            config.freefire_maintenance = document.getElementById('freefire_maintenance').checked;
            config.freefire_max_maintenance = document.getElementById('freefire_max_maintenance').checked;
            await saveConfig();
            updateUI();
        }
        
        async function generateKey() {
            const name = document.getElementById('key-name').value || 'User';
            const expiry = parseInt(document.getElementById('key-expiry').value);
            
            const res = await fetch('/api/admin/keys/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name, expires_days: expiry})
            });
            const data = await res.json();
            
            if (data.success) {
                showToast('KEY GENERATED!', 'success');
                loadKeys();
            }
        }
        
        async function loadKeys() {
            const res = await fetch('/api/admin/keys');
            const keys = await res.json();
            document.getElementById('key-count').textContent = keys.length;
            
            const listDiv = document.getElementById('keys-list');
            listDiv.innerHTML = '';
            
            keys.forEach(key => {
                listDiv.innerHTML += '<div style="padding: 10px; border: 1px solid #ddd; margin-bottom: 10px; border-radius: 5px;">' +
                    '<div class="api-key">' + key.key + '</div>' +
                    '<div style="font-size: 12px; color: #666;">' + key.name + ' | Active: ' + (key.is_active ? 'YES' : 'NO') + '</div>' +
                    '<button class="danger" style="padding: 5px 10px; font-size: 12px;" onclick="deleteKey(' + key.id + ')">DELETE</button>' +
                    '</div>';
            });
        }
        
        async function deleteKey(id) {
            if (confirm('Delete this key?')) {
                const res = await fetch('/api/admin/keys/' + id, {method: 'DELETE'});
                const data = await res.json();
                if (data.success) {
                    showToast('KEY DELETED!', 'success');
                    loadKeys();
                }
            }
        }
        
        function showToast(message, type) {
            const toast = document.createElement('div');
            toast.className = 'toast toast-' + type;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 2000);
        }
        
        loadConfig();
    </script>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>HEX Protocol - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .login-box { background: white; padding: 40px; border-radius: 10px; width: 100%; max-width: 350px; box-shadow: 0 2px 20px rgba(0,0,0,0.1); }
        h1 { color: #667eea; text-align: center; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
        .error { color: #ff4444; text-align: center; margin-top: 10px; display: none; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>HEX PROTOCOL</h1>
        <input type="text" id="username" placeholder="Username">
        <input type="password" id="password" placeholder="Password">
        <button onclick="login()">LOGIN</button>
        <div class="error" id="error">Invalid credentials!</div>
    </div>
    
    <script>
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const res = await fetch('/api/admin/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: username, password: password})
            });
            
            const data = await res.json();
            
            if (data.success) {
                window.location.href = '/admin';
            } else {
                document.getElementById('error').style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""

# API Endpoints
@app.get("/api/config")
async def get_config():
    config = load_config()
    # Don't hide master key for now to debug
    return config

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "HEX Protocol System API", "version": "6.0"}

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page():
    return LOGIN_HTML

@app.post("/api/admin/login")
async def admin_login(request: Request):
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return {"success": True}
        return {"success": False}
    except:
        return {"success": False}

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    return ADMIN_HTML

@app.get("/api/admin/config")
async def admin_get_config():
    return load_config()

@app.post("/api/admin/config")
async def admin_update_config(request: Request):
    try:
        config_data = await request.json()
        success = save_config(config_data)
        if success:
            log_action("Config updated")
            return {"success": True, "message": "Saved"}
        return {"success": False, "message": "Save failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/admin/keys")
async def get_api_keys():
    with get_db() as conn:
        keys = conn.execute("SELECT * FROM api_keys ORDER BY created_at DESC").fetchall()
        return [dict(k) for k in keys]

@app.post("/api/admin/keys/generate")
async def generate_api_key_endpoint(request: Request):
    try:
        data = await request.json()
        name = data.get("name", "User")
        expires_days = data.get("expires_days", 30)
        key = create_api_key(name, expires_days)
        log_action("API key generated", key)
        return {"success": True, "key": key}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/keys/{key_id}")
async def delete_api_key(key_id: int):
    try:
        with get_db() as conn:
            conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
            conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/admin/logs")
async def get_logs():
    with get_db() as conn:
        logs = conn.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100").fetchall()
        return [dict(l) for l in logs]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))