# Blog Auto Upload - Windows Setup & Run Guide

This folder contains the automation scripts for Naver and Tistory blog posting.

## Prerequisites
- A Windows machine (Windows 10 or 11 recommended).
- Internet connection.
- **Google Chrome** installed (Standard version).
- Admin rights (to install Python if not present).

## How to Run
1. **Download/Clone** this entire folder to your Windows machine.
2. **Configuration**:
   - Rename `.env.example` to `.env`.
   - Open `.env` with Notepad and fill in your:
     - `DATABASE_URL`: Connection string to your PostgreSQL database.
     - `NAVER_COOKIES`: (Optional) If using cookie login.
3. **Execute**:
   - Double-click `run_on_windows.bat`.
   - The script will:
     - Check for Python. If missing, it will try to install it (approve any prompts).
     - Create a virtual environment (`venv`).
     - Install necessary libraries.
     - Start the automation loop (`main.py`).

## Troubleshooting
- If the window closes immediately, try running it from a Command Prompt (cmd.exe) to see errors.
- If Python installation fails, install Python 3.11+ manually from python.org and check "Add Python to PATH" during installation.
