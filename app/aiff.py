"""AI Factory (AIFF) portal module.

The guided, cross-blade demo — Access Control / Anti-Virus / IPS — for the "protecting the AI
factory" workshop. The heavy lifting (benign netns probes that cross the BlueField-3 DPU, the
Check Point Management Web API posture toggle, and the Threat-Prevention log reads) runs in the
aiff-gw agent (Lab-Environment/attack-demo/aiff-demo.py). This module serves the portal page and
proxies its small JSON API to that agent, behind the same login as the rest of the server.

Point it at the agent with AIFF_AGENT_URL (default http://host.docker.internal:8090, which reaches
a mock/real agent on the Docker host). For local Docker testing run the agent with AIFF_MOCK=1.
"""
import os

import requests
from flask import render_template, jsonify, request, Response

from . import app
from .views import login_required

AGENT_URL = os.environ.get("AIFF_AGENT_URL", "http://host.docker.internal:8090").rstrip("/")
AGENT_TIMEOUT = float(os.environ.get("AIFF_AGENT_TIMEOUT", "240"))


@app.route("/aiff")
@login_required
def aiff_portal():
    return render_template("aiff.html", agent_url=AGENT_URL)


def _proxy(method, path):
    """Forward one call to the aiff-gw agent, passing its JSON straight back. The agent is the
    only thing that can touch the lab pod; this server never talks to the firewall directly."""
    url = f"{AGENT_URL}{path}"
    try:
        r = requests.request(method, url, timeout=AGENT_TIMEOUT)
        return Response(r.content, status=r.status_code,
                        content_type=r.headers.get("Content-Type", "application/json"))
    except requests.RequestException as e:
        return jsonify({"ok": False, "error": f"AIFF agent unreachable at {AGENT_URL}: {e}"}), 502


@app.route("/aiff/api/config")
@login_required
def aiff_config():
    return _proxy("GET", "/api/config")


@app.route("/aiff/api/status")
@login_required
def aiff_status():
    return _proxy("GET", "/api/status")


@app.route("/aiff/api/logrule/<attack_id>")
@login_required
def aiff_logrule(attack_id):
    return _proxy("GET", f"/api/logrule/{attack_id}")


@app.route("/aiff/api/threatlog/<attack_id>")
@login_required
def aiff_threatlog(attack_id):
    return _proxy("GET", f"/api/threatlog/{attack_id}")


@app.route("/aiff/api/setup", methods=["POST"])
@login_required
def aiff_setup():
    q = "?force=1" if request.args.get("force") == "1" else ""
    return _proxy("POST", f"/api/setup{q}")


@app.route("/aiff/api/toggle/<state>", methods=["POST"])
@login_required
def aiff_toggle(state):
    return _proxy("POST", f"/api/toggle/{state}")


@app.route("/aiff/api/run/<attack_id>", methods=["POST"])
@login_required
def aiff_run(attack_id):
    return _proxy("POST", f"/api/run/{attack_id}")
