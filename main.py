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

app = FastAPI(title="HEX Protocol System", version="6.0", docs_url="/api/docs", redoc_url=None)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security - Simple hardcoded credentials for reliability
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "hexadmin2024"

# Database setup
DB_PATH = Path("config.db")
CONFIG_FILE = Path("config.json")

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
        }
    ]
}

def load_config():
    """Load configuration from file with error handling"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            save_config(DEFAULT_CONFIG)
            return copy.deepcopy(DEFAULT_CONFIG)
    except Exception as e:
        print(f"Error loading config: {e}")
        return copy.deepcopy(DEFAULT_CONFIG)

def save_config(config):
    """Save configuration to file with error handling"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def log_action(action: str, request: Request = None, details: str = ""):
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO audit_log (action, timestamp, ip, details) VALUES (?, ?, ?, ?)",
                (action, datetime.now().isoformat(), request.client.host if request else "system", details)
            )
            conn.commit()
    except Exception as e:
        print(f"Error logging action: {e}")

def create_backup(note: str = ""):
    try:
        config = load_config()
        with get_db() as conn:
            conn.execute(
                "INSERT INTO backups (config_data, created_at, note) VALUES (?, ?, ?)",
                (json.dumps(config), datetime.now().isoformat(), note)
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

# Futuristic 3D Web UI
FUTURISTIC_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HEX Protocol - 3D Control Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #000010;
            --surface: rgba(20, 20, 40, 0.8);
            --surface-hover: rgba(30, 30, 60, 0.9);
            --border: rgba(100, 100, 255, 0.2);
            --border-hover: rgba(100, 100, 255, 0.5);
            --text: #e0e0ff;
            --text-secondary: #a0a0cc;
            --text-muted: #606080;
            --primary: #00ffff;
            --primary-hover: #00cccc;
            --primary-glow: rgba(0, 255, 255, 0.3);
            --secondary: #ff00ff;
            --secondary-glow: rgba(255, 0, 255, 0.3);
            --success: #00ff88;
            --success-glow: rgba(0, 255, 136, 0.3);
            --danger: #ff0044;
            --danger-glow: rgba(255, 0, 68, 0.3);
            --warning: #ffaa00;
            --warning-glow: rgba(255, 170, 0, 0.3);
            --info: #4488ff;
            --info-glow: rgba(68, 136, 255, 0.3);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Rajdhani', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
            cursor: default;
        }
        
        /* 3D Grid Background */
        #grid-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
        }
        
        /* Particle System */
        .particle {
            position: fixed;
            width: 2px;
            height: 2px;
            background: var(--primary);
            border-radius: 50%;
            pointer-events: none;
            z-index: 1;
            animation: float-particle 3s infinite;
            box-shadow: 0 0 10px var(--primary);
        }
        
        @keyframes float-particle {
            0%, 100% { transform: translateY(0) translateX(0); opacity: 0; }
            50% { transform: translateY(-50px) translateX(20px); opacity: 1; }
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 2;
        }
        
        /* Header with 3D effect */
        .header {
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(255, 0, 255, 0.1));
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            position: relative;
            overflow: hidden;
            transform-style: preserve-3d;
            animation: header-float 6s ease-in-out infinite;
        }
        
        @keyframes header-float {
            0%, 100% { transform: translateY(0) rotateX(0deg); }
            50% { transform: translateY(-5px) rotateX(2deg); }
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(0, 255, 255, 0.1), transparent);
            animation: header-shine 3s infinite;
        }
        
        @keyframes header-shine {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .header h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, #00ffff, #ff00ff, #00ffff);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradient-shift 3s ease-in-out infinite;
            margin-bottom: 10px;
            letter-spacing: 2px;
            text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
        }
        
        @keyframes gradient-shift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 1.1rem;
            letter-spacing: 1px;
        }
        
        /* 3D Navigation */
        .nav {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            position: sticky;
            top: 20px;
            z-index: 100;
            background: rgba(0, 0, 16, 0.9);
            backdrop-filter: blur(20px);
            padding: 15px;
            border-radius: 15px;
            border: 1px solid var(--border);
            transform-style: preserve-3d;
        }
        
        .nav-item {
            padding: 12px 20px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.9rem;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
            white-space: nowrap;
        }
        
        .nav-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            opacity: 0;
            transition: all 0.3s;
        }
        
        .nav-item:hover {
            border-color: var(--primary);
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 10px 30px var(--primary-glow);
            color: var(--text);
        }
        
        .nav-item.active {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: #000;
            border-color: transparent;
            box-shadow: 0 10px 40px var(--primary-glow);
            animation: nav-pulse 2s infinite;
        }
        
        @keyframes nav-pulse {
            0%, 100% { box-shadow: 0 0 20px var(--primary-glow); }
            50% { box-shadow: 0 0 40px var(--secondary-glow); }
        }
        
        /* Cards with 3D effect */
        .card {
            background: var(--surface);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            transition: all 0.3s;
            transform-style: preserve-3d;
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            opacity: 0;
            transition: all 0.3s;
        }
        
        .card:hover {
            border-color: var(--border-hover);
            transform: translateY(-5px) rotateX(2deg);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        .card:hover::before {
            opacity: 1;
        }
        
        .card h2 {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: var(--primary);
            letter-spacing: 1px;
            text-shadow: 0 0 20px var(--primary-glow);
        }
        
        .card h3 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--text);
        }
        
        /* Grid layouts */
        .grid {
            display: grid;
            gap: 20px;
        }
        
        .grid-2 { grid-template-columns: repeat(2, 1fr); }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }
        
        @media (max-width: 1024px) {
            .grid-4 { grid-template-columns: repeat(2, 1fr); }
        }
        
        @media (max-width: 768px) {
            .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
            .header h1 { font-size: 1.8rem; }
            .nav-item { padding: 8px 12px; font-size: 0.8rem; }
        }
        
        /* Form elements */
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.85rem;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px 16px;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-size: 0.95rem;
            transition: all 0.3s;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 20px var(--primary-glow);
            background: rgba(0, 0, 0, 0.7);
        }
        
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        /* Buttons */
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
            font-family: 'Orbitron', sans-serif;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transform: translateX(-100%);
            transition: all 0.5s;
        }
        
        .btn:hover::before {
            transform: translateX(100%);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: #000;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px var(--primary-glow);
        }
        
        .btn-success {
            background: linear-gradient(135deg, var(--success), #00cc66);
            color: #000;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, var(--danger), #cc0033);
            color: #fff;
        }
        
        .btn-warning {
            background: linear-gradient(135deg, var(--warning), #cc8800);
            color: #000;
        }
        
        .btn-info {
            background: linear-gradient(135deg, var(--info), #3366cc);
            color: #fff;
        }
        
        /* Toggle switches */
        .toggle {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 26px;
        }
        
        .toggle input {
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
            background: rgba(255, 255, 255, 0.1);
            transition: all 0.3s;
            border-radius: 26px;
            border: 1px solid var(--border);
        }
        
        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background: var(--text-secondary);
            transition: all 0.3s;
            border-radius: 50%;
        }
        
        .toggle input:checked + .toggle-slider {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-color: transparent;
        }
        
        .toggle input:checked + .toggle-slider:before {
            transform: translateX(24px);
            background: #000;
        }
        
        /* Badges */
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1px;
        }
        
        .badge-success {
            background: rgba(0, 255, 136, 0.2);
            color: var(--success);
            border: 1px solid var(--success);
        }
        
        .badge-danger {
            background: rgba(255, 0, 68, 0.2);
            color: var(--danger);
            border: 1px solid var(--danger);
        }
        
        .badge-warning {
            background: rgba(255, 170, 0, 0.2);
            color: var(--warning);
            border: 1px solid var(--warning);
        }
        
        .badge-info {
            background: rgba(68, 136, 255, 0.2);
            color: var(--info);
            border: 1px solid var(--info);
        }
        
        /* Stats */
        .stat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s;
            transform-style: preserve-3d;
        }
        
        .stat-card:hover {
            transform: translateY(-5px) rotateX(5deg);
            border-color: var(--primary);
            box-shadow: 0 15px 40px var(--primary-glow);
        }
        
        .stat-card .value {
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 900;
            color: var(--primary);
            text-shadow: 0 0 20px var(--primary-glow);
            margin-bottom: 8px;
        }
        
        .stat-card .label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            letter-spacing: 1px;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 16, 0.9);
            backdrop-filter: blur(10px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .modal-content {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            max-height: 90vh;
            overflow-y: auto;
            transform: scale(0.9);
            animation: modal-in 0.3s forwards;
        }
        
        @keyframes modal-in {
            to { transform: scale(1); }
        }
        
        .modal-content h3 {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            margin-bottom: 24px;
            color: var(--primary);
            text-shadow: 0 0 20px var(--primary-glow);
        }
        
        .button-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        
        .quick-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .json-viewer {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            overflow: auto;
            max-height: 600px;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            color: var(--text);
        }
        
        .log-entry {
            padding: 15px;
            border-left: 3px solid var(--primary);
            margin-bottom: 10px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
        }
        
        /* Toast */
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: linear-gradient(135deg, var(--success), #00cc66);
            color: #000;
            border-radius: 10px;
            font-weight: 700;
            z-index: 2000;
            animation: toast-in 0.3s ease;
        }
        
        @keyframes toast-in {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <canvas id="grid-canvas"></canvas>
    
    <div class="container">
        <div class="header">
            <h1>HEX PROTOCOL</h1>
            <p>3D Control Center v6.0</p>
        </div>
        
        <div class="nav">
            <div class="nav-item active" onclick="showTab('dashboard')">Dashboard</div>
            <div class="nav-item" onclick="showTab('general')">General</div>
            <div class="nav-item" onclick="showTab('maintenance')">Maintenance</div>
            <div class="nav-item" onclick="showTab('freefire')">Free Fire</div>
            <div class="nav-item" onclick="showTab('ffmax')">FF MAX</div>
            <div class="nav-item" onclick="showTab('rootlibs')">Root Libs</div>
            <div class="nav-item" onclick="showTab('assets')">Assets</div>
            <div class="nav-item" onclick="showTab('api')">API</div>
            <div class="nav-item" onclick="showTab('backups')">Backups</div>
            <div class="nav-item" onclick="showTab('logs')">Logs</div>
            <div class="nav-item" onclick="showTab('json')">JSON</div>
        </div>
        
        <div id="dashboard" class="tab-content">
            <div class="grid grid-4">
                <div class="stat-card">
                    <div class="value" id="stat-buttons">0</div>
                    <div class="label">TOTAL BUTTONS</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="stat-rootlibs">0</div>
                    <div class="label">ROOT LIBS</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="stat-assets">0</div>
                    <div class="label">ASSETS</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="stat-backups">0</div>
                    <div class="label">BACKUPS</div>
                </div>
            </div>
            
            <div class="card">
                <h2>QUICK ACTIONS</h2>
                <div class="quick-actions">
                    <button class="btn btn-primary" onclick="toggleMaintenance()">TOGGLE MAINTENANCE</button>
                    <button class="btn btn-success" onclick="createBackup()">CREATE BACKUP</button>
                    <button class="btn btn-info" onclick="exportConfig()">EXPORT CONFIG</button>
                    <button class="btn btn-warning" onclick="location.reload()">REFRESH</button>
                </div>
            </div>
            
            <div class="card">
                <h2>SYSTEM STATUS</h2>
                <div id="system-status"></div>
            </div>
        </div>
        
        <div id="general" class="tab-content" style="display:none;">
            <div class="card">
                <h2>GENERAL CONFIGURATION</h2>
                <div class="grid grid-2">
                    <div class="form-group">
                        <label>APP NAME</label>
                        <input type="text" id="app_name">
                    </div>
                    <div class="form-group">
                        <label>LOGIN NAME</label>
                        <input type="text" id="login_name">
                    </div>
                </div>
                <div class="form-group">
                    <label>MAINTENANCE MESSAGE</label>
                    <textarea id="maintenance_message"></textarea>
                </div>
                <div class="grid grid-2">
                    <div class="form-group">
                        <label>TELEGRAM LINK</label>
                        <input type="text" id="telegram_link">
                    </div>
                    <div class="form-group">
                        <label>GET KEY LINK</label>
                        <input type="text" id="get_key_link">
                    </div>
                </div>
                <div class="grid grid-2">
                    <div class="form-group">
                        <label>LOGO URL</label>
                        <input type="text" id="logo_url">
                    </div>
                    <div class="form-group">
                        <label>SHIZUKU LOGO URL</label>
                        <input type="text" id="shizuku_logo_url">
                    </div>
                </div>
                <div class="grid grid-2">
                    <div class="form-group">
                        <label>FREE FIRE LOGO URL</label>
                        <input type="text" id="freefire_logo_url">
                    </div>
                    <div class="form-group">
                        <label>FREE FIRE MAX LOGO URL</label>
                        <input type="text" id="freefire_max_logo_url">
                    </div>
                </div>
                <button class="btn btn-primary" onclick="saveGeneral()">SAVE SETTINGS</button>
            </div>
        </div>
        
        <div id="maintenance" class="tab-content" style="display:none;">
            <div class="card">
                <h2>MAINTENANCE CONTROL</h2>
                <div class="grid grid-2">
                    <div class="form-group">
                        <label class="toggle">
                            <input type="checkbox" id="maintenance" onchange="saveMaintenance()">
                            <span class="toggle-slider"></span>
                        </label>
                        <span style="margin-left: 12px;">GLOBAL MAINTENANCE</span>
                    </div>
                    <div class="form-group">
                        <label class="toggle">
                            <input type="checkbox" id="root_maintenance" onchange="saveMaintenance()">
                            <span class="toggle-slider"></span>
                        </label>
                        <span style="margin-left: 12px;">ROOT MAINTENANCE</span>
                    </div>
                    <div class="form-group">
                        <label class="toggle">
                            <input type="checkbox" id="nonroot_maintenance" onchange="saveMaintenance()">
                            <span class="toggle-slider"></span>
                        </label>
                        <span style="margin-left: 12px;">NON-ROOT MAINTENANCE</span>
                    </div>
                    <div class="form-group">
                        <label class="toggle">
                            <input type="checkbox" id="freefire_maintenance" onchange="saveMaintenance()">
                            <span class="toggle-slider"></span>
                        </label>
                        <span style="margin-left: 12px;">FREE FIRE MAINTENANCE</span>
                    </div>
                    <div class="form-group">
                        <label class="toggle">
                            <input type="checkbox" id="freefire_max_maintenance" onchange="saveMaintenance()">
                            <span class="toggle-slider"></span>
                        </label>
                        <span style="margin-left: 12px;">FREE FIRE MAX MAINTENANCE</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="freefire" class="tab-content" style="display:none;">
            <div class="card">
                <h2>FREE FIRE BUTTONS</h2>
                <div id="freefire-buttons"></div>
                <button class="btn btn-primary" onclick="addButton('freefire_buttons')">ADD BUTTON</button>
            </div>
        </div>
        
        <div id="ffmax" class="tab-content" style="display:none;">
            <div class="card">
                <h2>FREE FIRE MAX BUTTONS</h2>
                <div id="ffmax-buttons"></div>
                <button class="btn btn-primary" onclick="addButton('freefire_max_buttons')">ADD BUTTON</button>
            </div>
        </div>
        
        <div id="rootlibs" class="tab-content" style="display:none;">
            <div class="card">
                <h2>ROOT LIBRARIES</h2>
                <div id="rootlibs-list"></div>
                <button class="btn btn-primary" onclick="addRootLib()">ADD ROOT LIB</button>
            </div>
        </div>
        
        <div id="assets" class="tab-content" style="display:none;">
            <div class="card">
                <h2>ASSETS MANAGEMENT</h2>
                <div class="form-group">
                    <label>ASSETS VERSION</label>
                    <input type="text" id="assets_version" onchange="saveAssetsVersion()">
                </div>
                <div id="assets-list"></div>
                <button class="btn btn-primary" onclick="addAsset()">ADD ASSET</button>
            </div>
        </div>
        
        <div id="api" class="tab-content" style="display:none;">
            <div class="card">
                <h2>API CONFIGURATION</h2>
                <div class="form-group">
                    <label>API BASE URL</label>
                    <input type="text" id="api_base_url">
                </div>
                <div class="form-group">
                    <label>MASTER KEY</label>
                    <input type="text" id="master_key">
                </div>
                <div class="form-group">
                    <label>MASTER KEY EXPIRY</label>
                    <input type="datetime-local" id="master_key_expiry">
                </div>
                <button class="btn btn-primary" onclick="saveApiConfig()">SAVE API CONFIG</button>
            </div>
        </div>
        
        <div id="backups" class="tab-content" style="display:none;">
            <div class="card">
                <h2>CONFIGURATION BACKUPS</h2>
                <button class="btn btn-success" onclick="createBackup()">CREATE NEW BACKUP</button>
                <div id="backups-list" style="margin-top: 20px;"></div>
            </div>
        </div>
        
        <div id="logs" class="tab-content" style="display:none;">
            <div class="card">
                <h2>AUDIT LOGS</h2>
                <div id="logs-list"></div>
            </div>
        </div>
        
        <div id="json" class="tab-content" style="display:none;">
            <div class="card">
                <h2>JSON CONFIGURATION</h2>
                <div class="button-actions">
                    <button class="btn btn-primary" onclick="refreshJson()">REFRESH</button>
                    <button class="btn btn-success" onclick="copyJson()">COPY</button>
                    <button class="btn btn-info" onclick="downloadJson()">DOWNLOAD</button>
                </div>
                <div class="json-viewer" id="json-viewer" style="margin-top: 20px;"></div>
            </div>
        </div>
    </div>
    
    <div class="modal" id="button-modal">
        <div class="modal-content">
            <h3 id="modal-title">BUTTON CONFIGURATION</h3>
            <div class="form-group">
                <label>BUTTON ID</label>
                <input type="text" id="btn-id">
            </div>
            <div class="form-group">
                <label>BUTTON NAME</label>
                <input type="text" id="btn-name">
            </div>
            <div class="form-group">
                <label>URL</label>
                <input type="text" id="btn-url">
            </div>
            <div class="form-group">
                <label>KEY URL</label>
                <input type="text" id="btn-key-url">
            </div>
            <div class="grid grid-3">
                <div class="form-group">
                    <label class="toggle">
                        <input type="checkbox" id="btn-enabled" checked>
                        <span class="toggle-slider"></span>
                    </label>
                    <span style="margin-left: 12px;">ENABLED</span>
                </div>
                <div class="form-group">
                    <label class="toggle">
                        <input type="checkbox" id="btn-maintenance">
                        <span class="toggle-slider"></span>
                    </label>
                    <span style="margin-left: 12px;">MAINTENANCE</span>
                </div>
                <div class="form-group">
                    <label class="toggle">
                        <input type="checkbox" id="btn-persist">
                        <span class="toggle-slider"></span>
                    </label>
                    <span style="margin-left: 12px;">PERSIST</span>
                </div>
            </div>
            <div class="button-actions">
                <button class="btn btn-primary" onclick="saveButton()">SAVE</button>
                <button class="btn btn-danger" onclick="closeModal()">CANCEL</button>
            </div>
        </div>
    </div>
    
    <div class="modal" id="rootlib-modal">
        <div class="modal-content">
            <h3>ROOT LIBRARY CONFIGURATION</h3>
            <div class="form-group">
                <label>LIBRARY ID</label>
                <input type="text" id="lib-id">
            </div>
            <div class="form-group">
                <label>LIBRARY NAME</label>
                <input type="text" id="lib-name">
            </div>
            <div class="form-group">
                <label>URL</label>
                <input type="text" id="lib-url">
            </div>
            <div class="form-group">
                <label>LIBRARY PATH</label>
                <input type="text" id="lib-path">
            </div>
            <div class="form-group">
                <label>ARCHITECTURE</label>
                <select id="lib-arch">
                    <option value="arm64">ARM64</option>
                    <option value="arm">ARM</option>
                    <option value="x86">x86</option>
                    <option value="x86_64">x86_64</option>
                </select>
            </div>
            <div class="grid grid-2">
                <div class="form-group">
                    <label class="toggle">
                        <input type="checkbox" id="lib-enabled" checked>
                        <span class="toggle-slider"></span>
                    </label>
                    <span style="margin-left: 12px;">ENABLED</span>
                </div>
                <div class="form-group">
                    <label class="toggle">
                        <input type="checkbox" id="lib-maintenance">
                        <span class="toggle-slider"></span>
                    </label>
                    <span style="margin-left: 12px;">MAINTENANCE</span>
                </div>
            </div>
            <div class="button-actions">
                <button class="btn btn-primary" onclick="saveRootLib()">SAVE</button>
                <button class="btn btn-danger" onclick="closeRootLibModal()">CANCEL</button>
            </div>
        </div>
    </div>
    
    <div class="modal" id="asset-modal">
        <div class="modal-content">
            <h3>ASSET CONFIGURATION</h3>
            <div class="form-group">
                <label>ASSET NAME</label>
                <input type="text" id="asset-name">
            </div>
            <div class="form-group">
                <label>ASSET URL</label>
                <input type="text" id="asset-url">
            </div>
            <div class="button-actions">
                <button class="btn btn-primary" onclick="saveAsset()">SAVE</button>
                <button class="btn btn-danger" onclick="closeAssetModal()">CANCEL</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentConfig = null;
        let editingType = null;
        let editingIndex = null;
        
        // 3D Grid Background
        const canvas = document.getElementById('grid-canvas');
        const ctx = canvas.getContext('2d');
        
        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        function drawGrid() {
            ctx.fillStyle = '#000010';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            const gridSize = 50;
            const offset = (Date.now() * 0.05) % gridSize;
            
            ctx.strokeStyle = 'rgba(0, 255, 255, 0.1)';
            ctx.lineWidth = 1;
            
            // Vertical lines
            for (let x = -offset; x < canvas.width; x += gridSize) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }
            
            // Horizontal lines
            for (let y = -offset; y < canvas.height; y += gridSize) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }
            
            // Glowing points at intersections
            for (let x = -offset; x < canvas.width; x += gridSize) {
                for (let y = -offset; y < canvas.height; y += gridSize) {
                    ctx.fillStyle = 'rgba(0, 255, 255, 0.3)';
                    ctx.beginPath();
                    ctx.arc(x, y, 2, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
            
            requestAnimationFrame(drawGrid);
        }
        
        drawGrid();
        
        // Create particles
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 3 + 's';
            particle.style.animationDuration = (Math.random() * 3 + 2) + 's';
            document.body.appendChild(particle);
        }
        
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).style.display = 'block';
            event.target.classList.add('active');
            
            switch(tabName) {
                case 'dashboard': loadDashboard(); break;
                case 'general': populateGeneral(); break;
                case 'maintenance': populateMaintenance(); break;
                case 'freefire': loadButtons('freefire_buttons'); break;
                case 'ffmax': loadButtons('freefire_max_buttons'); break;
                case 'rootlibs': loadRootLibs(); break;
                case 'assets': loadAssets(); break;
                case 'api': populateApi(); break;
                case 'backups': loadBackups(); break;
                case 'logs': loadLogs(); break;
                case 'json': refreshJson(); break;
            }
        }
        
        async function loadConfig() {
            try {
                const response = await fetch('/api/admin/config');
                currentConfig = await response.json();
                return currentConfig;
            } catch (error) {
                console.error('Error loading config:', error);
                return null;
            }
        }
        
        async function saveConfig() {
            try {
                const response = await fetch('/api/admin/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(currentConfig)
                });
                const data = await response.json();
                if (data.success) {
                    showToast('CONFIGURATION SAVED');
                }
            } catch (error) {
                console.error('Error saving config:', error);
                showToast('ERROR SAVING CONFIGURATION', true);
            }
        }
        
        function showToast(message, isError = false) {
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.style.background = isError ? 'linear-gradient(135deg, #ff0044, #cc0033)' : 'linear-gradient(135deg, #00ff88, #00cc66)';
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 2000);
        }
        
        async function loadDashboard() {
            await loadConfig();
            if (!currentConfig) return;
            
            document.getElementById('stat-buttons').textContent = 
                (currentConfig.freefire_buttons?.length || 0) + (currentConfig.freefire_max_buttons?.length || 0);
            document.getElementById('stat-rootlibs').textContent = currentConfig.root_libs?.length || 0;
            document.getElementById('stat-assets').textContent = currentConfig.assets?.length || 0;
            
            try {
                const response = await fetch('/api/admin/backups/count');
                const data = await response.json();
                document.getElementById('stat-backups').textContent = data.count || 0;
            } catch (error) {}
            
            const systemStatus = document.getElementById('system-status');
            systemStatus.innerHTML = `
                <div class="grid grid-3">
                    <div class="stat-card">
                        <div class="value">${currentConfig.maintenance ? 'ON' : 'OFF'}</div>
                        <div class="label">MAINTENANCE</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${currentConfig.update_available ? 'YES' : 'NO'}</div>
                        <div class="label">UPDATE</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${currentConfig.assets_version || 'N/A'}</div>
                        <div class="label">VERSION</div>
                    </div>
                </div>
            `;
        }
        
        function populateGeneral() {
            if (!currentConfig) return;
            document.getElementById('app_name').value = currentConfig.app_name || '';
            document.getElementById('login_name').value = currentConfig.login_name || '';
            document.getElementById('maintenance_message').value = currentConfig.maintenance_message || '';
            document.getElementById('telegram_link').value = currentConfig.telegram_link || '';
            document.getElementById('get_key_link').value = currentConfig.get_key_link || '';
            document.getElementById('logo_url').value = currentConfig.logo_url || '';
            document.getElementById('shizuku_logo_url').value = currentConfig.shizuku_logo_url || '';
            document.getElementById('freefire_logo_url').value = currentConfig.freefire_logo_url || '';
            document.getElementById('freefire_max_logo_url').value = currentConfig.freefire_max_logo_url || '';
        }
        
        function populateMaintenance() {
            if (!currentConfig) return;
            document.getElementById('maintenance').checked = currentConfig.maintenance || false;
            document.getElementById('root_maintenance').checked = currentConfig.root_maintenance || false;
            document.getElementById('nonroot_maintenance').checked = currentConfig.nonroot_maintenance || false;
            document.getElementById('freefire_maintenance').checked = currentConfig.freefire_maintenance || false;
            document.getElementById('freefire_max_maintenance').checked = currentConfig.freefire_max_maintenance || false;
        }
        
        function populateApi() {
            if (!currentConfig) return;
            document.getElementById('api_base_url').value = currentConfig.api_base_url || '';
            document.getElementById('master_key').value = currentConfig.master_key || '';
            document.getElementById('master_key_expiry').value = currentConfig.master_key_expiry ? currentConfig.master_key_expiry.slice(0, 16) : '';
        }
        
        async function saveGeneral() {
            currentConfig.app_name = document.getElementById('app_name').value;
            currentConfig.login_name = document.getElementById('login_name').value;
            currentConfig.maintenance_message = document.getElementById('maintenance_message').value;
            currentConfig.telegram_link = document.getElementById('telegram_link').value;
            currentConfig.get_key_link = document.getElementById('get_key_link').value;
            currentConfig.logo_url = document.getElementById('logo_url').value;
            currentConfig.shizuku_logo_url = document.getElementById('shizuku_logo_url').value;
            currentConfig.freefire_logo_url = document.getElementById('freefire_logo_url').value;
            currentConfig.freefire_max_logo_url = document.getElementById('freefire_max_logo_url').value;
            await saveConfig();
        }
        
        async function saveMaintenance() {
            currentConfig.maintenance = document.getElementById('maintenance').checked;
            currentConfig.root_maintenance = document.getElementById('root_maintenance').checked;
            currentConfig.nonroot_maintenance = document.getElementById('nonroot_maintenance').checked;
            currentConfig.freefire_maintenance = document.getElementById('freefire_maintenance').checked;
            currentConfig.freefire_max_maintenance = document.getElementById('freefire_max_maintenance').checked;
            await saveConfig();
        }
        
        async function saveApiConfig() {
            currentConfig.api_base_url = document.getElementById('api_base_url').value;
            currentConfig.master_key = document.getElementById('master_key').value;
            currentConfig.master_key_expiry = document.getElementById('master_key_expiry').value;
            await saveConfig();
        }
        
        async function saveAssetsVersion() {
            currentConfig.assets_version = document.getElementById('assets_version').value;
            await saveConfig();
        }
        
        async function toggleMaintenance() {
            currentConfig.maintenance = !currentConfig.maintenance;
            await saveConfig();
            await loadDashboard();
        }
        
        async function loadButtons(type) {
            if (!currentConfig) await loadConfig();
            const container = document.getElementById(type === 'freefire_buttons' ? 'freefire-buttons' : 'ffmax-buttons');
            container.innerHTML = '';
            
            const buttons = currentConfig[type] || [];
            buttons.forEach((btn, index) => {
                container.innerHTML += `
                    <div class="card" style="margin-bottom: 12px;">
                        <h3>${btn.name}</h3>
                        <p><strong>ID:</strong> ${btn.id}</p>
                        <div class="grid grid-3">
                            <span class="badge ${btn.enabled ? 'badge-success' : 'badge-danger'}">${btn.enabled ? 'ENABLED' : 'DISABLED'}</span>
                            <span class="badge ${btn.maintenance ? 'badge-warning' : 'badge-success'}">${btn.maintenance ? 'MAINTENANCE' : 'ACTIVE'}</span>
                            <span class="badge ${btn.persist ? 'badge-info' : 'badge-danger'}">${btn.persist ? 'PERSIST' : 'NORMAL'}</span>
                        </div>
                        <div class="button-actions">
                            <button class="btn btn-primary" onclick="editButton('${type}', ${index})">EDIT</button>
                            <button class="btn btn-danger" onclick="deleteButton('${type}', ${index})">DELETE</button>
                            <button class="btn btn-warning" onclick="toggleButton('${type}', ${index}, 'enabled')">${btn.enabled ? 'DISABLE' : 'ENABLE'}</button>
                            <button class="btn btn-info" onclick="toggleButton('${type}', ${index}, 'maintenance')">${btn.maintenance ? 'REMOVE MAINT' : 'SET MAINT'}</button>
                        </div>
                    </div>
                `;
            });
        }
        
        function addButton(type) {
            editingType = type;
            editingIndex = null;
            document.getElementById('modal-title').textContent = type === 'freefire_buttons' ? 'ADD FREE FIRE BUTTON' : 'ADD FREE FIRE MAX BUTTON';
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
            editingType = type;
            editingIndex = index;
            const btn = currentConfig[type][index];
            document.getElementById('modal-title').textContent = 'EDIT BUTTON';
            document.getElementById('btn-id').value = btn.id;
            document.getElementById('btn-name').value = btn.name;
            document.getElementById('btn-url').value = btn.url;
            document.getElementById('btn-key-url').value = btn.urlKeyTxt || '';
            document.getElementById('btn-enabled').checked = btn.enabled;
            document.getElementById('btn-maintenance').checked = btn.maintenance;
            document.getElementById('btn-persist').checked = btn.persist;
            document.getElementById('button-modal').style.display = 'flex';
        }
        
        async function saveButton() {
            const buttonData = {
                id: document.getElementById('btn-id').value,
                name: document.getElementById('btn-name').value,
                url: document.getElementById('btn-url').value,
                urlKeyTxt: document.getElementById('btn-key-url').value,
                enabled: document.getElementById('btn-enabled').checked,
                maintenance: document.getElementById('btn-maintenance').checked,
                persist: document.getElementById('btn-persist').checked
            };
            
            if (!currentConfig[editingType]) currentConfig[editingType] = [];
            
            if (editingIndex !== null) {
                currentConfig[editingType][editingIndex] = buttonData;
            } else {
                currentConfig[editingType].push(buttonData);
            }
            
            await saveConfig();
            closeModal();
            loadButtons(editingType);
        }
        
        async function deleteButton(type, index) {
            if (confirm('DELETE THIS BUTTON?')) {
                currentConfig[type].splice(index, 1);
                await saveConfig();
                loadButtons(type);
            }
        }
        
        async function toggleButton(type, index, property) {
            currentConfig[type][index][property] = !currentConfig[type][index][property];
            await saveConfig();
            loadButtons(type);
        }
        
        async function loadRootLibs() {
            if (!currentConfig) await loadConfig();
            const container = document.getElementById('rootlibs-list');
            container.innerHTML = '';
            
            const libs = currentConfig.root_libs || [];
            libs.forEach((lib, index) => {
                container.innerHTML += `
                    <div class="card" style="margin-bottom: 12px;">
                        <h3>${lib.name}</h3>
                        <p><strong>ID:</strong> ${lib.id}</p>
                        <p><strong>PATH:</strong> ${lib.lib_path}</p>
                        <div class="grid grid-2">
                            <span class="badge ${lib.enabled ? 'badge-success' : 'badge-danger'}">${lib.enabled ? 'ENABLED' : 'DISABLED'}</span>
                            <span class="badge ${lib.maintenance ? 'badge-warning' : 'badge-success'}">${lib.maintenance ? 'MAINTENANCE' : 'ACTIVE'}</span>
                        </div>
                        <div class="button-actions">
                            <button class="btn btn-primary" onclick="editRootLib(${index})">EDIT</button>
                            <button class="btn btn-danger" onclick="deleteRootLib(${index})">DELETE</button>
                        </div>
                    </div>
                `;
            });
        }
        
        function addRootLib() {
            editingIndex = null;
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
            editingIndex = index;
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
        
        async function saveRootLib() {
            const libData = {
                id: document.getElementById('lib-id').value,
                name: document.getElementById('lib-name').value,
                url: document.getElementById('lib-url').value,
                lib_path: document.getElementById('lib-path').value,
                arch: document.getElementById('lib-arch').value,
                enabled: document.getElementById('lib-enabled').checked,
                maintenance: document.getElementById('lib-maintenance').checked
            };
            
            if (!currentConfig.root_libs) currentConfig.root_libs = [];
            
            if (editingIndex !== null) {
                currentConfig.root_libs[editingIndex] = libData;
            } else {
                currentConfig.root_libs.push(libData);
            }
            
            await saveConfig();
            closeRootLibModal();
            loadRootLibs();
        }
        
        async function deleteRootLib(index) {
            if (confirm('DELETE THIS ROOT LIB?')) {
                currentConfig.root_libs.splice(index, 1);
                await saveConfig();
                loadRootLibs();
            }
        }
        
        async function loadAssets() {
            if (!currentConfig) await loadConfig();
            document.getElementById('assets_version').value = currentConfig.assets_version || '';
            const container = document.getElementById('assets-list');
            container.innerHTML = '';
            
            const assets = currentConfig.assets || [];
            assets.forEach((asset, index) => {
                container.innerHTML += `
                    <div class="card" style="margin-bottom: 12px;">
                        <h3>${asset.name}</h3>
                        <p><strong>URL:</strong> ${asset.url}</p>
                        <div class="button-actions">
                            <button class="btn btn-primary" onclick="editAsset(${index})">EDIT</button>
                            <button class="btn btn-danger" onclick="deleteAsset(${index})">DELETE</button>
                        </div>
                    </div>
                `;
            });
        }
        
        function addAsset() {
            editingIndex = null;
            document.getElementById('asset-name').value = '';
            document.getElementById('asset-url').value = '';
            document.getElementById('asset-modal').style.display = 'flex';
        }
        
        function editAsset(index) {
            editingIndex = index;
            const asset = currentConfig.assets[index];
            document.getElementById('asset-name').value = asset.name;
            document.getElementById('asset-url').value = asset.url;
            document.getElementById('asset-modal').style.display = 'flex';
        }
        
        async function saveAsset() {
            const assetData = {
                name: document.getElementById('asset-name').value,
                url: document.getElementById('asset-url').value
            };
            
            if (!currentConfig.assets) currentConfig.assets = [];
            
            if (editingIndex !== null) {
                currentConfig.assets[editingIndex] = assetData;
            } else {
                currentConfig.assets.push(assetData);
            }
            
            await saveConfig();
            closeAssetModal();
            loadAssets();
        }
        
        async function deleteAsset(index) {
            if (confirm('DELETE THIS ASSET?')) {
                currentConfig.assets.splice(index, 1);
                await saveConfig();
                loadAssets();
            }
        }
        
        async function createBackup() {
            try {
                const response = await fetch('/api/admin/backup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({note: 'Manual backup'})
                });
                const data = await response.json();
                if (data.success) {
                    showToast('BACKUP CREATED');
                    loadBackups();
                }
            } catch (error) {
                console.error('Error creating backup:', error);
            }
        }
        
        async function loadBackups() {
            try {
                const response = await fetch('/api/admin/backups');
                const backups = await response.json();
                const container = document.getElementById('backups-list');
                container.innerHTML = '';
                
                backups.forEach(backup => {
                    container.innerHTML += `
                        <div class="card" style="margin-bottom: 12px;">
                            <h3>BACKUP #${backup.id}</h3>
                            <p><strong>CREATED:</strong> ${backup.created_at}</p>
                            <p><strong>NOTE:</strong> ${backup.note || 'N/A'}</p>
                            <div class="button-actions">
                                <button class="btn btn-primary" onclick="restoreBackup(${backup.id})">RESTORE</button>
                                <button class="btn btn-danger" onclick="deleteBackup(${backup.id})">DELETE</button>
                            </div>
                        </div>
                    `;
                });
            } catch (error) {
                console.error('Error loading backups:', error);
            }
        }
        
        async function restoreBackup(id) {
            if (confirm('RESTORE THIS BACKUP?')) {
                try {
                    const response = await fetch(`/api/admin/backup/${id}/restore`, {method: 'POST'});
                    const data = await response.json();
                    if (data.success) {
                        showToast('BACKUP RESTORED');
                        await loadConfig();
                    }
                } catch (error) {
                    console.error('Error restoring backup:', error);
                }
            }
        }
        
        async function deleteBackup(id) {
            if (confirm('DELETE THIS BACKUP?')) {
                try {
                    const response = await fetch(`/api/admin/backup/${id}`, {method: 'DELETE'});
                    const data = await response.json();
                    if (data.success) {
                        loadBackups();
                    }
                } catch (error) {
                    console.error('Error deleting backup:', error);
                }
            }
        }
        
        async function loadLogs() {
            try {
                const response = await fetch('/api/admin/logs');
                const logs = await response.json();
                const container = document.getElementById('logs-list');
                container.innerHTML = '';
                
                logs.forEach(log => {
                    container.innerHTML += `
                        <div class="log-entry">
                            <strong>${log.action}</strong>
                            <p>TIME: ${log.timestamp}</p>
                            <p>IP: ${log.ip}</p>
                            ${log.details ? `<p>DETAILS: ${log.details}</p>` : ''}
                        </div>
                    `;
                });
            } catch (error) {
                console.error('Error loading logs:', error);
            }
        }
        
        function refreshJson() {
            const viewer = document.getElementById('json-viewer');
            viewer.textContent = JSON.stringify(currentConfig, null, 2);
        }
        
        function copyJson() {
            navigator.clipboard.writeText(JSON.stringify(currentConfig, null, 2))
                .then(() => showToast('JSON COPIED'));
        }
        
        function downloadJson() {
            const blob = new Blob([JSON.stringify(currentConfig, null, 2)], {type: 'application/json'});
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
        
        // Initial load
        loadConfig();
    </script>
</body>
</html>
"""

# Simple login page
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HEX Protocol - Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Rajdhani', sans-serif;
            background: #000010;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            position: relative;
            overflow: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(ellipse at top left, rgba(0, 255, 255, 0.2), transparent 50%),
                radial-gradient(ellipse at bottom right, rgba(255, 0, 255, 0.15), transparent 50%);
            pointer-events: none;
        }
        
        .login-container {
            background: rgba(20, 20, 40, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 0 60px rgba(0, 255, 255, 0.2);
            position: relative;
            z-index: 1;
        }
        
        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 900;
            background: linear-gradient(135deg, #00ffff, #ff00ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            margin-bottom: 30px;
            letter-spacing: 2px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #00ffff;
            font-weight: 600;
            letter-spacing: 1px;
        }
        
        .form-group input {
            width: 100%;
            padding: 14px;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 10px;
            color: #fff;
            font-size: 1rem;
            transition: all 0.3s;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #00ffff;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #00ffff, #ff00ff);
            color: #000;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 1px;
        }
        
        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0, 255, 255, 0.4);
        }
        
        .error {
            color: #ff0044;
            text-align: center;
            margin-top: 15px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>HEX PROTOCOL</h1>
        <form id="login-form">
            <div class="form-group">
                <label>USERNAME</label>
                <input type="text" id="username" required>
            </div>
            <div class="form-group">
                <label>PASSWORD</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit">LOGIN</button>
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
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = '/admin';
                } else {
                    document.getElementById('error-message').textContent = 'INVALID CREDENTIALS';
                }
            } catch (error) {
                document.getElementById('error-message').textContent = 'LOGIN FAILED';
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
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
        
        print(f"Login attempt: {username}")  # Debug log
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            log_action("Admin login successful", request)
            return {"success": True, "message": "Login successful"}
        
        log_action("Admin login failed", request)
        return {"success": False, "message": "Invalid credentials"}
    except Exception as e:
        print(f"Login error: {e}")
        return {"success": False, "message": str(e)}

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    return FUTURISTIC_HTML

@app.get("/api/admin/config")
async def admin_get_config():
    return load_config()

@app.post("/api/admin/config")
async def admin_update_config(request: Request):
    try:
        config_data = await request.json()
        success = save_config(config_data)
        if success:
            log_action("Configuration updated", request, "Full configuration update")
            return {"success": True, "message": "Configuration saved"}
        else:
            return {"success": False, "message": "Error saving configuration"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/admin/backup")
async def create_backup_endpoint(request: Request):
    data = await request.json()
    note = data.get("note", "")
    success = create_backup(note)
    if success:
        log_action("Backup created", request, note)
        return {"success": True, "message": "Backup created"}
    return {"success": False, "message": "Error creating backup"}

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
            success = save_config(config_data)
            if success:
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