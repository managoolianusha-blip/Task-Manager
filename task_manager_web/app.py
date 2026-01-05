from flask import Flask, render_template, jsonify, request, abort, redirect, url_for, flash
import os
import json
import uuid
import tempfile
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'change-me-in-production-please'

from utils import read_tasks as load_tasks, write_tasks as save_tasks, add_notification, read_notifications, clear_notifications
from flask import make_response


def _format_display_ts(iso_str: str) -> str:
    """Return a human display string for an ISO date/datetime.

    - Date-only strings (e.g. 'YYYY-MM-DD') -> 'DD-MM-YYYY'
    - Datetime strings (with time) -> 'DD-MM-YYYY HH:MM:SS'
    Falls back to the original string on parse error.
    """
    if not iso_str:
        return ''
    try:
        dt = datetime.fromisoformat(str(iso_str))
        if 'T' not in str(iso_str) and dt.hour == 0 and dt.minute == 0 and dt.second == 0:
            return dt.strftime('%d-%m-%Y')
        return dt.strftime('%d-%m-%Y %H:%M:%S')
    except Exception:
        return str(iso_str)


"""Flask web application for the Task Manager dashboard.

This module defines the HTTP routes used by the UI and a small JSON-backed
API. Tasks are read/written via `utils.read_tasks` / `utils.write_tasks`.

Routes:
- `/` : dashboard view
- `/api/tasks` : GET/POST API for tasks
- `/api/tasks/<id>` : PUT/DELETE API endpoints
- `/add-task`, `/update-task/<id>`, `/delete-task/<id>` : form-backed endpoints
"""


@app.route('/')
def dashboard():
    """Render the dashboard view.

    Computes helpful derived values (completed flag, due-labels, counts)
    and supports filtering (`?filter=...`) and sorting (`?sort=...&order=...`).
    """
    tasks = load_tasks()
    # Normalize task fields for template convenience
    now = datetime.utcnow().date()
    for t in tasks:
        # completed flag from either boolean or status field
        t['completed'] = bool(t.get('completed')) or str(t.get('status', '')).lower() in ('done', 'completed')
        # compute due label
        due_raw = t.get('due_date')
        due_label = None
        if due_raw:
            try:
                # accept date or datetime in ISO format
                due_dt = datetime.fromisoformat(due_raw).date()
                delta = (due_dt - now).days
                if delta < 0:
                    due_label = 'Overdue'
                elif delta == 0:
                    due_label = 'Today'
                elif delta == 1:
                    due_label = 'Tomorrow'
                elif delta <= 7:
                    due_label = 'This week'
                else:
                    due_label = due_dt.strftime('%b %d')
            except Exception:
                due_label = None
        t['due_label'] = due_label
        # formatted display strings for due/created
        t['due_display'] = _format_display_ts(t.get('due_date'))
        t['created_display'] = _format_display_ts(t.get('created_at'))
        # formatted display strings for due/created
        t['due_display'] = _format_display_ts(t.get('due_date'))
        t['created_display'] = _format_display_ts(t.get('created_at'))
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if bool(t.get('completed')) or str(t.get('status')).lower() in ('done', 'completed'))
    pending_tasks = total_tasks - completed_tasks
    try:
        high_priority_tasks = sum(1 for t in tasks if int(t.get('priority', 3)) >= 4)
    except Exception:
        high_priority_tasks = 0

    # Filtering support via ?filter=pending|completed|high
    view = request.args.get('filter', 'all')
    def _is_completed(t):
        return bool(t.get('completed')) or str(t.get('status','')).lower() in ('done','completed')

    if view == 'pending':
        filtered_tasks = [t for t in tasks if not _is_completed(t)]
    elif view == 'completed':
        filtered_tasks = [t for t in tasks if _is_completed(t)]
    elif view == 'high':
        try:
            filtered_tasks = [t for t in tasks if int(t.get('priority', 3)) >= 4]
        except Exception:
            filtered_tasks = []
    else:
        filtered_tasks = tasks

    # Date filtering support via ?date=YYYY-MM-DD
    # Selecting a calendar date will show tasks that have that `due_date`.
    # We only match against `due_date` now so calendar badges and filtering
    # align to due dates (completed tasks may be hidden by the `filter`).
    date_filter = request.args.get('date')
    if date_filter:
        try:
            filtered_tasks = [t for t in filtered_tasks if t.get('due_date') == date_filter]
        except Exception:
            filtered_tasks = []

    # counts for filters
    filter_counts = {
        'all': total_tasks,
        'pending': sum(1 for t in tasks if not _is_completed(t)),
        'completed': sum(1 for t in tasks if _is_completed(t)),
        'high': sum(1 for t in tasks if int(t.get('priority', 3)) >= 4) if tasks else 0,
    }

    # category counts (skip empty/None categories)
    category_counts = {}
    for t in tasks:
        cat = (t.get('category') or '').strip()
        if not cat:
            continue
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Sorting support via ?sort=due|priority and ?order=asc|desc
    sort_by = request.args.get('sort')
    order = request.args.get('order', 'asc')
    def _parse_due(t):
        d = t.get('due_date')
        if not d:
            return None
        try:
            return datetime.fromisoformat(d).date()
        except Exception:
            return None

    if sort_by == 'due':
        # sort by due date, None goes to end
        filtered_tasks.sort(key=lambda x: (_parse_due(x) is None, _parse_due(x) or datetime.max.date()), reverse=(order=='desc'))
    elif sort_by == 'priority':
        # sort by numeric priority
        try:
            filtered_tasks.sort(key=lambda x: int(x.get('priority', 3)), reverse=(order=='desc'))
        except Exception:
            pass

    return render_template(
        'dashboard.html',
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        high_priority_tasks=high_priority_tasks,
        filtered_tasks=filtered_tasks,
        active_filter=view,
        filter_counts=filter_counts,
        active_sort=sort_by,
        active_order=order,
        selected_date=date_filter if date_filter else None,
        unread_count=len(read_notifications()),
        category_counts=category_counts,
    )


