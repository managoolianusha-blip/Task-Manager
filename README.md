# Task Manager

A professional Task Manager web app built with Flask, featuring task CRUD, calendar view, persistent notifications, and light/dark themes.

## Demo
- Run locally (see Run section) or host remotely.

## Features
- Task create / read / update / delete with priority and due dates
- Monthly calendar with day selection, task badges, and navigation
- Persistent notifications with unread badge and clear action
- Light / Dark theme toggle persisted in a cookie
- Responsive layout: sidebar + hamburger, ambient glass modals
- Custom checkbox visuals and task priority indicators

## Tech Stack
- Backend: Python + Flask
- Templates: Jinja2
- Frontend: Vanilla JavaScript + CSS
- Storage: JSON files under `task_manager_web/data/`

## Run locally
1. Create a virtual environment and activate it:

```powershell
cd "C:\Task Manager"
python -m venv venv
venv\Scripts\Activate.ps1   # PowerShell
# or: venv\Scripts\activate.bat  (cmd)
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the app:

```powershell
python task_manager_web/app.py
```

Open http://127.0.0.1:5000 in your browser.

## Data
Persistent JSON files live in `task_manager_web/data/` (tasks and notifications). Back these up if needed.

## Files of interest
- `task_manager_web/app.py` — Flask app entry
- `task_manager_web/utils.py` — helper read/write functions
- `task_manager_web/static/styles.css` — main stylesheet
- `task_manager_web/templates/` — HTML templates (dashboard, tasks, notifications, settings)


## License
This project is licensed under the MIT License — see `LICENSE`.

