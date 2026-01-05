# Task Manager (Flask)

A small Task Manager web app built with Flask, using a JSON file for persistence.

## Requirements
- Python 3.10+
- Recommended: create a virtual environment

## Setup (Windows)
```powershell
python -m venv venv
venv\Scripts\Activate
pip install --upgrade pip
pip install flask
```

## Run (development)
```powershell
python main.py
# then open http://127.0.0.1:5000/
```

## Project layout
- `app.py` — Flask routes and logic
- `main.py` — development entrypoint
- `templates/` — Jinja2 HTML templates
- `static/` — CSS and icons
- `data/tasks.json` — JSON storage for tasks
- `models.py` — optional SQLAlchemy model helpers
- `utils.py` — safe JSON read/write helpers

## API (examples)
- List tasks:
```bash
curl http://127.0.0.1:5000/api/tasks
```
- Add task (JSON):
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"title":"New task","priority":3}' \
  http://127.0.0.1:5000/api/tasks
```
- Update task:
```bash
curl -X PUT -H "Content-Type: application/json" \
  -d '{"status":"done"}' \
  http://127.0.0.1:5000/api/tasks/<task_id>
```
- Delete task:
```bash
curl -X DELETE http://127.0.0.1:5000/api/tasks/<task_id>
```

## UI
- Open the root URL to use the dashboard. Use the `+ New Task` button or the header form to add tasks.
- The app supports filtering and sorting via query params (e.g. `?filter=pending&sort=due&order=asc`).

## Notes
- The app uses `data/tasks.json` for persistence. `utils.read_tasks()` returns an empty list if the file is missing or malformed.
- `app.secret_key` in `app.py` is a development placeholder — change it for production.
- There is an optional `models.py` with SQLAlchemy setup if you prefer to migrate to a database.

## Tests
- No automated tests included yet. You can test endpoints using `curl` as shown above.

If you want, I can add `requirements.txt`, basic `pytest` tests for the API, or Docker support next.
