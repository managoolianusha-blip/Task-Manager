"""Entrypoint for running the Task Manager Flask application.

Execute this module to start a development server on the default Flask
port. In production use a WSGI server and set `debug=False`.
"""

from app import app


if __name__ == '__main__':
    app.run(debug=True)
