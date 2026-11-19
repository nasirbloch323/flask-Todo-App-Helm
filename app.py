"""ReleaseBoard: a small Flask app for tracking application releases.

Every section is intentionally documented so a beginner can connect Python,
Docker, Kubernetes objects, and Helm values to a working application.
"""

import os  # Read runtime configuration supplied by Docker or Kubernetes.
from contextlib import contextmanager  # Ensure each database connection is closed after use.
import sqlite3  # Use a lightweight database stored on the mounted /data volume.
from datetime import datetime, timezone  # Add consistent UTC timestamps to releases.
from flask import Flask, flash, redirect, render_template, request, url_for  # Build the web UI.

app = Flask(__name__)  # Create the Flask application object.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-development-only")  # Use a Kubernetes Secret in real deployments.
DB_PATH = os.getenv("DATABASE_PATH", "/data/releases.db")  # Keep database files on the persistent volume.
APP_ENV = os.getenv("APP_ENV", "development")  # Show which environment is running.
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")  # Display the version injected by Helm.

@contextmanager
def get_db():
    """Open a SQLite connection and always close it after the caller finishes."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)  # Ensure the database directory exists.
    connection = sqlite3.connect(DB_PATH)  # Open or create the SQLite database file.
    connection.row_factory = sqlite3.Row  # Allow templates to access columns by name.
    try:  # Keep the connection open while the caller performs its SQL work.
        yield connection  # Let the route use the connection inside a with block.
        connection.commit()  # Save successful changes made by the caller.
    except Exception:  # Roll back partial changes if a database operation fails.
        connection.rollback()  # Avoid leaving a half-completed transaction.
        raise  # Preserve the original error for Flask's error handler.
    finally:  # Run cleanup for both successful and failed database operations.
        connection.close()  # Release the SQLite connection after every request.

def initialize_database():
    """Create the releases table when the container starts for the first time."""
    with get_db() as connection:  # Automatically commit successful SQL statements.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                version TEXT NOT NULL,
                environment TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Planned',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)  # Define the fields our release tracker stores.

# Gunicorn imports this module instead of running it as __main__, so initialize here too.
initialize_database()

@app.get("/")
def dashboard():
    """Render the release dashboard and its current statistics."""
    with get_db() as connection:  # Open a short-lived database connection.
        releases = connection.execute(
            "SELECT * FROM releases ORDER BY id DESC"
        ).fetchall()  # Load newest release records first.
        total = connection.execute("SELECT COUNT(*) FROM releases").fetchone()[0]  # Count all releases.
        deployed = connection.execute(
            "SELECT COUNT(*) FROM releases WHERE status = 'Deployed'"
        ).fetchone()[0]  # Count releases marked as deployed.
        planned = connection.execute(
            "SELECT COUNT(*) FROM releases WHERE status = 'Planned'"
        ).fetchone()[0]  # Count releases that are still planned.
    return render_template(
        "index.html",
        releases=releases,
        total=total,
        deployed=deployed,
        planned=planned,
        app_env=APP_ENV,
        app_version=APP_VERSION,
    )  # Pass database records and runtime metadata to the HTML template.

@app.post("/releases")
def create_release():
    """Validate and save a new release submitted from the dashboard."""
    service = request.form.get("service", "").strip()  # Remove accidental whitespace from service name.
    version = request.form.get("version", "").strip()  # Read the version label from the form.
    environment = request.form.get("environment", "Development").strip()  # Read target environment.
    notes = request.form.get("notes", "").strip()  # Read optional release notes.
    if not service or not version:  # Do not save incomplete release records.
        flash("Service name and version are required.", "error")  # Explain the validation failure.
        return redirect(url_for("dashboard"))  # Return the user to the dashboard.
    with get_db() as connection:  # Open a database transaction.
        connection.execute(
            """INSERT INTO releases
               (service, version, environment, status, notes, created_at)
               VALUES (?, ?, ?, 'Planned', ?, ?)""",
            (service, version, environment, notes, datetime.now(timezone.utc).isoformat()),
        )  # Use SQL placeholders to avoid SQL injection.
    flash("Release added to the deployment board.", "success")  # Confirm the saved record.
    return redirect(url_for("dashboard"))  # Refresh the dashboard after submission.

@app.post("/releases/<int:release_id>/status")
def update_status(release_id):
    """Move a release between Planned, Deploying, Deployed, and Failed."""
    allowed = {"Planned", "Deploying", "Deployed", "Failed"}  # Accept only known workflow states.
    status = request.form.get("status", "")  # Read the requested status.
    if status not in allowed:  # Reject unexpected values from a modified browser request.
        flash("Invalid release status.", "error")  # Show a safe validation message.
        return redirect(url_for("dashboard"))  # Return without changing the database.
    with get_db() as connection:  # Open a database transaction.
        connection.execute(
            "UPDATE releases SET status = ? WHERE id = ?",
            (status, release_id),
        )  # Update only the selected release row.
    flash("Release status updated.", "success")  # Confirm the status change.
    return redirect(url_for("dashboard"))  # Reload the release list.

@app.post("/releases/<int:release_id>/delete")
def delete_release(release_id):
    """Delete one release record using a POST request."""
    with get_db() as connection:  # Open a database transaction.
        connection.execute("DELETE FROM releases WHERE id = ?", (release_id,))  # Delete by safe parameter.
    flash("Release removed from the board.", "success")  # Confirm the deletion.
    return redirect(url_for("dashboard"))  # Return to the main screen.

@app.get("/healthz")
def health():
    """Liveness probe: confirms that the Python web process can answer HTTP."""
    return {"status": "ok", "service": "releaseboard"}, 200  # Kubernetes restarts a container if this fails.

@app.get("/readyz")
def readiness():
    """Readiness probe: verify that the app can reach its SQLite database."""
    try:  # Catch database errors so Kubernetes receives a useful failure response.
        with get_db() as connection:  # Open the configured database file.
            connection.execute("SELECT 1").fetchone()  # Run a tiny query to validate connectivity.
        return {"status": "ready"}, 200  # Kubernetes may now send traffic to this Pod.
    except sqlite3.Error:  # Handle a missing or unavailable database.
        return {"status": "not-ready"}, 503  # Remove this Pod from Service endpoints temporarily.

@app.get("/metrics")
def metrics():
    """Expose a tiny Prometheus text endpoint without an extra dependency."""
    with get_db() as connection:  # Read counters from the application database.
        total = connection.execute("SELECT COUNT(*) FROM releases").fetchone()[0]  # Total release count.
        deployed = connection.execute(
            "SELECT COUNT(*) FROM releases WHERE status = 'Deployed'"
        ).fetchone()[0]  # Successfully deployed release count.
    body = (
        "# HELP releaseboard_releases_total Number of tracked releases.\n"
        "# TYPE releaseboard_releases_total gauge\n"
        f"releaseboard_releases_total {total}\n"
        "# HELP releaseboard_deployed_total Number of deployed releases.\n"
        "# TYPE releaseboard_deployed_total gauge\n"
        f"releaseboard_deployed_total {deployed}\n"
    )  # Format metrics using the Prometheus text exposition format.
    return body, 200, {"Content-Type": "text/plain; version=0.0.4; charset=utf-8"}  # Return scrapeable metrics.

if __name__ == "__main__":  # Run this block only when executing python app.py directly.
    initialize_database()  # Prepare the local database before accepting requests.
    app.run(host="0.0.0.0", port=5000)  # Listen on all container interfaces for local development.
