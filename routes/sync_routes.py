"""Lightweight invalidation for separate browsers using the shared MySQL data."""
import hashlib
import json

from flask import Blueprint, jsonify, session
from database.connection import query_db
from routes import login_required
from services.app_version_service import get_app_version

sync_bp = Blueprint('sync_bp', __name__)


@sync_bp.get('/api/sync')
@login_required
def sync_status():
    # An opaque change token only; never return another user's records or audit data.
    clock = query_db('SELECT COALESCE(MAX(id),0) AS revision FROM audit_logs', one=True)
    memberships = query_db('SELECT project_id,project_role FROM project_members WHERE user_id=%s ORDER BY project_id',
                           (session['user_id'],))
    notifications = query_db('''SELECT COUNT(*) AS total, COALESCE(MAX(id),0) AS latest,
        COALESCE(SUM(CASE WHEN is_read=FALSE THEN 1 ELSE 0 END),0) AS unread
        FROM notifications WHERE user_id=%s''', (session['user_id'],), one=True)
    payload = [clock['revision'], session['user_id'], session['role'], session.get('full_name'), memberships, notifications]
    revision = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode('utf-8')).hexdigest()
    return jsonify(success=True, revision=revision, app_version=get_app_version(), poll_seconds=5)
