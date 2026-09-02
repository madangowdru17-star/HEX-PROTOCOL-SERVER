import os
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import sqlite3
from contextlib import contextmanager
import copy

app = FastAPI(title="HEX Protocol System", version="6.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "hexadmin2024"

# Database
DB_PATH = Path("data/config.db")
CONFIG_FILE = Path("data/config.json")
API_KEYS_FILE = Path("data/api_keys.json")

# Create data directory
Path("data").mkdir(exist_ok=True)

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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                timestamp TIMESTAMP,
                ip TEXT,
                details TEXT
            )
        """)
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_data TEXT,
                created_at TIMESTAMP,
                note TEXT
            )
        """)
        conn.commit()

init_db()

# Default config
DEFAULT_CONFIG = {
    "maintenance": False,
    "root_maintenance": False,
    "nonroot_maintenance": False,
    "freefire_maintenance": False,
    "freefire_max_maintenance": False,
    
    "master_key": "HEXPROXY999",
    "master_key_expiry": "2026-12-31T23:59:59.000000",
    
    "login_name": "HEX PROXY XOS V6",
    "app_name": "HEX PROXY XOS V6",
    
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

def load_config():
    """Load config from file"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            save_config(DEFAULT_CONFIG)
            return copy.deepcopy(DEFAULT_CONFIG)
    except:
        return copy.deepcopy(DEFAULT_CONFIG)

def save_config(config):
    """Save config to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False

def log_action(action, request=None, details=""):
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO audit_log (action, timestamp, ip, details) VALUES (?, ?, ?, ?)",
                (action, datetime.now().isoformat(), request.client.host if request else "system", details)
            )
            conn.commit()
    except:
        pass

def generate_api_key():
    """Generate a unique API key"""
    return "HEX-" + secrets.token_hex(16).upper()

def create_api_key(name, expires_days=30):
    """Create a new API key"""
    key = generate_api_key()
    created_at = datetime.now()
    expires_at = created_at + timedelta(days=expires_days)
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO api_keys (key, name, created_at, expires_at, is_active, usage_count) VALUES (?, ?, ?, ?, 1, 0)",
            (key, name, created_at.isoformat(), expires_at.isoformat())
        )
        conn.commit()
    
    return key

def validate_api_key(key):
    """Validate API key"""
    with get_db() as conn:
        api_key = conn.execute(
            "SELECT * FROM api_keys WHERE key = ? AND is_active = 1 AND expires_at > ?",
            (key, datetime.now().isoformat())
        ).fetchone()
        
        if api_key:
            conn.execute(
                "UPDATE api_keys SET usage_count = usage_count + 1 WHERE key = ?",
                (key,)
            )
            conn.commit()
            return True
    
    return False