@app.route('/my-tasks')
def my_tasks():
    """Render a standalone My Tasks page showing the task list and controls.

    Mirrors the dashboard task list but is a dedicated page with a Back
    to Dashboard action.
    """
    tasks = load_tasks()
    now = datetime.utcnow().date()
    for t in tasks:
        t['completed'] = bool(t.get('completed')) or str(t.get('status', '')).lower() in ('done', 'completed')
        due_raw = t.get('due_date')
        due_label = None
        if due_raw:
            try:
                due_dt = datetime.fromisoformat(due_raw).date()
                delta = (due_dt - now).days
                if delta < 0:
                    due_label = 'Overdue'
                elif delta == 0:
                    due_label = 'Today'
                elif delta == 1:
                    due_label = 'Tomorrow'
                elif delta <= 7:
                    due_label = 'This week'
                else:
                    due_label = due_dt.strftime('%b %d')
            except Exception:
                due_label = None
        t['due_label'] = due_label

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if bool(t.get('completed')) or str(t.get('status')).lower() in ('done', 'completed'))
    pending_tasks = total_tasks - completed_tasks
    try:
        high_priority_tasks = sum(1 for t in tasks if int(t.get('priority', 3)) >= 4)
    except Exception:
        high_priority_tasks = 0

    view = request.args.get('filter', 'all')
    def _is_completed(t):
        return bool(t.get('completed')) or str(t.get('status','')).lower() in ('done','completed')

    if view == 'pending':
        filtered_tasks = [t for t in tasks if not _is_completed(t)]
    elif view == 'completed':
        filtered_tasks = [t for t in tasks if _is_completed(t)]
    elif view == 'high':
        try:
            filtered_tasks = [t for t in tasks if int(t.get('priority', 3)) >= 4]
        except Exception:
            filtered_tasks = []
    else:
        filtered_tasks = tasks

    # Sorting support via ?sort=due|priority and ?order=asc|desc
    sort_by = request.args.get('sort')
    order = request.args.get('order', 'asc')
    def _parse_due(t):
        d = t.get('due_date')
        if not d:
            return None
        try:
            return datetime.fromisoformat(d).date()
        except Exception:
            return None

    if sort_by == 'due':
        filtered_tasks.sort(key=lambda x: (_parse_due(x) is None, _parse_due(x) or datetime.max.date()), reverse=(order=='desc'))
    elif sort_by == 'priority':
        try:
            filtered_tasks.sort(key=lambda x: int(x.get('priority', 3)), reverse=(order=='desc'))
        except Exception:
            pass

    filter_counts = {
        'all': total_tasks,
        'pending': sum(1 for t in tasks if not _is_completed(t)),
        'completed': sum(1 for t in tasks if _is_completed(t)),
        'high': sum(1 for t in tasks if int(t.get('priority', 3)) >= 4) if tasks else 0,
    }

    # compute category counts for my-tasks view as well
    category_counts = {}
    for t in tasks:
        cat = (t.get('category') or '').strip()
        if not cat:
            continue
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return render_template('tasks.html',
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        high_priority_tasks=high_priority_tasks,
        filtered_tasks=filtered_tasks,
        active_filter=view,
        filter_counts=filter_counts,
        active_sort=sort_by,
        active_order=order,
        unread_count=len(read_notifications()),
        category_counts=category_counts,
    )


