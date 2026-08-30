import os
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
import uvicorn
from pathlib import Path
import sqlite3
from contextlib import contextmanager
import hashlib
import time
from fastapi.middleware.cors import CORSMiddleware
import copy

app = FastAPI(title="HEX Protocol System", version="6.0", docs_url="/api/docs", redoc_url="/api/redoc")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
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
                ip TEXT,
                details TEXT
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

# Default configuration
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
        },
        {
            "id": "ff_antenna",
            "name": "DRAG HS + ANTENNA SPEED 2x",
            "url": "https://raw.githubusercontent.com/madangowdru17-star/DARG-HS-1000/refs/heads/main/localconfig.json",
            "urlKeyTxt": "",
            "enabled": False,
            "maintenance": True,
            "persist": False
        },
        {
            "id": "ff_headshot",
            "name": "HEADSHOT 99%",
            "url": "https://raw.githubusercontent.com/madangowdru17-star/Assistant/refs/heads/main/localconfig.json",
            "urlKeyTxt": "",
            "enabled": False,
            "maintenance": False,
            "persist": False
        },
        {
            "id": "ff_aimbot",
            "name": "AIMBOT PRO",
            "url": "https://raw.githubusercontent.com/madangowdru17-star/Assistant/refs/heads/main/localconfig.json",
            "urlKeyTxt": "",
            "enabled": False,
            "maintenance": False,
            "persist": False
        },
        {
            "id": "ff_wallhack",
            "name": "WALLHACK XRAY",
            "url": "https://raw.githubusercontent.com/madangowdru17-star/Assistant/refs/heads/main/localconfig.json",
            "urlKeyTxt": "",
            "enabled": False,
            "maintenance": False,
            "persist": False
        },
        {
            "id": "ff_esp",
            "name": "ESP PLAYER",
            "url": "https://raw.githubusercontent.com/madangowdru17-star/Assistant/refs/heads/main/localconfig.json",
            "urlKeyTxt": "",
            "enabled": False,
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
        },
        {
            "id": "max_nick",
            "name": "NICK HS 95%",
            "url": "",
            "urlKeyTxt": "",
            "enabled": True,
            "maintenance": False,
            "persist": False
        },
        {
            "id": "max_body",
            "name": "BODY HS 99%",
            "url": "",
            "urlKeyTxt": "",
            "enabled": True,
            "maintenance": False,
            "persist": False
        },
        {
            "id": "max_aimbot",
            "name": "AIMBOT MAX",
            "url": "",
            "urlKeyTxt": "",
            "enabled": True,
            "maintenance": False,
            "persist": False
        },
        {
            "id": "max_wallhack",
            "name": "WALLHACK MAX",
            "url": "",
            "urlKeyTxt": "",
            "enabled": True,
            "maintenance": False,
            "persist": False
        },
        {
            "id": "max_esp",
            "name": "ESP MAX",
            "url": "",
            "urlKeyTxt": "",
            "enabled": True,
            "maintenance": False,
            "persist": False
        }
    ],
    
    "root_libs": [
        {
            "id": "root_max64",
            "name": "FF Max 64-bit",
            "url": "https://github.com/YOUR_USERNAME/YOUR_REPO/raw/main/libcrashlytics_arm64.so",
            "lib_path": "lib/arm64-v8a/libcrashlytics.so",
            "arch": "arm64",
            "enabled": True,
            "maintenance": False
        },
        {
            "id": "root_max32",
            "name": "FF Max 32-bit",
            "url": "https://github.com/YOUR_USERNAME/YOUR_REPO/raw/main/libcrashlytics_arm.so",
            "lib_path": "lib/armeabi-v7a/libcrashlytics.so",
            "arch": "arm",
            "enabled": True,
            "maintenance": False
        },
        {
            "id": "root_aimbot",
            "name": "Aimbot Module",
            "url": "https://github.com/YOUR_USERNAME/YOUR_REPO/raw/main/libaimbot.so",
            "lib_path": "lib/arm64-v8a/libaimbot.so",
            "arch": "arm64",
            "enabled": True,
            "maintenance": False
        },
        {
            "id": "root_esp",
            "name": "ESP Module",
            "url": "https://github.com/YOUR_USERNAME/YOUR_REPO/raw/main/libesp.so",
            "lib_path": "lib/arm64-v8a/libesp.so",
            "arch": "arm64",
            "enabled": True,
            "maintenance": False
        }
    ]
}

CONFIG_FILE = Path("config.json")

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        save_config(DEFAULT_CONFIG)
        return copy.deepcopy(DEFAULT_CONFIG)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def log_action(action: str, request: Request = None, details: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO audit_log (action, timestamp, ip, details) VALUES (?, ?, ?, ?)",
            (action, datetime.now().isoformat(), request.client.host if request else "system", details)
        )
        conn.commit()