# White theme HTML
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>HEX Protocol Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }
        
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center; color: white; }
        .header h1 { margin-bottom: 5px; }
        
        .nav { display: flex; flex-wrap: wrap; gap: 5px; padding: 15px; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 100; }
        .nav button { padding: 10px 20px; background: #f0f0f0; color: #333; border: none; cursor: pointer; border-radius: 5px; font-weight: 500; transition: all 0.3s; }
        .nav button:hover { background: #e0e0e0; }
        .nav button.active { background: #667eea; color: white; }
        
        .content { padding: 20px; max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 25px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h2 { color: #667eea; margin-bottom: 20px; font-size: 1.3em; }
        
        input[type="text"], input[type="password"], input[type="datetime-local"], textarea, select { 
            width: 100%; padding: 12px; margin: 8px 0 15px; background: #f9f9f9; border: 1px solid #ddd; 
            color: #333; border-radius: 5px; font-size: 14px;
        }
        input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; }
        
        button { padding: 10px 20px; background: #667eea; color: white; border: none; cursor: pointer; border-radius: 5px; margin: 5px; font-weight: 500; transition: all 0.3s; }
        button:hover { background: #5a67d8; }
        button.danger { background: #ff4444; }
        button.danger:hover { background: #cc0000; }
        button.success { background: #00c851; }
        button.success:hover { background: #00993d; }
        button.warning { background: #ffaa00; }
        button.warning:hover { background: #cc8800; }
        button.small { padding: 5px 10px; font-size: 12px; }
        
        .toggle-container { display: flex; align-items: center; gap: 10px; margin: 15px 0; }
        .toggle { position: relative; width: 50px; height: 25px; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 25px; }
        .slider:before { position: absolute; content: ""; height: 19px; width: 19px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #00c851; }
        input:checked + .slider:before { transform: translateX(25px); }
        
        .badge { display: inline-block; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: 600; }
        .badge-green { background: #d4edda; color: #155724; }
        .badge-red { background: #f8d7da; color: #721c24; }
        .badge-yellow { background: #fff3cd; color: #856404; }
        .badge-blue { background: #d1ecf1; color: #0c5460; }
        
        .grid { display: grid; gap: 20px; }
        .grid-2 { grid-template-columns: repeat(2, 1fr); }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }
        
        @media (max-width: 768px) {
            .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
        }
        
        .hidden { display: none; }
        
        .api-key-item { 
            padding: 15px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
        }
        
        .api-key { font-family: monospace; font-size: 14px; color: #667eea; word-break: break-all; }
        
        .stat-card {
            background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card .value { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-card .label { color: #666; margin-top: 5px; }
        
        .toast {
            position: fixed; top: 20px; right: 20px; padding: 15px 25px; border-radius: 5px;
            color: white; font-weight: 500; z-index: 1000; animation: slideIn 0.3s ease;
        }
        .toast-success { background: #00c851; }
        .toast-error { background: #ff4444; }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f5f5f5; font-weight: 600; }
        tr:hover { background: #f9f9f9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>HEX Protocol Admin Panel</h1>
        <p>Control Center v6.0</p>
    </div>
    
    <div class="nav">
        <button class="active" onclick="showTab('dashboard', this)">Dashboard</button>
        <button onclick="showTab('general', this)">General</button>
        <button onclick="showTab('maintenance', this)">Maintenance</button>
        <button onclick="showTab('buttons', this)">Buttons</button>
        <button onclick="showTab('api', this)">API Config</button>
        <button onclick="showTab('apikeys', this)">API Keys</button>
        <button onclick="showTab('logs', this)">Logs</button>
    </div>
    
    <div class="content">
        <div id="dashboard" class="tab">
            <div class="grid grid-4">
                <div class="stat-card">
                    <div class="value" id="stat-buttons">0</div>
                    <div class="label">Total Buttons</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="stat-keys">0</div>
                    <div class="label">API Keys</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="stat-active">0</div>
                    <div class="label">Active Keys</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="stat-maint">OFF</div>
                    <div class="label">Maintenance</div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <h2>Quick Actions</h2>
                <button onclick="toggleMaintenance()">Toggle Maintenance</button>
                <button class="success" onclick="createBackup()">Create Backup</button>
                <button class="warning" onclick="location.reload()">Refresh</button>
            </div>
        </div>
        
        <div id="general" class="tab hidden">
            <div class="card">
                <h2>General Settings</h2>
                <div class="grid grid-2">
                    <div>
                        <label>App Name</label>
                        <input type="text" id="app_name">
                    </div>
                    <div>
                        <label>Login Name</label>
                        <input type="text" id="login_name">
                    </div>
                </div>
                <label>Telegram Link</label>
                <input type="text" id="telegram_link">
                <label>Get Key Link</label>
                <input type="text" id="get_key_link">
                <label>Maintenance Message</label>
                <textarea id="maintenance_message" rows="3"></textarea>
                <label>Logo URL</label>
                <input type="text" id="logo_url">
                <label>Free Fire Logo URL</label>
                <input type="text" id="freefire_logo_url">
                <label>Free Fire MAX Logo URL</label>
                <input type="text" id="freefire_max_logo_url">
                <br>
                <button class="success" onclick="saveGeneral()">Save General Settings</button>
            </div>
        </div>
        
        <div id="maintenance" class="tab hidden">
            <div class="card">
                <h2>Maintenance Control</h2>
                <p style="color: #666; margin-bottom: 20px;">Toggle switches to enable/disable maintenance modes. Changes save automatically.</p>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="maintenance" onchange="saveMaintenance(this)">
                        <span class="slider"></span>
                    </label>
                    <strong>Global Maintenance</strong>
                </div>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="root_maintenance" onchange="saveMaintenance(this)">
                        <span class="slider"></span>
                    </label>
                    <strong>Root Maintenance</strong>
                </div>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="nonroot_maintenance" onchange="saveMaintenance(this)">
                        <span class="slider"></span>
                    </label>
                    <strong>Non-Root Maintenance</strong>
                </div>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="freefire_maintenance" onchange="saveMaintenance(this)">
                        <span class="slider"></span>
                    </label>
                    <strong>Free Fire Maintenance</strong>
                </div>
                
                <div class="toggle-container">
                    <label class="toggle">
                        <input type="checkbox" id="freefire_max_maintenance" onchange="saveMaintenance(this)">
                        <span class="slider"></span>
                    </label>
                    <strong>Free Fire MAX Maintenance</strong>
                </div>
            </div>
        </div>
        
        <div id="buttons" class="tab hidden">
            <div class="card">
                <h2>Free Fire Buttons</h2>
                <div id="ff-buttons"></div>
            </div>
            <div class="card">
                <h2>Free Fire MAX Buttons</h2>
                <div id="ffmax-buttons"></div>
            </div>
        </div>
        
        <div id="api" class="tab hidden">
            <div class="card">
                <h2>API Configuration</h2>
                <label>API Base URL</label>
                <input type="text" id="api_base_url">
                <label>Master Key</label>
                <input type="text" id="master_key">
                <label>Master Key Expiry</label>
                <input type="datetime-local" id="master_key_expiry">
                <br>
                <button class="success" onclick="saveApi()">Save API Config</button>
            </div>
        </div>
        
        <div id="apikeys" class="tab hidden">
            <div class="card">
                <h2>API Key Management</h2>
                <p style="color: #666; margin-bottom: 20px;">Generate and manage API keys for accessing your configuration.</p>
                
                <div class="grid grid-2" style="margin-bottom: 20px;">
                    <div>
                        <label>Key Name</label>
                        <input type="text" id="key-name" placeholder="e.g., User123">
                    </div>
                    <div>
                        <label>Expiry (Days)</label>
                        <select id="key-expiry">
                            <option value="7">7 Days</option>
                            <option value="30" selected>30 Days</option>
                            <option value="90">90 Days</option>
                            <option value="365">1 Year</option>
                            <option value="0">Never</option>
                        </select>
                    </div>
                </div>
                <button class="success" onclick="generateKey()">Generate API Key</button>
                
                <div id="api-keys-list" style="margin-top: 20px;"></div>
            </div>
        </div>
        
        <div id="logs" class="tab hidden">
            <div class="card">
                <h2>Audit Logs</h2>
                <div id="logs-list"></div>
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
                console.error('Load error:', e);
            }
        }
        
        async function saveConfigToServer() {
            try {
                const res = await fetch('/api/admin/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Saved successfully!', 'success');
                    return true;
                } else {
                    showToast('Save failed!', 'error');
                    return false;
                }
            } catch(e) {
                showToast('Error: ' + e.message, 'error');
                return false;
            }
        }
        
        function updateUI() {
            if (!config) return;
            
            // Dashboard
            document.getElementById('stat-buttons').textContent = 
                (config.freefire_buttons?.length || 0) + (config.freefire_max_buttons?.length || 0);
            document.getElementById('stat-maint').textContent = config.maintenance ? 'ON' : 'OFF';
            document.getElementById('stat-maint').style.color = config.maintenance ? '#ff4444' : '#00c851';
            
            // General
            document.getElementById('app_name').value = config.app_name || '';
            document.getElementById('login_name').value = config.login_name || '';
            document.getElementById('telegram_link').value = config.telegram_link || '';
            document.getElementById('get_key_link').value = config.get_key_link || '';
            document.getElementById('maintenance_message').value = config.maintenance_message || '';
            document.getElementById('logo_url').value = config.logo_url || '';
            document.getElementById('freefire_logo_url').value = config.freefire_logo_url || '';
            document.getElementById('freefire_max_logo_url').value = config.freefire_max_logo_url || '';
            
            // Maintenance
            document.getElementById('maintenance').checked = config.maintenance === true;
            document.getElementById('root_maintenance').checked = config.root_maintenance === true;
            document.getElementById('nonroot_maintenance').checked = config.nonroot_maintenance === true;
            document.getElementById('freefire_maintenance').checked = config.freefire_maintenance === true;
            document.getElementById('freefire_max_maintenance').checked = config.freefire_max_maintenance === true;
            
            // API
            document.getElementById('api_base_url').value = config.api_base_url || '';
            document.getElementById('master_key').value = config.master_key || '';
            document.getElementById('master_key_expiry').value = config.master_key_expiry ? config.master_key_expiry.slice(0, 16) : '';
            
            // Buttons
            loadButtons();
        }
        
        function loadButtons() {
            const ffDiv = document.getElementById('ff-buttons');
            const ffmaxDiv = document.getElementById('ffmax-buttons');
            ffDiv.innerHTML = '';
            ffmaxDiv.innerHTML = '';
            
            (config.freefire_buttons || []).forEach((btn, i) => {
                ffDiv.innerHTML += '<div class="card" style="margin-bottom: 10px;"><h3>' + btn.name + '</h3>' +
                    '<p>ID: ' + btn.id + '</p>' +
                    '<p>Enabled: <span class="badge ' + (btn.enabled ? 'badge-green' : 'badge-red') + '">' + (btn.enabled ? 'YES' : 'NO') + '</span> ' +
                    'Maintenance: <span class="badge ' + (btn.maintenance ? 'badge-yellow' : 'badge-green') + '">' + (btn.maintenance ? 'ON' : 'OFF') + '</span></p>' +
                    '<button class="small" onclick="toggleFFButton(' + i + ')">' + (btn.enabled ? 'Disable' : 'Enable') + '</button>' +
                    '<button class="small danger" onclick="deleteFFButton(' + i + ')">Delete</button></div>';
            });
            
            (config.freefire_max_buttons || []).forEach((btn, i) => {
                ffmaxDiv.innerHTML += '<div class="card" style="margin-bottom: 10px;"><h3>' + btn.name + '</h3>' +
                    '<p>ID: ' + btn.id + '</p>' +
                    '<p>Enabled: <span class="badge ' + (btn.enabled ? 'badge-green' : 'badge-red') + '">' + (btn.enabled ? 'YES' : 'NO') + '</span> ' +
                    'Maintenance: <span class="badge ' + (btn.maintenance ? 'badge-yellow' : 'badge-green') + '">' + (btn.maintenance ? 'ON' : 'OFF') + '</span></p>' +
                    '<button class="small" onclick="toggleFFMaxButton(' + i + ')">' + (btn.enabled ? 'Disable' : 'Enable') + '</button>' +
                    '<button class="small danger" onclick="deleteFFMaxButton(' + i + ')">Delete</button></div>';
            });
        }
        
        function showTab(name, btn) {
            document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden'));
            document.getElementById(name).classList.remove('hidden');
            document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            if (name === 'apikeys') loadApiKeys();
            if (name === 'logs') loadLogs();
            if (name === 'dashboard') loadDashboardStats();
        }
        
        async function saveGeneral() {
            config.app_name = document.getElementById('app_name').value;
            config.login_name = document.getElementById('login_name').value;
            config.telegram_link = document.getElementById('telegram_link').value;
            config.get_key_link = document.getElementById('get_key_link').value;
            config.maintenance_message = document.getElementById('maintenance_message').value;
            config.logo_url = document.getElementById('logo_url').value;
            config.freefire_logo_url = document.getElementById('freefire_logo_url').value;
            config.freefire_max_logo_url = document.getElementById('freefire_max_logo_url').value;
            await saveConfigToServer();
        }
        
        async function saveMaintenance() {
            config.maintenance = document.getElementById('maintenance').checked;
            config.root_maintenance = document.getElementById('root_maintenance').checked;
            config.nonroot_maintenance = document.getElementById('nonroot_maintenance').checked;
            config.freefire_maintenance = document.getElementById('freefire_maintenance').checked;
            config.freefire_max_maintenance = document.getElementById('freefire_max_maintenance').checked;
            await saveConfigToServer();
            updateUI();
        }
        
        async function saveApi() {
            config.api_base_url = document.getElementById('api_base_url').value;
            config.master_key = document.getElementById('master_key').value;
            config.master_key_expiry = document.getElementById('master_key_expiry').value;
            await saveConfigToServer();
        }
        
        async function toggleMaintenance() {
            config.maintenance = !config.maintenance;
            await saveConfigToServer();
            updateUI();
        }
        
        async function toggleFFButton(i) {
            config.freefire_buttons[i].enabled = !config.freefire_buttons[i].enabled;
            await saveConfigToServer();
            loadButtons();
        }
        
        async function toggleFFMaxButton(i) {
            config.freefire_max_buttons[i].enabled = !config.freefire_max_buttons[i].enabled;
            await saveConfigToServer();
            loadButtons();
        }
        
        async function deleteFFButton(i) {
            if (confirm('Delete this button?')) {
                config.freefire_buttons.splice(i, 1);
                await saveConfigToServer();
                loadButtons();
            }
        }
        
        async function deleteFFMaxButton(i) {
            if (confirm('Delete this button?')) {
                config.freefire_max_buttons.splice(i, 1);
                await saveConfigToServer();
                loadButtons();
            }
        }
        
        async function generateKey() {
            const name = document.getElementById('key-name').value || 'User';
            const expiry = document.getElementById('key-expiry').value;
            
            try {
                const res = await fetch('/api/admin/keys/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: name, expires_days: parseInt(expiry)})
                });
                const data = await res.json();
                
                if (data.success) {
                    showToast('API Key generated!', 'success');
                    loadApiKeys();
                } else {
                    showToast('Failed to generate key!', 'error');
                }
            } catch(e) {
                showToast('Error: ' + e.message, 'error');
            }
        }
        
        async function loadApiKeys() {
            try {
                const res = await fetch('/api/admin/keys');
                const keys = await res.json();
                const listDiv = document.getElementById('api-keys-list');
                listDiv.innerHTML = '';
                
                document.getElementById('stat-keys').textContent = keys.length;
                document.getElementById('stat-active').textContent = keys.filter(k => k.is_active).length;
                
                keys.forEach(key => {
                    const statusBadge = key.is_active ? 
                        '<span class="badge badge-green">ACTIVE</span>' : 
                        '<span class="badge badge-red">INACTIVE</span>';
                    
                    listDiv.innerHTML += '<div class="api-key-item">' +
                        '<div style="flex: 1;">' +
                        '<div class="api-key">' + key.key + '</div>' +
                        '<div style="font-size: 12px; color: #666;">' + key.name + ' | Created: ' + key.created_at + ' | Usage: ' + key.usage_count + '</div>' +
                        '</div>' +
                        statusBadge +
                        '<button class="small danger" onclick="deleteApiKey(' + key.id + ')">Delete</button>' +
                        '</div>';
                });
            } catch(e) {
                console.error('Error loading keys:', e);
            }
        }
        
        async function deleteApiKey(id) {
            if (confirm('Delete this API key?')) {
                try {
                    const res = await fetch('/api/admin/keys/' + id, {method: 'DELETE'});
                    const data = await res.json();
                    if (data.success) {
                        showToast('API Key deleted!', 'success');
                        loadApiKeys();
                    }
                } catch(e) {
                    showToast('Error: ' + e.message, 'error');
                }
            }
        }
        
        async function loadLogs() {
            try {
                const res = await fetch('/api/admin/logs');
                const logs = await res.json();
                const listDiv = document.getElementById('logs-list');
                listDiv.innerHTML = '';
                
                logs.forEach(log => {
                    listDiv.innerHTML += '<div style="padding: 10px; border-bottom: 1px solid #ddd;">' +
                        '<strong>' + log.action + '</strong> ' +
                        '<span style="color: #666;">(' + log.timestamp + ')</span></div>';
                });
            } catch(e) {
                console.error('Error loading logs:', e);
            }
        }
        
        async function loadDashboardStats() {
            try {
                const res = await fetch('/api/admin/keys');
                const keys = await res.json();
                document.getElementById('stat-keys').textContent = keys.length;
                document.getElementById('stat-active').textContent = keys.filter(k => k.is_active).length;
            } catch(e) {
                console.error('Error loading stats:', e);
            }
        }
        
        async function createBackup() {
            try {
                const res = await fetch('/api/admin/backup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({note: 'Manual backup'})
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Backup created!', 'success');
                }
            } catch(e) {
                showToast('Error: ' + e.message, 'error');
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
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .login-box { background: white; padding: 40px; border-radius: 10px; width: 100%; max-width: 350px; box-shadow: 0 2px 20px rgba(0,0,0,0.1); }
        h1 { color: #667eea; text-align: center; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #f9f9f9; border: 1px solid #ddd; color: #333; border-radius: 5px; }
        input:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: 600; }
        button:hover { background: #5a67d8; }
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
    config["master_key"] = "HIDDEN"
    return config

@app.get("/api/config/full")
async def get_full_config():
    return load_config()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "HEX Protocol System API", "version": "6.0"}

# Admin endpoints
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
            log_action("Admin login successful", request)
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
            log_action("Config updated", request)
            return {"success": True, "message": "Saved"}
        return {"success": False, "message": "Save failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# API Key endpoints
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
        log_action("API key generated", request, f"Key: {key}, Name: {name}")
        return {"success": True, "key": key}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/keys/{key_id}")
async def delete_api_key(key_id: int, request: Request):
    try:
        with get_db() as conn:
            conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
            conn.commit()
        log_action("API key deleted", request, f"Key ID: {key_id}")
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Backup endpoints
@app.post("/api/admin/backup")
async def create_backup_endpoint(request: Request):
    try:
        data = await request.json()
        note = data.get("note", "")
        config = load_config()
        with get_db() as conn:
            conn.execute(
                "INSERT INTO backups (config_data, created_at, note) VALUES (?, ?, ?)",
                (json.dumps(config), datetime.now().isoformat(), note)
            )
            conn.commit()
        log_action("Backup created", request, note)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Logs
@app.get("/api/admin/logs")
async def get_logs():
    with get_db() as conn:
        logs = conn.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100").fetchall()
        return [dict(l) for l in logs]

# Export
@app.get("/export")
async def export_config():
    config = load_config()
    return JSONResponse(content=config)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
