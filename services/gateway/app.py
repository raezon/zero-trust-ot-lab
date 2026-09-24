"""
Passerelle Zero-Trust : PEP (Policy Enforcement Point) + PDP.

Point d'application UNIQUE (conduit) par lequel transite toute demande d'acces
a l'OT. Elle :
  1. authentifie le sujet (IAM / identities.authenticate),
  2. interroge le moteur de politique (policies.evaluate),
  3. journalise la decision au format JSON (verification continue / detection),
  4. ne relaie la requete a la ressource QUE si la decision est ALLOW.

Conformement a NIST SP 800-207, le sujet ne dialogue jamais directement avec
la ressource : il passe toujours par le PEP.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import time
from collections import deque

import httpx
from fastapi import FastAPI, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import progress
from identities import authenticate
from policies import AccessRequest, Effect, evaluate

SCADA_URL = os.environ.get("SCADA_URL", "http://scada:8000")
PLC_URL = os.environ.get("PLC_URL", "http://plc:8000")
TARGETS = {"scada": SCADA_URL, "plc": PLC_URL}
LAB_MODE = os.environ.get("LAB_MODE", "zero-trust")

logging.basicConfig(level=logging.INFO, format="%(message)s")
audit = logging.getLogger("audit")

app = FastAPI(title="Zero-Trust OT Gateway (PEP/PDP)")

# Journal d'audit en memoire (alimente le tableau de bord live, en plus des logs).
AUDIT_LOG: deque = deque(maxlen=200)
# Dernier rapport d'attaque remonte par le conteneur attacker (vue reelle IT).
LAST_REPORT: dict = {}
_HERE = pathlib.Path(__file__).parent
DASHBOARD_HTML = (_HERE / "dashboard.html").read_text(encoding="utf-8")
ARCHITECTURE_HTML = (_HERE / "architecture.html").read_text(encoding="utf-8")
LEADERBOARD_HTML = (_HERE / "leaderboard.html").read_text(encoding="utf-8")
GUIDE_HTML = (_HERE / "guide.html").read_text(encoding="utf-8")


class CommandIn(BaseModel):
    target: str            # "scada" | "plc"
    action: str            # ex. "OPEN_VALVE", "READ_METRICS"
    params: dict = {}


def _log(decision, req_ctx, extra=None):
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "effect": decision.effect.value,
        "principle": decision.principle,
        "reason": decision.reason,
        "user": (req_ctx.identity or {}).get("user"),
        "role": (req_ctx.identity or {}).get("role"),
        "action": req_ctx.action,
        "target": req_ctx.target,
        "source_zone": req_ctx.source_zone,
        "device_posture": req_ctx.device_posture,
    }
    if extra:
        entry.update(extra)
    audit.info(json.dumps(entry, ensure_ascii=False))
    AUDIT_LOG.append(entry)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/whoami")
def whoami(authorization: str | None = Header(default=None)):
    """Introspection du jeton (IAM) : que vaut ce jeton, pour qui, encore valide ?"""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    identity, valid, expired = authenticate(token)
    return {"valid": valid, "expired": expired, "identity": identity}


# --------------------------------------------------------------------------- #
# Tableau de bord (visualisation pedagogique)
# --------------------------------------------------------------------------- #

@app.get("/", response_class=HTMLResponse)
def architecture():
    """Schema d'architecture anime : propagation de l'attaque IT -> OT."""
    return ARCHITECTURE_HTML


@app.get("/guide", response_class=HTMLResponse)
def guide():
    """Documentation : marche a suivre pas-a-pas des attaques (avec indices)."""
    return GUIDE_HTML


@app.get("/live", response_class=HTMLResponse)
def dashboard():
    """Tableau de bord live branche sur le vrai lab (etats + journal PEP)."""
    return DASHBOARD_HTML


@app.get("/dashboard/state")
async def dashboard_state():
    """Etat live des equipements OT, vus depuis le conduit (la passerelle)."""
    out = {"mode": LAB_MODE, "plc": None, "scada": None}
    async with httpx.AsyncClient(timeout=3) as client:
        for name, path in (("plc", "/state"), ("scada", "/state")):
            try:
                r = await client.get(f"{TARGETS[name]}{path}")
                out[name] = {"reachable": True, "data": r.json()}
            except Exception as exc:
                out[name] = {"reachable": False, "error": type(exc).__name__}
    return out


@app.get("/dashboard/audit")
def dashboard_audit(limit: int = 50):
    return {"entries": list(AUDIT_LOG)[-limit:]}


class AttackReport(BaseModel):
    mode: str = "inconnu"
    ts: str = ""
    steps: list = []


@app.post("/dashboard/report")
def dashboard_report(report: AttackReport):
    """Le conteneur attacker remonte ici le resultat de son scenario."""
    global LAST_REPORT
    LAST_REPORT = report.model_dump()
    return {"ok": True, "received": len(report.steps)}


@app.get("/dashboard/report")
def dashboard_get_report():
    return LAST_REPORT or {"steps": [], "mode": LAB_MODE, "ts": ""}


# --------------------------------------------------------------------------- #
# Mini-LMS : sign-in etudiant, progression, notes, rapport
# --------------------------------------------------------------------------- #

class LoginIn(BaseModel):
    name: str
    email: str = ""
    group: str = ""


class ProgressIn(BaseModel):
    student_id: str
    objective: str


class SubmitIn(BaseModel):
    student_id: str


class EventIn(BaseModel):
    student_id: str
    text: str = ""


@app.get("/lab/objectives")
def lab_objectives():
    return {"objectives": progress.OBJECTIFS, "total": progress.TOTAL}


@app.post("/lab/login")
def lab_login(body: LoginIn):
    if not (body.name or body.email).strip():
        return JSONResponse(status_code=400, content={"error": "nom ou e-mail requis"})
    rec = progress.login(body.name.strip(), body.email.strip(), body.group.strip())
    return {"student_id": rec["id"], "name": rec["name"], "group": rec.get("group", ""),
            "score": rec.get("score", 0), "total": progress.TOTAL,
            "done": list(rec.get("objectifs", {}).keys())}


@app.post("/lab/progress")
def lab_progress(body: ProgressIn):
    return progress.mark(body.student_id, body.objective)


@app.post("/lab/event")
def lab_event(body: EventIn):
    progress.add_event(body.student_id, body.text)
    return {"ok": True}


@app.post("/lab/submit")
def lab_submit(body: SubmitIn):
    return progress.submit(body.student_id)


@app.get("/lab/report.csv")
def lab_report_csv(code: str = ""):
    if code != progress.INSTRUCTOR_CODE:
        return JSONResponse(status_code=403,
                            content={"error": "code formateur invalide (?code=...)"})
    return HTMLResponse(content=progress.to_csv(), media_type="text/csv")


@app.get("/lab/report.json")
def lab_report_json(code: str = ""):
    if code != progress.INSTRUCTOR_CODE:
        return JSONResponse(status_code=403,
                            content={"error": "code formateur invalide (?code=...)"})
    return {"total": progress.TOTAL, "students": progress.all_records()}


@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard_page():
    """Tableau de classement des étudiants (scores et temps)."""
    return LEADERBOARD_HTML


@app.get("/leaderboard.json")
def leaderboard_json():
    """Données du classement (scores, temps, soumissions)."""
    records = progress.all_records()
    return [
        {
            "name": r.get("name", "Anonyme"),
            "email": r.get("email", ""),
            "group": r.get("group", ""),
            "score": r.get("score", 0),
            "total": progress.TOTAL,
            "submitted_at": r.get("submitted_at"),
            "objectifs": list(r.get("objectifs", {}).keys()),
        }
        for r in records
    ]


@app.post("/flat/command")
async def flat_command(body: CommandIn):
    """
    CHEMIN NON SECURISE — simule un RESEAU PLAT (chateau-fort).

    Il n'y a AUCUNE politique, AUCUNE authentification : la requete est relayee
    DIRECTEMENT a la ressource, comme si l'attaquant partageait le meme reseau.
    Sert uniquement a montrer le contraste avec le chemin Zero-Trust (/command).
    """
    base = TARGETS.get(body.target)
    if base is None:
        return JSONResponse(status_code=404,
                            content={"error": f"cible inconnue: {body.target}"})
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(f"{base}/execute",
                                  json={"action": body.action, "params": body.params})
        upstream = r.json()
    except Exception as exc:
        return JSONResponse(status_code=502,
                            content={"error": "ressource injoignable", "detail": str(exc)})
    AUDIT_LOG.append({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "effect": "ALLOW", "principle": "AUCUNE (reseau plat)",
        "reason": "Acces direct sans controle.", "user": "attaquant", "role": "-",
        "action": body.action, "target": body.target,
        "source_zone": "flat", "device_posture": "-",
    })
    return {"decision": "NO_POLICY", "result": upstream}


@app.post("/command")
async def command(
    body: CommandIn,
    request: Request,
    authorization: str | None = Header(default=None),
    x_source_zone: str = Header(default="unknown"),
    x_device_posture: str = Header(default="unknown"),
):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    identity, valid, expired = authenticate(token)

    req_ctx = AccessRequest(
        action=body.action,
        target=body.target,
        source_zone=x_source_zone,
        device_posture=x_device_posture,
        identity=identity,
        token_valid=valid,
        token_expired=expired,
    )

    decision = evaluate(req_ctx)

    if decision.effect is Effect.DENY:
        _log(decision, req_ctx)
        return JSONResponse(
            status_code=403,
            content={"decision": "DENY", "principle": decision.principle,
                     "reason": decision.reason},
        )

    # ALLOW -> relais vers la ressource : le conduit controle.
    base = TARGETS.get(body.target)
    if base is None:
        _log(decision, req_ctx, {"forward": "target_inconnu"})
        return JSONResponse(status_code=404,
                            content={"error": f"cible inconnue: {body.target}"})

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(f"{base}/execute",
                                  json={"action": body.action, "params": body.params})
        upstream = r.json()
    except Exception as exc:  # ressource injoignable
        _log(decision, req_ctx, {"forward": "erreur", "detail": str(exc)})
        return JSONResponse(status_code=502,
                            content={"error": "ressource injoignable", "detail": str(exc)})

    _log(decision, req_ctx, {"forward": "ok"})
    return {"decision": "ALLOW", "principle": decision.principle,
            "reason": decision.reason, "result": upstream}
