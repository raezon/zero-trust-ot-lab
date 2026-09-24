"""
Moteur de decision Zero-Trust (PDP - Policy Decision Point).

Ce module est volontairement PUR (aucune I/O reseau) pour etre testable
unitairement et pour servir de support pedagogique : chaque regle est
rattachee explicitement a l'un des cinq principes fondateurs du Zero-Trust
vus au Chapitre 4 (verifier explicitement, moindre privilege, supposer la
compromission, microsegmenter, verifier en continu).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Effect(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


# Actions sensibles = commandes qui agissent sur le procede physique (niveau 0/1).
COMMANDES_PROCEDE = {"OPEN_VALVE", "CLOSE_VALVE", "SET_SETPOINT", "STOP_LINE"}
# Actions de lecture (supervision, historian, telemetrie capteurs).
LECTURES = {"READ_METRICS", "READ_STATE", "READ_SENSORS"}
# Actions "engineering" a forte valeur (programme automate, recettes, topologie).
# Volontairement absentes de toute matrice RBAC : elles ne passent JAMAIS par le
# conduit -> il faut un acces local d'ingenierie. Un jeton vole ne les obtient pas.

# Zones "de confiance suffisante" pour EMETTRE une commande vers l'OT.
# Un poste IT (zone "it") ne doit JAMAIS commander directement un automate.
ZONES_COMMANDE_OT = {"ot_supervision", "ot_terrain"}

# Matrice RBAC : role -> actions autorisees (principe de moindre privilege).
RBAC = {
    "admin_it":    LECTURES,                       # IT : lecture historian replique uniquement
    "operator_ot": LECTURES | COMMANDES_PROCEDE,   # operateur OT : lecture + commandes procede
    "maintenance": {"READ_STATE"},                 # prestataire : lecture d'etat seule (JIT)
}


@dataclass
class AccessRequest:
    action: str
    target: str                       # "scada" | "plc"
    source_zone: str = "unknown"      # zone reseau d'origine (conduit emprunte)
    device_posture: str = "unknown"   # "managed" | "unmanaged" | "unknown"
    identity: dict | None = None      # identite resolue (None si jeton invalide)
    token_valid: bool = False
    token_expired: bool = False


@dataclass
class Decision:
    effect: Effect
    reason: str
    principle: str
    request: "AccessRequest | None" = field(default=None, repr=False)

    @property
    def allowed(self) -> bool:
        return self.effect is Effect.ALLOW


def evaluate(req: AccessRequest) -> Decision:
    """Evalue une demande d'acces. Politique par defaut : DENY."""

    # 1. VERIFIER EXPLICITEMENT — pas d'identite valide, pas d'acces.
    if not req.token_valid or req.identity is None:
        return Decision(Effect.DENY,
                        "Jeton d'authentification absent ou invalide.",
                        "Verifier explicitement", req)

    # 2. VERIFIER EN CONTINU — la confiance expire ; on ne l'accorde pas "a vie".
    if req.token_expired:
        return Decision(Effect.DENY,
                        "Jeton expire : la confiance doit etre reevaluee.",
                        "Verifier en continu", req)

    role = req.identity.get("role", "")
    autorisees = RBAC.get(role, set())

    # 3. MOINDRE PRIVILEGE — l'action doit etre explicitement permise au role.
    if req.action not in autorisees:
        return Decision(Effect.DENY,
                        f"Le role '{role}' n'est pas autorise a executer '{req.action}'.",
                        "Moindre privilege", req)

    # 4. SUPPOSER LA COMPROMISSION + MICROSEGMENTATION —
    #    une commande vers le procede ne peut pas provenir de la zone IT.
    if req.action in COMMANDES_PROCEDE and req.source_zone not in ZONES_COMMANDE_OT:
        return Decision(Effect.DENY,
                        f"Commande procede interdite depuis la zone '{req.source_zone}' "
                        f"(conduit non autorise vers l'OT).",
                        "Supposer la compromission", req)

    # 5. VERIFIER EXPLICITEMENT (posture appareil) —
    #    equipement non maitrise = refus sur action sensible.
    if req.action in COMMANDES_PROCEDE and req.device_posture != "managed":
        return Decision(Effect.DENY,
                        f"Posture de l'appareil '{req.device_posture}' insuffisante "
                        f"pour une commande sur le procede.",
                        "Verifier explicitement", req)

    return Decision(Effect.ALLOW,
                    f"Acces accorde a '{req.identity.get('user')}' pour '{req.action}'.",
                    "Acces conforme a la politique", req)
