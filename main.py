import os
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from pathlib import Path
import sqlite3
from contextlib import contextmanager
import hashlib
import time

app = FastAPI(title="HEX Protocol System", version="6.0")

# Security
security = HTTPBasic()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "hexadmin2024")

# Database setup
DB_PATH = Path("config.db")

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
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                timestamp TIMESTAMP,
                ip TEXT
            )
        """)
        conn.commit()

init_db()

# Default configuration
DEFAULT_CONFIG = {
    "maintenance": False,
    "root_maintenance": False,
    "nonroot_maintenance": False,
    "freefire_maintenance": False,
    "freefire_max_maintenance": True,
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
    "api_base_url": "https://key-system-production-1bc5.up.railway.app",
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

# Configuration file management
CONFIG_FILE = Path("config.json")

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def log_action(action: str, request: Request):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO audit_log (action, timestamp, ip) VALUES (?, ?, ?)",
            (action, datetime.now().isoformat(), request.client.host)
        )
        conn.commit()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def create_session():
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(hours=24)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (token, created_at, expires_at) VALUES (?, ?, ?)",
            (token, datetime.now().isoformat(), expires.isoformat())
        )
        conn.commit()
    return token

def verify_session(token: str):
    with get_db() as conn:
        session = conn.execute(
            "SELECT * FROM sessions WHERE token = ? AND expires_at > ?",
            (token, datetime.now().isoformat())
        ).fetchone()
        return session is not None

# HTML Templates
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HEX Protocol Admin Panel</title>
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #1a1a2e;
            --bg-card: #16213e;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0b0;
            --accent: #00ff88;
            --accent-hover: #00cc6a;
            --danger: #ff4444;
            --warning: #ffaa00;
            --border: #2a2a3e;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
        }
        
        .header h1 {
            font-size: 2.5em;
            color: var(--accent);
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 1.1em;
        }
        
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .nav-tab {
            padding: 12px 24px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .nav-tab:hover {
            background: var(--bg-card);
            border-color: var(--accent);
        }
        
        .nav-tab.active {
            background: var(--accent);
            color: var(--bg-primary);
            border-color: var(--accent);
        }
        
        .card {
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid var(--border);
            transition: all 0.3s;
        }
        
        .card:hover {
            border-color: #3a3a5e;
        }
        
        .card h2 {
            color: var(--accent);
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1);
        }
        
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn-primary {
            background: var(--accent);
            color: var(--bg-primary);
        }
        
        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 136, 0.3);
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        .btn-danger:hover {
            background: #cc0000;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 68, 68, 0.3);
        }
        
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        
        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        
        input:checked + .toggle-slider {
            background-color: var(--accent);
        }
        
        input:checked + .toggle-slider:before {
            transform: translateX(26px);
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .table th,
        .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        
        .table th {
            background: var(--bg-card);
            color: var(--accent);
            font-weight: 600;
        }
        
        .table tr:hover {
            background: var(--bg-card);
        }
        
        .status-badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-active {
            background: rgba(0, 255, 136, 0.1);
            color: var(--accent);
        }
        
        .status-inactive {
            background: rgba(255, 68, 68, 0.1);
            color: var(--danger);
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .grid-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
        }
        
        @media (max-width: 768px) {
            .grid-2,
            .grid-3 {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
        }
        
        .json-viewer {
            background: var(--bg-primary);
            padding: 20px;
            border-radius: 8px;
            overflow: auto;
            max-height: 600px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.5;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .modal-content {
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 15px;
            max-width: 500px;
            width: 90%;
            border: 1px solid var(--border);
        }
        
        .modal-content h3 {
            color: var(--accent);
            margin-bottom: 20px;
        }
        
        .log-entry {
            padding: 10px;
            border-left: 3px solid var(--accent);
            margin-bottom: 10px;
            background: var(--bg-primary);
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>HEX Protocol Admin Panel</h1>
            <p>Control Center for Configuration Management</p>
        </div>
        
        <div class="nav-tabs">
            <div class="nav-tab active" onclick="showTab('dashboard')">Dashboard</div>
            <div class="nav-tab" onclick="showTab('general')">General Settings</div>
            <div class="nav-tab" onclick="showTab('freefire')">Free Fire Settings</div>
            <div class="nav-tab" onclick="showTab('freefire_max')">Free Fire MAX</div>
            <div class="nav-tab" onclick="showTab('buttons')">Button Management</div>
            <div class="nav-tab" onclick="showTab('api')">API Configuration</div>
            <div class="nav-tab" onclick="showTab('logs')">Audit Logs</div>
        </div>
        
        <div id="dashboard" class="tab-content">
            <div class="card">
                <h2>System Overview</h2>
                <div class="grid-3">
                    <div class="card">
                        <h3>Maintenance Status</h3>
                        <p id="maintenance-status">Checking...</p>
                    </div>
                    <div class="card">
                        <h3>Master Key</h3>
                        <p id="master-key-display">Loading...</p>
                    </div>
                    <div class="card">
                        <h3>Total Buttons</h3>
                        <p id="total-buttons">0</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="general" class="tab-content" style="display:none;">
            <div class="card">
                <h2>General Configuration</h2>
                <form id="general-form">
                    <div class="grid-2">
                        <div class="form-group">
                            <label>App Name</label>
                            <input type="text" id="app_name" name="app_name">
                        </div>
                        <div class="form-group">
                            <label>Login Name</label>
                            <input type="text" id="login_name" name="login_name">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Maintenance Message</label>
                        <textarea id="maintenance_message" name="maintenance_message"></textarea>
                    </div>
                    
                    <div class="grid-2">
                        <div class="form-group">
                            <label>Telegram Link</label>
                            <input type="text" id="telegram_link" name="telegram_link">
                        </div>
                        <div class="form-group">
                            <label>Get Key Link</label>
                            <input type="text" id="get_key_link" name="get_key_link">
                        </div>
                    </div>
                    
                    <div class="grid-2">
                        <div class="form-group">
                            <label>Logo URL</label>
                            <input type="text" id="logo_url" name="logo_url">
                        </div>
                        <div class="form-group">
                            <label>Shizuku Logo URL</label>
                            <input type="text" id="shizuku_logo_url" name="shizuku_logo_url">
                        </div>
                    </div>
                    
                    <div class="grid-2">
                        <div class="form-group">
                            <label>Free Fire Logo URL</label>
                            <input type="text" id="freefire_logo_url" name="freefire_logo_url">
                        </div>
                        <div class="form-group">
                            <label>Free Fire MAX Logo URL</label>
                            <input type="text" id="freefire_max_logo_url" name="freefire_max_logo_url">
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Save General Settings</button>
                </form>
            </div>
        </div>
        
        <div id="freefire" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Free Fire Settings</h2>
                <form id="freefire-form">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="freefire_maintenance" name="freefire_maintenance">
                            Free Fire Maintenance Mode
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="nonroot_maintenance" name="nonroot_maintenance">
                            Non-Root Maintenance Mode
                        </label>
                    </div>
                    <button type="submit" class="btn btn-primary">Save Free Fire Settings</button>
                </form>
            </div>
        </div>
        
        <div id="freefire_max" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Free Fire MAX Settings</h2>
                <form id="freefire-max-form">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="freefire_max_maintenance" name="freefire_max_maintenance">
                            Free Fire MAX Maintenance Mode
                        </label>
                    </div>
                    <button type="submit" class="btn btn-primary">Save Free Fire MAX Settings</button>
                </form>
            </div>
        </div>
        
        <div id="buttons" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Button Management</h2>
                <div id="buttons-list"></div>
                <button class="btn btn-primary" onclick="addButton()">Add Button</button>
            </div>
        </div>
        
        <div id="api" class="tab-content" style="display:none;">
            <div class="card">
                <h2>API Configuration</h2>
                <div class="form-group">
                    <label>API Base URL</label>
                    <input type="text" id="api_base_url" value="">
                </div>
                <div class="form-group">
                    <label>Master Key</label>
                    <input type="text" id="master_key" value="">
                </div>
                <div class="form-group">
                    <label>Master Key Expiry</label>
                    <input type="datetime-local" id="master_key_expiry" value="">
                </div>
                <button class="btn btn-primary" onclick="saveApiConfig()">Save API Configuration</button>
            </div>
        </div>
        
        <div id="logs" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Audit Logs</h2>
                <div id="logs-list"></div>
            </div>
        </div>
    </div>
    
    <div class="modal" id="button-modal">
        <div class="modal-content">
            <h3>Button Configuration</h3>
            <div class="form-group">
                <label>Button ID</label>
                <input type="text" id="btn-id">
            </div>
            <div class="form-group">
                <label>Button Name</label>
                <input type="text" id="btn-name">
            </div>
            <div class="form-group">
                <label>URL</label>
                <input type="text" id="btn-url">
            </div>
            <div class="form-group">
                <label>Key URL</label>
                <input type="text" id="btn-key-url">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="btn-enabled">
                    Enabled
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="btn-maintenance">
                    Maintenance Mode
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="btn-persist">
                    Persist
                </label>
            </div>
            <button class="btn btn-primary" onclick="saveButton()">Save Button</button>
            <button class="btn btn-danger" onclick="closeModal()">Cancel</button>
        </div>
    </div>
    
    <script>
        let currentConfig = null;
        let editingButtonId = null;
        
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).style.display = 'block';
            event.target.classList.add('active');
            
            if (tabName === 'dashboard') {
                loadDashboard();
            } else if (tabName === 'buttons') {
                loadButtons();
            } else if (tabName === 'logs') {
                loadLogs();
            }
        }
        
        function loadConfig() {
            fetch('/api/config')
                .then(response => response.json())
                .then(data => {
                    currentConfig = data;
                    populateForms(data);
                    updateDashboard(data);
                })
                .catch(error => console.error('Error loading config:', error));
        }
        
        function populateForms(config) {
            document.getElementById('app_name').value = config.app_name || '';
            document.getElementById('login_name').value = config.login_name || '';
            document.getElementById('maintenance_message').value = config.maintenance_message || '';
            document.getElementById('telegram_link').value = config.telegram_link || '';
            document.getElementById('get_key_link').value = config.get_key_link || '';
            document.getElementById('logo_url').value = config.logo_url || '';
            document.getElementById('shizuku_logo_url').value = config.shizuku_logo_url || '';
            document.getElementById('freefire_logo_url').value = config.freefire_logo_url || '';
            document.getElementById('freefire_max_logo_url').value = config.freefire_max_logo_url || '';
            
            document.getElementById('freefire_maintenance').checked = config.freefire_maintenance || false;
            document.getElementById('nonroot_maintenance').checked = config.nonroot_maintenance || false;
            document.getElementById('freefire_max_maintenance').checked = config.freefire_max_maintenance || false;
            
            document.getElementById('api_base_url').value = config.api_base_url || '';
            document.getElementById('master_key').value = config.master_key || '';
            document.getElementById('master_key_expiry').value = config.master_key_expiry ? config.master_key_expiry.slice(0, 16) : '';
        }
        
        function updateDashboard(config) {
            document.getElementById('maintenance-status').textContent = 
                config.maintenance ? 'Maintenance Active' : 'System Online';
            document.getElementById('maintenance-status').className = 
                config.maintenance ? 'status-badge status-inactive' : 'status-badge status-active';
            
            document.getElementById('master-key-display').textContent = config.master_key || 'Not Set';
            
            const totalButtons = (config.freefire_buttons?.length || 0) + (config.freefire_max_buttons?.length || 0);
            document.getElementById('total-buttons').textContent = totalButtons;
        }
        
        function loadDashboard() {
            loadConfig();
        }
        
        function loadButtons() {
            const buttonsList = document.getElementById('buttons-list');
            buttonsList.innerHTML = '<h3>Free Fire Buttons</h3>';
            
            if (currentConfig.freefire_buttons) {
                currentConfig.freefire_buttons.forEach((btn, index) => {
                    buttonsList.innerHTML += `
                        <div class="card">
                            <h4>${btn.name}</h4>
                            <p>ID: ${btn.id}</p>
                            <p>Enabled: ${btn.enabled ? 'Yes' : 'No'}</p>
                            <p>Maintenance: ${btn.maintenance ? 'Yes' : 'No'}</p>
                            <button class="btn btn-primary" onclick="editButton('freefire', ${index})">Edit</button>
                            <button class="btn btn-danger" onclick="deleteButton('freefire', ${index})">Delete</button>
                        </div>
                    `;
                });
            }
            
            buttonsList.innerHTML += '<h3>Free Fire MAX Buttons</h3>';
            
            if (currentConfig.freefire_max_buttons) {
                currentConfig.freefire_max_buttons.forEach((btn, index) => {
                    buttonsList.innerHTML += `
                        <div class="card">
                            <h4>${btn.name}</h4>
                            <p>ID: ${btn.id}</p>
                            <p>Enabled: ${btn.enabled ? 'Yes' : 'No'}</p>
                            <p>Maintenance: ${btn.maintenance ? 'Yes' : 'No'}</p>
                            <button class="btn btn-primary" onclick="editButton('freefire_max', ${index})">Edit</button>
                            <button class="btn btn-danger" onclick="deleteButton('freefire_max', ${index})">Delete</button>
                        </div>
                    `;
                });
            }
        }
        
        function addButton() {
            editingButtonId = null;
            document.getElementById('btn-id').value = '';
            document.getElementById('btn-name').value = '';
            document.getElementById('btn-url').value = '';
            document.getElementById('btn-key-url').value = '';
            document.getElementById('btn-enabled').checked = true;
            document.getElementById('btn-maintenance').checked = false;
            document.getElementById('btn-persist').checked = false;
            document.getElementById('button-modal').style.display = 'flex';
        }
        
        function editButton(type, index) {
            const buttons = type === 'freefire' ? currentConfig.freefire_buttons : currentConfig.freefire_max_buttons;
            const btn = buttons[index];
            editingButtonId = index;
            document.getElementById('btn-id').value = btn.id;
            document.getElementById('btn-name').value = btn.name;
            document.getElementById('btn-url').value = btn.url;
            document.getElementById('btn-key-url').value = btn.urlKeyTxt || '';
            document.getElementById('btn-enabled').checked = btn.enabled;
            document.getElementById('btn-maintenance').checked = btn.maintenance;
            document.getElementById('btn-persist').checked = btn.persist;
            document.getElementById('button-modal').style.display = 'flex';
        }
        
        function deleteButton(type, index) {
            if (confirm('Are you sure you want to delete this button?')) {
                if (type === 'freefire') {
                    currentConfig.freefire_buttons.splice(index, 1);
                } else {
                    currentConfig.freefire_max_buttons.splice(index, 1);
                }
                saveConfig();
                loadButtons();
            }
        }
        
        function saveButton() {
            const buttonData = {
                id: document.getElementById('btn-id').value,
                name: document.getElementById('btn-name').value,
                url: document.getElementById('btn-url').value,
                urlKeyTxt: document.getElementById('btn-key-url').value,
                enabled: document.getElementById('btn-enabled').checked,
                maintenance: document.getElementById('btn-maintenance').checked,
                persist: document.getElementById('btn-persist').checked
            };
            
            if (editingButtonId !== null) {
                // Edit existing button
                if (currentConfig.freefire_buttons && editingButtonId < currentConfig.freefire_buttons.length) {
                    currentConfig.freefire_buttons[editingButtonId] = buttonData;
                } else if (currentConfig.freefire_max_buttons) {
                    const maxIndex = editingButtonId - (currentConfig.freefire_buttons?.length || 0);
                    currentConfig.freefire_max_buttons[maxIndex] = buttonData;
                }
            } else {
                // Add new button to freefire_buttons by default
                if (!currentConfig.freefire_buttons) {
                    currentConfig.freefire_buttons = [];
                }
                currentConfig.freefire_buttons.push(buttonData);
            }
            
            saveConfig();
            closeModal();
            loadButtons();
        }
        
        function closeModal() {
            document.getElementById('button-modal').style.display = 'none';
        }
        
        function saveConfig() {
            fetch('/api/admin/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(currentConfig)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Configuration saved successfully');
                    loadConfig();
                }
            })
            .catch(error => {
                console.error('Error saving config:', error);
                alert('Error saving configuration');
            });
        }
        
        function saveApiConfig() {
            currentConfig.api_base_url = document.getElementById('api_base_url').value;
            currentConfig.master_key = document.getElementById('master_key').value;
            currentConfig.master_key_expiry = document.getElementById('master_key_expiry').value;
            saveConfig();
        }
        
        function loadLogs() {
            fetch('/api/admin/logs')
                .then(response => response.json())
                .then(logs => {
                    const logsList = document.getElementById('logs-list');
                    logsList.innerHTML = '';
                    logs.forEach(log => {
                        logsList.innerHTML += `
                            <div class="log-entry">
                                <strong>${log.action}</strong>
                                <p>Time: ${log.timestamp}</p>
                                <p>IP: ${log.ip}</p>
                            </div>
                        `;
                    });
                });
        }
        
        document.getElementById('general-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            currentConfig.app_name = document.getElementById('app_name').value;
            currentConfig.login_name = document.getElementById('login_name').value;
            currentConfig.maintenance_message = document.getElementById('maintenance_message').value;
            currentConfig.telegram_link = document.getElementById('telegram_link').value;
            currentConfig.get_key_link = document.getElementById('get_key_link').value;
            currentConfig.logo_url = document.getElementById('logo_url').value;
            currentConfig.shizuku_logo_url = document.getElementById('shizuku_logo_url').value;
            currentConfig.freefire_logo_url = document.getElementById('freefire_logo_url').value;
            currentConfig.freefire_max_logo_url = document.getElementById('freefire_max_logo_url').value;
            
            saveConfig();
        });
        
        document.getElementById('freefire-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            currentConfig.freefire_maintenance = document.getElementById('freefire_maintenance').checked;
            currentConfig.nonroot_maintenance = document.getElementById('nonroot_maintenance').checked;
            
            saveConfig();
        });
        
        document.getElementById('freefire-max-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            currentConfig.freefire_max_maintenance = document.getElementById('freefire_max_maintenance').checked;
            
            saveConfig();
        });
        
        // Initial load
        loadConfig();
    </script>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HEX Protocol - Admin Login</title>
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #1a1a2e;
            --text-primary: #e0e0e0;
            --accent: #00ff88;
            --border: #2a2a3e;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        
        .login-container {
            background: var(--bg-secondary);
            padding: 40px;
            border-radius: 15px;
            border: 1px solid var(--border);
            width: 100%;
            max-width: 400px;
        }
        
        h1 {
            color: var(--accent);
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-primary);
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
        }
        
        .form-group input:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: var(--accent);
            color: var(--bg-primary);
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button:hover {
            background: #00cc6a;
        }
        
        .error {
            color: #ff4444;
            text-align: center;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>HEX Protocol</h1>
        <form id="login-form">
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit">Login</button>
            <div class="error" id="error-message"></div>
        </form>
    </div>
    
    <script>
        document.getElementById('login-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    localStorage.setItem('admin_token', data.token);
                    window.location.href = '/admin';
                } else {
                    document.getElementById('error-message').textContent = 'Invalid credentials';
                }
            } catch (error) {
                document.getElementById('error-message').textContent = 'Login failed';
            }
        });
    </script>
</body>
</html>
"""

# API Endpoints
@app.get("/api/config")
async def get_config():
    config = load_config()
    config["master_key"] = "HIDDEN"  # Hide master key from public API
    return config

@app.get("/api/config/full")
async def get_full_config():
    return load_config()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    return {"message": "HEX Protocol System API", "version": "6.0"}

# Admin endpoints
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page():
    return LOGIN_HTML

@app.post("/api/admin/login")
async def admin_login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = create_session()
        log_action("Admin login successful", request)
        return {"success": True, "token": token}
    
    log_action("Admin login failed", request)
    return {"success": False}

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    return ADMIN_HTML

@app.get("/api/admin/config")
async def admin_get_config():
    return load_config()

@app.post("/api/admin/config")
async def admin_update_config(request: Request):
    config_data = await request.json()
    save_config(config_data)
    log_action("Configuration updated", request)
    return {"success": True, "message": "Configuration saved"}

@app.get("/api/admin/logs")
async def get_logs():
    with get_db() as conn:
        logs = conn.execute(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100"
        ).fetchall()
        return [dict(log) for log in logs]

# Export configuration endpoint
@app.get("/export")
async def export_config():
    config = load_config()
    return JSONResponse(
        content=config,
        headers={"Content-Disposition": "attachment; filename=config.json"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