def create_backup(note: str = ""):
    config = load_config()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO backups (config_data, created_at, note) VALUES (?, ?, ?)",
            (json.dumps(config), datetime.now().isoformat(), note)
        )
        conn.commit()

def verify_admin(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
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

# Premium Admin Panel HTML
PREMIUM_ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HEX Protocol Control Center</title>
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #1a1a2e;
            --bg-card: #16213e;
            --bg-hover: #1e2a4a;
            --text-primary: #ffffff;
            --text-secondary: #b0b0c0;
            --text-muted: #707080;
            --accent: #00ff88;
            --accent-hover: #00cc6a;
            --accent-glow: rgba(0, 255, 136, 0.3);
            --danger: #ff4444;
            --danger-hover: #cc0000;
            --warning: #ffaa00;
            --info: #0088ff;
            --border: #2a2a3e;
            --border-light: #3a3a5e;
            --shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            --radius: 12px;
            --radius-sm: 8px;
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
            min-height: 100vh;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #0f3460 0%, #16213e 50%, #1a1a2e 100%);
            padding: 30px;
            border-radius: var(--radius);
            margin-bottom: 30px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, var(--accent) 0%, #00ffcc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
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
            position: sticky;
            top: 0;
            z-index: 100;
            background: var(--bg-primary);
            padding: 10px 0;
        }
        
        .nav-tab {
            padding: 12px 24px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.3s;
            color: var(--text-primary);
            font-weight: 500;
            position: relative;
            overflow: hidden;
        }
        
        .nav-tab:hover {
            background: var(--bg-hover);
            border-color: var(--accent);
            transform: translateY(-2px);
        }
        
        .nav-tab.active {
            background: var(--accent);
            color: var(--bg-primary);
            border-color: var(--accent);
            box-shadow: 0 5px 20px var(--accent-glow);
        }
        
        .card {
            background: var(--bg-secondary);
            border-radius: var(--radius);
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid var(--border);
            transition: all 0.3s;
            box-shadow: var(--shadow);
        }
        
        .card:hover {
            border-color: var(--border-light);
            transform: translateY(-2px);
        }
        
        .card h2 {
            color: var(--accent);
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .card h3 {
            color: var(--text-primary);
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: var(--radius-sm);
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
            box-shadow: 0 5px 15px var(--accent-glow);
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        .btn-danger:hover {
            background: var(--danger-hover);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 68, 68, 0.3);
        }
        
        .btn-warning {
            background: var(--warning);
            color: var(--bg-primary);
        }
        
        .btn-info {
            background: var(--info);
            color: white;
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
            background: var(--bg-hover);
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
        
        .grid-4 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 20px;
        }
        
        @media (max-width: 768px) {
            .grid-2,
            .grid-3,
            .grid-4 {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
        }
        
        .json-viewer {
            background: var(--bg-primary);
            padding: 20px;
            border-radius: var(--radius-sm);
            overflow: auto;
            max-height: 600px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.5;
            border: 1px solid var(--border);
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
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: var(--radius);
            max-width: 600px;
            width: 90%;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            max-height: 90vh;
            overflow-y: auto;
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
            border-radius: var(--radius-sm);
        }
        
        .quick-action {
            display: inline-block;
            padding: 8px 16px;
            margin: 5px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .quick-action:hover {
            background: var(--bg-hover);
            border-color: var(--accent);
        }
        
        .stats-card {
            background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
            padding: 20px;
            border-radius: var(--radius);
            text-align: center;
            border: 1px solid var(--border);
        }
        
        .stats-card .number {
            font-size: 2em;
            font-weight: 700;
            color: var(--accent);
        }
        
        .stats-card .label {
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        .backup-item {
            padding: 15px;
            background: var(--bg-primary);
            border-radius: var(--radius-sm);
            margin-bottom: 10px;
            border: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>HEX Protocol Control Center</h1>
            <p>Premium Configuration Management System</p>
        </div>
        
        <div class="nav-tabs">
            <div class="nav-tab active" onclick="showTab('dashboard')">Dashboard</div>
            <div class="nav-tab" onclick="showTab('general')">General</div>
            <div class="nav-tab" onclick="showTab('maintenance')">Maintenance</div>
            <div class="nav-tab" onclick="showTab('freefire')">Free Fire</div>
            <div class="nav-tab" onclick="showTab('freefire_max')">FF MAX</div>
            <div class="nav-tab" onclick="showTab('buttons')">Buttons</div>
            <div class="nav-tab" onclick="showTab('root_libs')">Root Libs</div>
            <div class="nav-tab" onclick="showTab('assets')">Assets</div>
            <div class="nav-tab" onclick="showTab('api')">API Config</div>
            <div class="nav-tab" onclick="showTab('backups')">Backups</div>
            <div class="nav-tab" onclick="showTab('logs')">Logs</div>
            <div class="nav-tab" onclick="showTab('json')">JSON View</div>
        </div>
        
        <div id="dashboard" class="tab-content">
            <div class="grid-4">
                <div class="stats-card">
                    <div class="number" id="stat-buttons">0</div>
                    <div class="label">Total Buttons</div>
                </div>
                <div class="stats-card">
                    <div class="number" id="stat-rootlibs">0</div>
                    <div class="label">Root Libraries</div>
                </div>
                <div class="stats-card">
                    <div class="number" id="stat-assets">0</div>
                    <div class="label">Assets</div>
                </div>
                <div class="stats-card">
                    <div class="number" id="stat-backups">0</div>
                    <div class="label">Backups</div>
                </div>
            </div>
            
            <div class="card">
                <h2>Quick Actions</h2>
                <div>
                    <button class="quick-action" onclick="toggleMaintenance()">Toggle Maintenance</button>
                    <button class="quick-action" onclick="createBackup()">Create Backup</button>
                    <button class="quick-action" onclick="exportConfig()">Export Config</button>
                    <button class="quick-action" onclick="location.reload()">Refresh</button>
                </div>
            </div>
            
            <div class="card">
                <h2>System Status</h2>
                <div id="system-status"></div>
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
            
            <div class="card">
                <h2>Update Configuration</h2>
                <form id="update-form">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="update_available">
                            Update Available
                        </label>
                    </div>
                    <div class="grid-2">
                        <div class="form-group">
                            <label>Update Version</label>
                            <input type="text" id="update_version">
                        </div>
                        <div class="form-group">
                            <label>Update URL</label>
                            <input type="text" id="update_url">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Update Changelog</label>
                        <textarea id="update_changelog"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Save Update Settings</button>
                </form>
            </div>
        </div>
        
        <div id="maintenance" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Maintenance Control</h2>
                <div class="grid-2">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="maintenance">
                            Global Maintenance
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="root_maintenance">
                            Root Maintenance
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="nonroot_maintenance">
                            Non-Root Maintenance
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="freefire_maintenance">
                            Free Fire Maintenance
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="freefire_max_maintenance">
                            Free Fire MAX Maintenance
                        </label>
                    </div>
                </div>
                <button class="btn btn-primary" onclick="saveMaintenance()">Save Maintenance Settings</button>
            </div>
        </div>
        
        <div id="freefire" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Free Fire Buttons Management</h2>
                <div id="freefire-buttons-list"></div>
                <button class="btn btn-primary" onclick="addButton('freefire')">Add Free Fire Button</button>
            </div>
        </div>
        
        <div id="freefire_max" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Free Fire MAX Buttons Management</h2>
                <div id="freefire-max-buttons-list"></div>
                <button class="btn btn-primary" onclick="addButton('freefire_max')">Add Free Fire MAX Button</button>
            </div>
        </div>
        
        <div id="buttons" class="tab-content" style="display:none;">
            <div class="card">
                <h2>All Buttons Overview</h2>
                <div id="all-buttons-list"></div>
            </div>
        </div>
        
        <div id="root_libs" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Root Libraries Management</h2>
                <div id="root-libs-list"></div>
                <button class="btn btn-primary" onclick="addRootLib()">Add Root Library</button>
            </div>
        </div>
        
        <div id="assets" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Assets Management</h2>
                <div class="form-group">
                    <label>Assets Version</label>
                    <input type="text" id="assets_version">
                </div>
                <div id="assets-list"></div>
                <button class="btn btn-primary" onclick="addAsset()">Add Asset</button>
                <button class="btn btn-primary" onclick="saveAssetsVersion()">Save Assets Version</button>
            </div>
        </div>
        
        <div id="api" class="tab-content" style="display:none;">
            <div class="card">
                <h2>API Configuration</h2>
                <div class="form-group">
                    <label>API Base URL</label>
                    <input type="text" id="api_base_url">
                </div>
                <div class="form-group">
                    <label>Master Key</label>
                    <input type="text" id="master_key">
                </div>
                <div class="form-group">
                    <label>Master Key Expiry</label>
                    <input type="datetime-local" id="master_key_expiry">
                </div>
                <button class="btn btn-primary" onclick="saveApiConfig()">Save API Configuration</button>
            </div>
        </div>
        
        <div id="backups" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Configuration Backups</h2>
                <button class="btn btn-primary" onclick="createBackup()">Create New Backup</button>
                <div id="backups-list"></div>
            </div>
        </div>
        
        <div id="logs" class="tab-content" style="display:none;">
            <div class="card">
                <h2>Audit Logs</h2>
                <div id="logs-list"></div>
            </div>
        </div>
        
        <div id="json" class="tab-content" style="display:none;">
            <div class="card">
                <h2>JSON Configuration Viewer</h2>
                <button class="btn btn-primary" onclick="refreshJsonView()">Refresh</button>
                <button class="btn btn-primary" onclick="copyJson()">Copy JSON</button>
                <button class="btn btn-primary" onclick="downloadJson()">Download JSON</button>
                <div class="json-viewer" id="json-viewer"></div>
            </div>
        </div>
    </div>
    
    <div class="modal" id="button-modal">
        <div class="modal-content">
            <h3 id="modal-title">Button Configuration</h3>
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
            <div class="grid-3">
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="btn-enabled">
                        Enabled
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="btn-maintenance">
                        Maintenance
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="btn-persist">
                        Persist
                    </label>
                </div>
            </div>
            <button class="btn btn-primary" onclick="saveButton()">Save</button>
            <button class="btn btn-danger" onclick="closeModal()">Cancel</button>
        </div>
    </div>
    
    <div class="modal" id="rootlib-modal">
        <div class="modal-content">
            <h3>Root Library Configuration</h3>
            <div class="form-group">
                <label>Library ID</label>
                <input type="text" id="lib-id">
            </div>
            <div class="form-group">
                <label>Library Name</label>
                <input type="text" id="lib-name">
            </div>
            <div class="form-group">
                <label>URL</label>
                <input type="text" id="lib-url">
            </div>
            <div class="form-group">
                <label>Library Path</label>
                <input type="text" id="lib-path">
            </div>
            <div class="form-group">
                <label>Architecture</label>
                <select id="lib-arch">
                    <option value="arm64">ARM64</option>
                    <option value="arm">ARM</option>
                    <option value="x86">x86</option>
                    <option value="x86_64">x86_64</option>
                </select>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="lib-enabled">
                        Enabled
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="lib-maintenance">
                        Maintenance
                    </label>
                </div>
            </div>
            <button class="btn btn-primary" onclick="saveRootLib()">Save</button>
            <button class="btn btn-danger" onclick="closeRootLibModal()">Cancel</button>
        </div>
    </div>
    
    <div class="modal" id="asset-modal">
        <div class="modal-content">
            <h3>Asset Configuration</h3>
            <div class="form-group">
                <label>Asset Name</label>
                <input type="text" id="asset-name">
            </div>
            <div class="form-group">
                <label>Asset URL</label>
                <input type="text" id="asset-url">
            </div>
            <button class="btn btn-primary" onclick="saveAsset()">Save</button>
            <button class="btn btn-danger" onclick="closeAssetModal()">Cancel</button>
        </div>
    </div>
    
    <script>
        let currentConfig = null;
        let editingButtonType = null;
        let editingButtonIndex = null;
        let editingRootLibIndex = null;
        let editingAssetIndex = null;
        
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).style.display = 'block';
            event.target.classList.add('active');
            
            switch(tabName) {
                case 'dashboard':
                    loadDashboard();
                    break;
                case 'freefire':
                    loadFreeFireButtons();
                    break;
                case 'freefire_max':
                    loadFreeFireMaxButtons();
                    break;
                case 'buttons':
                    loadAllButtons();
                    break;
                case 'root_libs':
                    loadRootLibs();
                    break;
                case 'assets':
                    loadAssets();
                    break;
                case 'backups':
                    loadBackups();
                    break;
                case 'logs':
                    loadLogs();
                    break;
                case 'json':
                    refreshJsonView();
                    break;
            }
        }
        
        function loadConfig() {
            fetch('/api/admin/config')
                .then(response => response.json())
                .then(data => {
                    currentConfig = data;
                    populateForms(data);
                    updateDashboard(data);
                })
                .catch(error => console.error('Error loading config:', error));
        }
        
        function populateForms(config) {
            // General settings
            document.getElementById('app_name').value = config.app_name || '';
            document.getElementById('login_name').value = config.login_name || '';
            document.getElementById('maintenance_message').value = config.maintenance_message || '';
            document.getElementById('telegram_link').value = config.telegram_link || '';
            document.getElementById('get_key_link').value = config.get_key_link || '';
            document.getElementById('logo_url').value = config.logo_url || '';
            document.getElementById('shizuku_logo_url').value = config.shizuku_logo_url || '';
            document.getElementById('freefire_logo_url').value = config.freefire_logo_url || '';
            document.getElementById('freefire_max_logo_url').value = config.freefire_max_logo_url || '';
            
            // Update settings
            document.getElementById('update_available').checked = config.update_available || false;
            document.getElementById('update_version').value = config.update_version || '';
            document.getElementById('update_url').value = config.update_url || '';
            document.getElementById('update_changelog').value = config.update_changelog || '';
            
            // Maintenance
            document.getElementById('maintenance').checked = config.maintenance || false;
            document.getElementById('root_maintenance').checked = config.root_maintenance || false;
            document.getElementById('nonroot_maintenance').checked = config.nonroot_maintenance || false;
            document.getElementById('freefire_maintenance').checked = config.freefire_maintenance || false;
            document.getElementById('freefire_max_maintenance').checked = config.freefire_max_maintenance || false;
            
            // API config
            document.getElementById('api_base_url').value = config.api_base_url || '';
            document.getElementById('master_key').value = config.master_key || '';
            document.getElementById('master_key_expiry').value = config.master_key_expiry ? config.master_key_expiry.slice(0, 16) : '';
            
            // Assets
            document.getElementById('assets_version').value = config.assets_version || '';
        }
        
        function updateDashboard(config) {
            document.getElementById('stat-buttons').textContent = 
                (config.freefire_buttons?.length || 0) + (config.freefire_max_buttons?.length || 0);
            document.getElementById('stat-rootlibs').textContent = config.root_libs?.length || 0;
            document.getElementById('stat-assets').textContent = config.assets?.length || 0;
            
            const systemStatus = document.getElementById('system-status');
            systemStatus.innerHTML = `
                <div class="grid-3">
                    <div class="stats-card">
                        <div class="number">${config.maintenance ? 'ON' : 'OFF'}</div>
                        <div class="label">Maintenance Mode</div>
                    </div>
                    <div class="stats-card">
                        <div class="number">${config.update_available ? 'YES' : 'NO'}</div>
                        <div class="label">Update Available</div>
                    </div>
                    <div class="stats-card">
                        <div class="number">${config.assets_version || 'N/A'}</div>
                        <div class="label">Assets Version</div>
                    </div>
                </div>
            `;
        }
        
        function loadDashboard() {
            loadConfig();
            fetch('/api/admin/backups/count')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('stat-backups').textContent = data.count || 0;
                });
        }
        
        function loadFreeFireButtons() {
            const list = document.getElementById('freefire-buttons-list');
            list.innerHTML = '';
            
            if (currentConfig.freefire_buttons) {
                currentConfig.freefire_buttons.forEach((btn, index) => {
                    list.innerHTML += createButtonCard(btn, 'freefire', index);
                });
            }
        }
        
        function loadFreeFireMaxButtons() {
            const list = document.getElementById('freefire-max-buttons-list');
            list.innerHTML = '';
            
            if (currentConfig.freefire_max_buttons) {
                currentConfig.freefire_max_buttons.forEach((btn, index) => {
                    list.innerHTML += createButtonCard(btn, 'freefire_max', index);
                });
            }
        }
        
        function loadAllButtons() {
            const list = document.getElementById('all-buttons-list');
            list.innerHTML = '<h3>Free Fire Buttons</h3>';
            
            if (currentConfig.freefire_buttons) {
                currentConfig.freefire_buttons.forEach((btn, index) => {
                    list.innerHTML += createButtonCard(btn, 'freefire', index);
                });
            }
            
            list.innerHTML += '<h3>Free Fire MAX Buttons</h3>';
            
            if (currentConfig.freefire_max_buttons) {
                currentConfig.freefire_max_buttons.forEach((btn, index) => {
                    list.innerHTML += createButtonCard(btn, 'freefire_max', index);
                });
            }
        }
        
        function createButtonCard(btn, type, index) {
            return `
                <div class="card">
                    <h3>${btn.name}</h3>
                    <p><strong>ID:</strong> ${btn.id}</p>
                    <p><strong>URL:</strong> ${btn.url || 'N/A'}</p>
                    <p><strong>Key URL:</strong> ${btn.urlKeyTxt || 'N/A'}</p>
                    <div class="grid-3">
                        <div>
                            <span class="status-badge ${btn.enabled ? 'status-active' : 'status-inactive'}">
                                ${btn.enabled ? 'ENABLED' : 'DISABLED'}
                            </span>
                        </div>
                        <div>
                            <span class="status-badge ${btn.maintenance ? 'status-inactive' : 'status-active'}">
                                ${btn.maintenance ? 'MAINTENANCE' : 'ACTIVE'}
                            </span>
                        </div>
                        <div>
                            <span class="status-badge ${btn.persist ? 'status-active' : 'status-inactive'}">
                                ${btn.persist ? 'PERSIST' : 'NORMAL'}
                            </span>
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <button class="btn btn-primary" onclick="editButton('${type}', ${index})">Edit</button>
                        <button class="btn btn-danger" onclick="deleteButton('${type}', ${index})">Delete</button>
                        <button class="btn btn-warning" onclick="toggleButtonEnabled('${type}', ${index})">
                            ${btn.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button class="btn btn-info" onclick="toggleButtonMaintenance('${type}', ${index})">
                            ${btn.maintenance ? 'Remove Maintenance' : 'Set Maintenance'}
                        </button>
                    </div>
                </div>
            `;
        }
        
        function addButton(type) {
            editingButtonType = type;
            editingButtonIndex = null;
            document.getElementById('modal-title').textContent = 
                type === 'freefire' ? 'Add Free Fire Button' : 'Add Free Fire MAX Button';
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
            editingButtonType = type;
            editingButtonIndex = index;
            const buttons = type === 'freefire' ? currentConfig.freefire_buttons : currentConfig.freefire_max_buttons;
            const btn = buttons[index];
            document.getElementById('modal-title').textContent = 'Edit Button';
            document.getElementById('btn-id').value = btn.id;
            document.getElementById('btn-name').value = btn.name;
            document.getElementById('btn-url').value = btn.url;
            document.getElementById('btn-key-url').value = btn.urlKeyTxt || '';
            document.getElementById('btn-enabled').checked = btn.enabled;
            document.getElementById('btn-maintenance').checked = btn.maintenance;
            document.getElementById('btn-persist').checked = btn.persist;
            document.getElementById('button-modal').style.display = 'flex';
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
            
            const buttons = editingButtonType === 'freefire' ? 
                (currentConfig.freefire_buttons ||= []) : 
                (currentConfig.freefire_max_buttons ||= []);
            
            if (editingButtonIndex !== null && editingButtonIndex !== undefined) {
                buttons[editingButtonIndex] = buttonData;
            } else {
                buttons.push(buttonData);
            }
            
            saveConfig();
            closeModal();
            showTab(editingButtonType);
        }
        
        function deleteButton(type, index) {
            if (confirm('Are you sure you want to delete this button?')) {
                const buttons = type === 'freefire' ? currentConfig.freefire_buttons : currentConfig.freefire_max_buttons;
                buttons.splice(index, 1);
                saveConfig();
                showTab(type);
            }
        }
        
        function toggleButtonEnabled(type, index) {
            const buttons = type === 'freefire' ? currentConfig.freefire_buttons : currentConfig.freefire_max_buttons;
            buttons[index].enabled = !buttons[index].enabled;
            saveConfig();
            showTab(type);
        }
        
        function toggleButtonMaintenance(type, index) {
            const buttons = type === 'freefire' ? currentConfig.freefire_buttons : currentConfig.freefire_max_buttons;
            buttons[index].maintenance = !buttons[index].maintenance;
            saveConfig();
            showTab(type);
        }
        
        function loadRootLibs() {
            const list = document.getElementById('root-libs-list');
            list.innerHTML = '';
            
            if (currentConfig.root_libs) {
                currentConfig.root_libs.forEach((lib, index) => {
                    list.innerHTML += `
                        <div class="card">
                            <h3>${lib.name}</h3>
                            <p><strong>ID:</strong> ${lib.id}</p>
                            <p><strong>URL:</strong> ${lib.url}</p>
                            <p><strong>Path:</strong> ${lib.lib_path}</p>
                            <p><strong>Arch:</strong> ${lib.arch}</p>
                            <div class="grid-2">
                                <span class="status-badge ${lib.enabled ? 'status-active' : 'status-inactive'}">
                                    ${lib.enabled ? 'ENABLED' : 'DISABLED'}
                                </span>
                                <span class="status-badge ${lib.maintenance ? 'status-inactive' : 'status-active'}">
                                    ${lib.maintenance ? 'MAINTENANCE' : 'ACTIVE'}
                                </span>
                            </div>
                            <div style="margin-top: 15px;">
                                <button class="btn btn-primary" onclick="editRootLib(${index})">Edit</button>
                                <button class="btn btn-danger" onclick="deleteRootLib(${index})">Delete</button>
                            </div>
                        </div>
                    `;
                });
            }
        }
        
        function addRootLib() {
            editingRootLibIndex = null;
            document.getElementById('lib-id').value = '';
            document.getElementById('lib-name').value = '';
            document.getElementById('lib-url').value = '';
            document.getElementById('lib-path').value = '';
            document.getElementById('lib-arch').value = 'arm64';
            document.getElementById('lib-enabled').checked = true;
            document.getElementById('lib-maintenance').checked = false;
            document.getElementById('rootlib-modal').style.display = 'flex';
        }
        
        function editRootLib(index) {
            editingRootLibIndex = index;
            const lib = currentConfig.root_libs[index];
            document.getElementById('lib-id').value = lib.id;
            document.getElementById('lib-name').value = lib.name;
            document.getElementById('lib-url').value = lib.url;
            document.getElementById('lib-path').value = lib.lib_path;
            document.getElementById('lib-arch').value = lib.arch;
            document.getElementById('lib-enabled').checked = lib.enabled;
            document.getElementById('lib-maintenance').checked = lib.maintenance;
            document.getElementById('rootlib-modal').style.display = 'flex';
        }
        
        function saveRootLib() {
            const libData = {
                id: document.getElementById('lib-id').value,
                name: document.getElementById('lib-name').value,
                url: document.getElementById('lib-url').value,
                lib_path: document.getElementById('lib-path').value,
                arch: document.getElementById('lib-arch').value,
                enabled: document.getElementById('lib-enabled').checked,
                maintenance: document.getElementById('lib-maintenance').checked
            };
            
            if (!currentConfig.root_libs) {
                currentConfig.root_libs = [];
            }
            
            if (editingRootLibIndex !== null) {
                currentConfig.root_libs[editingRootLibIndex] = libData;
            } else {
                currentConfig.root_libs.push(libData);
            }
            
            saveConfig();
            closeRootLibModal();
            loadRootLibs();
        }
        
        function deleteRootLib(index) {
            if (confirm('Are you sure you want to delete this root library?')) {
                currentConfig.root_libs.splice(index, 1);
                saveConfig();
                loadRootLibs();
            }
        }
        
        function loadAssets() {
            const list = document.getElementById('assets-list');
            list.innerHTML = '';
            
            if (currentConfig.assets) {
                currentConfig.assets.forEach((asset, index) => {
                    list.innerHTML += `
                        <div class="card">
                            <h3>${asset.name}</h3>
                            <p><strong>URL:</strong> ${asset.url}</p>
                            <div style="margin-top: 15px;">
                                <button class="btn btn-primary" onclick="editAsset(${index})">Edit</button>
                                <button class="btn btn-danger" onclick="deleteAsset(${index})">Delete</button>
                            </div>
                        </div>
                    `;
                });
            }
        }
        
        function addAsset() {
            editingAssetIndex = null;
            document.getElementById('asset-name').value = '';
            document.getElementById('asset-url').value = '';
            document.getElementById('asset-modal').style.display = 'flex';
        }
        
        function editAsset(index) {
            editingAssetIndex = index;
            const asset = currentConfig.assets[index];
            document.getElementById('asset-name').value = asset.name;
            document.getElementById('asset-url').value = asset.url;
            document.getElementById('asset-modal').style.display = 'flex';
        }
        
        function saveAsset() {
            const assetData = {
                name: document.getElementById('asset-name').value,
                url: document.getElementById('asset-url').value
            };
            
            if (!currentConfig.assets) {
                currentConfig.assets = [];
            }
            
            if (editingAssetIndex !== null) {
                currentConfig.assets[editingAssetIndex] = assetData;
            } else {
                currentConfig.assets.push(assetData);
            }
            
            saveConfig();
            closeAssetModal();
            loadAssets();
        }
        
        function deleteAsset(index) {
            if (confirm('Are you sure you want to delete this asset?')) {
                currentConfig.assets.splice(index, 1);
                saveConfig();
                loadAssets();
            }
        }
        
        function saveAssetsVersion() {
            currentConfig.assets_version = document.getElementById('assets_version').value;
            saveConfig();
        }
        
        function toggleMaintenance() {
            currentConfig.maintenance = !currentConfig.maintenance;
            saveConfig();
            loadDashboard();
        }
        
        function saveMaintenance() {
            currentConfig.maintenance = document.getElementById('maintenance').checked;
            currentConfig.root_maintenance = document.getElementById('root_maintenance').checked;
            currentConfig.nonroot_maintenance = document.getElementById('nonroot_maintenance').checked;
            currentConfig.freefire_maintenance = document.getElementById('freefire_maintenance').checked;
            currentConfig.freefire_max_maintenance = document.getElementById('freefire_max_maintenance').checked;
            saveConfig();
        }
        
        function saveApiConfig() {
            currentConfig.api_base_url = document.getElementById('api_base_url').value;
            currentConfig.master_key = document.getElementById('master_key').value;
            currentConfig.master_key_expiry = document.getElementById('master_key_expiry').value;
            saveConfig();
        }
        
        function createBackup() {
            fetch('/api/admin/backup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ note: 'Manual backup' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Backup created successfully');
                    loadBackups();
                }
            });
        }
        
        function loadBackups() {
            fetch('/api/admin/backups')
                .then(response => response.json())
                .then(backups => {
                    const list = document.getElementById('backups-list');
                    list.innerHTML = '';
                    backups.forEach(backup => {
                        list.innerHTML += `
                            <div class="backup-item">
                                <div>
                                    <strong>Backup #${backup.id}</strong>
                                    <p>Created: ${backup.created_at}</p>
                                    <p>Note: ${backup.note || 'N/A'}</p>
                                </div>
                                <div>
                                    <button class="btn btn-primary" onclick="restoreBackup(${backup.id})">Restore</button>
                                    <button class="btn btn-danger" onclick="deleteBackup(${backup.id})">Delete</button>
                                </div>
                            </div>
                        `;
                    });
                });
        }
        
        function restoreBackup(id) {
            if (confirm('Are you sure you want to restore this backup?')) {
                fetch(`/api/admin/backup/${id}/restore`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Backup restored successfully');
                        loadConfig();
                    }
                });
            }
        }
        
        function deleteBackup(id) {
            if (confirm('Are you sure you want to delete this backup?')) {
                fetch(`/api/admin/backup/${id}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadBackups();
                    }
                });
            }
        }
        
        function loadLogs() {
            fetch('/api/admin/logs')
                .then(response => response.json())
                .then(logs => {
                    const list = document.getElementById('logs-list');
                    list.innerHTML = '';
                    logs.forEach(log => {
                        list.innerHTML += `
                            <div class="log-entry">
                                <strong>${log.action}</strong>
                                <p>Time: ${log.timestamp}</p>
                                <p>IP: ${log.ip}</p>
                                ${log.details ? `<p>Details: ${log.details}</p>` : ''}
                            </div>
                        `;
                    });
                });
        }
        
        function refreshJsonView() {
            const viewer = document.getElementById('json-viewer');
            viewer.textContent = JSON.stringify(currentConfig, null, 2);
        }
        
        function copyJson() {
            const jsonText = JSON.stringify(currentConfig, null, 2);
            navigator.clipboard.writeText(jsonText).then(() => {
                alert('JSON copied to clipboard');
            });
        }
        
        function downloadJson() {
            const jsonText = JSON.stringify(currentConfig, null, 2);
            const blob = new Blob([jsonText], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'config.json';
            a.click();
            URL.revokeObjectURL(url);
        }
        
        function exportConfig() {
            window.open('/export', '_blank');
        }
        
        function closeModal() {
            document.getElementById('button-modal').style.display = 'none';
        }
        
        function closeRootLibModal() {
            document.getElementById('rootlib-modal').style.display = 'none';
        }
        
        function closeAssetModal() {
            document.getElementById('asset-modal').style.display = 'none';
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
                    console.log('Configuration saved');
                }
            })
            .catch(error => {
                console.error('Error saving config:', error);
            });
        }
        
        // Form submissions
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
            alert('General settings saved successfully');
        });
        
        document.getElementById('update-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            currentConfig.update_available = document.getElementById('update_available').checked;
            currentConfig.update_version = document.getElementById('update_version').value;
            currentConfig.update_url = document.getElementById('update_url').value;
            currentConfig.update_changelog = document.getElementById('update_changelog').value;
            
            saveConfig();
            alert('Update settings saved successfully');
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
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0a0a0f 100%);
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
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
        
        h1 {
            background: linear-gradient(135deg, var(--accent) 0%, #00ffcc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
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
            box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1);
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
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 136, 0.3);
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
    config["master_key"] = "HIDDEN"
    return config

@app.get("/api/config/full")
async def get_full_config():
    return load_config()

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "6.0"
    }

@app.get("/")
async def root():
    return {
        "message": "HEX Protocol System API",
        "version": "6.0",
        "admin_panel": "/admin",
        "docs": "/api/docs"
    }

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
    return PREMIUM_ADMIN_HTML

@app.get("/api/admin/config")
async def admin_get_config():
    return load_config()

@app.post("/api/admin/config")
async def admin_update_config(request: Request):
    config_data = await request.json()
    save_config(config_data)
    log_action("Configuration updated", request, "Full configuration update")
    return {"success": True, "message": "Configuration saved"}

@app.post("/api/admin/backup")
async def create_backup_endpoint(request: Request):
    data = await request.json()
    note = data.get("note", "")
    create_backup(note)
    log_action("Backup created", request, note)
    return {"success": True, "message": "Backup created"}

@app.get("/api/admin/backups")
async def get_backups():
    with get_db() as conn:
        backups = conn.execute(
            "SELECT id, created_at, note FROM backups ORDER BY created_at DESC"
        ).fetchall()
        return [dict(backup) for backup in backups]

@app.get("/api/admin/backups/count")
async def get_backup_count():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) as count FROM backups").fetchone()
        return {"count": count["count"]}

@app.post("/api/admin/backup/{backup_id}/restore")
async def restore_backup(backup_id: int, request: Request):
    with get_db() as conn:
        backup = conn.execute(
            "SELECT config_data FROM backups WHERE id = ?",
            (backup_id,)
        ).fetchone()
        
        if backup:
            config_data = json.loads(backup["config_data"])
            save_config(config_data)
            log_action("Backup restored", request, f"Restored backup #{backup_id}")
            return {"success": True, "message": "Backup restored"}
    
    return {"success": False, "message": "Backup not found"}

@app.delete("/api/admin/backup/{backup_id}")
async def delete_backup(backup_id: int, request: Request):
    with get_db() as conn:
        conn.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
        conn.commit()
    log_action("Backup deleted", request, f"Deleted backup #{backup_id}")
    return {"success": True, "message": "Backup deleted"}

@app.get("/api/admin/logs")
async def get_logs():
    with get_db() as conn:
        logs = conn.execute(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 200"
        ).fetchall()
        return [dict(log) for log in logs]

@app.get("/export")
async def export_config():
    config = load_config()
    return JSONResponse(
        content=config,
        headers={"Content-Disposition": "attachment; filename=config.json"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))