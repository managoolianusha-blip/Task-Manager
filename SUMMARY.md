Project Summary

Purpose:
Built a professional Task Manager web app using Flask, Jinja2, vanilla JavaScript and CSS. The app supports task CRUD, a monthly calendar view, persistent notifications, and a light/dark theme.

Key Features:
- Backend: Flask routes for Dashboard, My Tasks, Notifications and Settings, with JSON persistence for tasks and notifications.
- Tasks: Create/update/delete tasks with priority, due dates, filtering and sorting.
- Calendar: Monthly calendar with day selection, badges showing task counts, Clear action and month navigation.
- Notifications: Persisted notifications with unread counts and Clear button.
- Theme: Light/Dark toggle persisted in cookie and applied immediately.
- UX polish: custom checkbox visuals (thick green tick in light, desaturated in dark), pill-style New Task button with circular plus, glassy modals, animated calendar ticks, and responsive layout.

Files changed / key locations:
- `task_manager_web/static/styles.css` — primary styling for themes, buttons, calendar, checkbox and modals.
- `task_manager_web/templates/dashboard.html` — brand, sidebar and main dashboard layout.
- `task_manager_web/templates/*` — tasks, notifications, settings templates updated for UI parity.
- `task_manager_web/app.py` — Flask routes and task handlers.

Run/Preview:
1. `python -m venv venv`
2. `venv\Scripts\Activate.ps1` (PowerShell)
3. `pip install -r requirements.txt`
4. `python task_manager_web/app.py`

Resume blurb (copy-paste):
Task Manager — Personal Project — https://github.com/<your-username>/task-manager
Full-stack Task Manager built with Flask, featuring persistent JSON storage, calendar view, notifications, and responsive light/dark UI. Implemented task CRUD, priority sorting, calendar filtering, and polished UX with custom checkbox visuals and ambient glass modals.