@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """Return the full list of tasks as JSON."""
    return jsonify(load_tasks())


@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    """Create a new task via JSON API.

    Expects JSON body with at least a `title` field. Returns the created
    task object with generated `id` and `created_at` fields.
    """
    payload = request.get_json(force=True)
    title = (payload or {}).get('title')
    if not title:
        return jsonify({'error': 'title is required'}), 400
    tasks = load_tasks()
    now_date = datetime.utcnow().date().isoformat()
    task = {
        'id': str(uuid.uuid4()),
        'title': title,
        'description': payload.get('description', ''),
        'priority': int(payload.get('priority', 3)) if payload and payload.get('priority') else 3,
        'due_date': payload.get('due_date') or None,
        'status': payload.get('status') or 'Pending',
        'category': payload.get('category', '') or '',
        'completed': bool(payload.get('completed', False)),
        'created_at': now_date,
    }
    tasks.append(task)
    save_tasks(tasks)
    try:
        add_notification(f"Task created: {task.get('title')} (id={task.get('id')})", kind='create')
    except Exception:
        pass
    return jsonify(task), 201


@app.route('/api/tasks/<task_id>', methods=['PUT'])
def api_update_task(task_id):
    """Update a task by `task_id` via JSON API.

    Fields present in the JSON body will be updated on the matching task.
    """
    payload = request.get_json(force=True)
    tasks = load_tasks()
    for t in tasks:
        if t.get('id') == task_id:
            if 'title' in payload:
                t['title'] = payload['title']
            if 'description' in payload:
                t['description'] = payload.get('description', '')
            if 'completed' in payload:
                t['completed'] = bool(payload.get('completed'))
            save_tasks(tasks)
            try:
                add_notification(f"Task updated: {t.get('title')} (id={t.get('id')})", kind='update')
            except Exception:
                pass
            return jsonify(t)
    return jsonify({'error': 'task not found'}), 404


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """Delete a task by `task_id` via JSON API.

    Returns HTTP 204 on success or 404 if the task does not exist.
    """
    tasks = load_tasks()
    # find the task so we can include a friendly title in the notification
    deleted_task = next((t for t in tasks if t.get('id') == task_id), None)
    new_tasks = [t for t in tasks if t.get('id') != task_id]
    if len(new_tasks) == len(tasks):
        return jsonify({'error': 'task not found'}), 404
    save_tasks(new_tasks)
    try:
        if deleted_task and deleted_task.get('title'):
            add_notification(f"Task deleted: {deleted_task.get('title')}", kind='delete')
        else:
            add_notification("Task deleted", kind='delete')
    except Exception:
        pass
    return ('', 204)



@app.route('/add-task', methods=['POST'])
def add_task():
    """Create a new task from a submitted form (modal or header form).

    The route accepts `application/x-www-form-urlencoded` POSTs and also
    JSON requests. On success redirects back to the dashboard and flashes
    a success message.
    """
    # Accept form-encoded or JSON payloads
    if request.is_json:
        payload = request.get_json(force=True)
    else:
        payload = request.form

    title = (payload or {}).get('title')
    if not title:
        abort(400, 'title is required')

    tasks = load_tasks()
    task = {
        'id': str(uuid.uuid4()),
        'title': title,
        'description': payload.get('description', '') if payload else '',
        'priority': int(payload.get('priority', 3)) if payload and payload.get('priority') else 3,
        'due_date': payload.get('due_date') or None,
        'status': payload.get('status') or 'Pending',
        'category': payload.get('category', '') if payload else '',
        'created_at': datetime.utcnow().date().isoformat(),
    }
    tasks.append(task)
    save_tasks(tasks)
    try:
        add_notification(f"Task created: {task.get('title')} (id={task.get('id')})", kind='create')
    except Exception:
        pass
    flash('Task added', 'success')
    return redirect(url_for('dashboard'))


@app.route('/update-task/<task_id>', methods=['POST'])
def update_task(task_id):
    """Handle form-based updates for a specific task.

    This is used by the manual "Update" button in the UI and accepts
    either form data or JSON. After saving redirects back to dashboard.
    """
    # update status or other fields
    if request.is_json:
        payload = request.get_json(force=True)
    else:
        payload = request.form

    tasks = load_tasks()
    for t in tasks:
        if t.get('id') == task_id:
            if 'status' in payload:
                t['status'] = payload.get('status')
            if 'title' in payload:
                t['title'] = payload.get('title')
            if 'description' in payload:
                t['description'] = payload.get('description')
            if 'priority' in payload:
                try:
                    t['priority'] = int(payload.get('priority'))
                except Exception:
                    pass
            if 'due_date' in payload:
                t['due_date'] = payload.get('due_date') or None
            save_tasks(tasks)
            flash('Task updated', 'success')
            try:
                add_notification(f"Task updated: {t.get('title')} (id={t.get('id')})", kind='update')
            except Exception:
                pass
            # Redirect back to the page the user came from (e.g., /my-tasks)
            # Prefer an explicit `next` form field if present, otherwise use the HTTP referrer.
            next_url = None
            try:
                next_url = (payload.get('next') if hasattr(payload, 'get') else None) or request.form.get('next')
            except Exception:
                next_url = None
            if not next_url:
                next_url = request.referrer
            if next_url:
                return redirect(next_url)
            return redirect(url_for('dashboard'))
    abort(404, 'task not found')


