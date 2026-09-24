"""
Magasin d'identites et validation de jetons (simulateur d'IAM).

En production, ce role est tenu par un IdP (Azure AD, Keycloak...) avec des
jetons signes (OIDC / JWT). Ici on simule un jeton opaque assorti d'une duree
de vie (TTL) pour illustrer la "verification continue".

/!\\ Jetons en clair : usage strictement pedagogique dans le lab.
"""
from __future__ import annotations

import time

IDENTITES = {
    "tok-admin-it": {
        "user": "j.durand", "role": "admin_it",
        "home_zone": "it", "issued_at": None, "ttl": 3600,
    },
    "tok-operator-ot": {
        "user": "operateur.nantes", "role": "operator_ot",
        # TTL tres long (30 j) pour que le chemin gagnant reste jouable en
        # continu (cours + deploiement en ligne). La demo "verifier en continu"
        # reste assuree par tok-expire (deja expire) et tok-maintenance (5 min).
        "home_zone": "ot_supervision", "issued_at": None, "ttl": 2592000,
    },
    "tok-maintenance": {
        "user": "prestataire.ext", "role": "maintenance",
        "home_zone": "dmz", "issued_at": None, "ttl": 300,
    },
    # Jeton volontairement DEJA expire (demo "verifier en continu").
    "tok-expire": {
        "user": "ancien.compte", "role": "operator_ot",
        "home_zone": "ot_supervision", "issued_at": 0, "ttl": 60,
    },
}


def _bootstrap() -> None:
    now = time.time()
    for ident in IDENTITES.values():
        if ident["issued_at"] is None:
            ident["issued_at"] = now


_bootstrap()


def authenticate(token: str | None, now: float | None = None):
    """Retourne (identity | None, token_valid: bool, token_expired: bool)."""
    if now is None:
        now = time.time()
    ident = IDENTITES.get(token or "")
    if ident is None:
        return None, False, False
    expired = (now - ident["issued_at"]) > ident["ttl"]
    public = {k: ident[k] for k in ("user", "role", "home_zone")}
    return public, True, expired