@app.route('/delete-task/<task_id>', methods=['POST'])
def delete_task(task_id):
    """Delete a task submitted from a form.

    Prompts confirmation client-side; on success flashes a message and
    redirects back to the dashboard.
    """
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t.get('id') != task_id]
    if len(new_tasks) == len(tasks):
        abort(404, 'task not found')
    save_tasks(new_tasks)
    try:
        deleted_task = next((t for t in tasks if t.get('id') == task_id), None)
        if deleted_task and deleted_task.get('title'):
            add_notification(f"Task deleted: {deleted_task.get('title')}", kind='delete')
        else:
            add_notification("Task deleted", kind='delete')
    except Exception:
        pass
    flash('Task deleted', 'success')
    return redirect(url_for('dashboard'))


@app.route('/notifications')
def notifications():
    """Show persisted notifications and generated due-soon alerts.

    The view shows persisted events (add/update/delete) and also
    computes due-soon alerts for tasks due today or tomorrow.
    """
    notes = read_notifications()
    # derive due-soon alerts
    tasks = load_tasks()
    now = datetime.utcnow().date()
    due_alerts = []
    for t in tasks:
        # skip completed
        completed = bool(t.get('completed')) or str(t.get('status','')).lower() in ('done','completed')
        if completed:
            continue
        due_raw = t.get('due_date')
        if not due_raw:
            continue
        try:
            due_dt = datetime.fromisoformat(due_raw).date()
        except Exception:
            continue
        delta = (due_dt - now).days
        if delta == 0:
            due_alerts.append({'ts': datetime.utcnow().isoformat(), 'kind': 'due', 'message': f"Due Today: {t.get('title')}", 'due': due_raw})
        elif delta == 1:
            due_alerts.append({'ts': datetime.utcnow().isoformat(), 'kind': 'due', 'message': f"Due Tomorrow: {t.get('title')}", 'due': due_raw})

    # show due alerts first, then persisted notes (latest first)
    combined = list(reversed(due_alerts)) + list(reversed(notes))
    # format timestamps for display (DD-MM-YYYY HH:MM:SS) and format any due dates in messages
    def _fmt_iso_ts(iso_str):
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime('%d-%m-%Y %H:%M:%S')
        except Exception:
            return iso_str

    for item in combined:
        # add a display-friendly timestamp (when applicable)
        item['ts_display'] = _fmt_iso_ts(item.get('ts', ''))
        # if this is a due-alert, also provide a display-ready due date
        try:
            due_raw = item.get('due')
            if due_raw:
                try:
                    item['due_display'] = datetime.fromisoformat(due_raw).strftime('%d-%m-%Y %H:%M:%S')
                except Exception:
                    try:
                        item['due_display'] = datetime.fromisoformat(due_raw).date().strftime('%d-%m-%Y')
                    except Exception:
                        item['due_display'] = due_raw
            else:
                item['due_display'] = ''
        except Exception:
            item['due_display'] = ''
    return render_template('notifications.html', notifications=combined, unread_count=len(notes))


@app.route('/notifications/clear', methods=['POST'])
def notifications_clear():
    """Clear persisted notifications and redirect back to notifications page."""
    try:
        clear_notifications()
        flash('Notifications cleared', 'success')
    except Exception:
        flash('Failed to clear notifications', 'danger')
    return redirect(url_for('notifications'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page to choose Light/Dark theme. Persists choice in a cookie."""
    if request.method == 'POST':
        theme = (request.form.get('theme') or '').lower()
        if theme not in ('light', 'dark'):
            theme = 'light'
        resp = make_response(redirect(url_for('settings')))
        # persist for 365 days
        resp.set_cookie('theme', theme, max_age=60 * 60 * 24 * 365)
        flash('Theme updated', 'success')
        return resp

    # GET -> render page; read cookie to know current theme
    current_theme = request.cookies.get('theme', 'light')
    return render_template('settings.html', current_theme=current_theme, unread_count=len(read_notifications()))


if __name__ == '__main__':
    app.run(debug=True)
