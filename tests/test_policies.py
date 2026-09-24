"""Tests unitaires du moteur de politique Zero-Trust (PDP)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "gateway"))

from policies import AccessRequest, Effect, evaluate  # noqa: E402


def req(**kw):
    base = dict(
        action="READ_METRICS", target="scada",
        source_zone="ot_supervision", device_posture="managed",
        identity={"user": "u", "role": "operator_ot"},
        token_valid=True, token_expired=False,
    )
    base.update(kw)
    return AccessRequest(**base)


def test_jeton_invalide_refuse():
    d = evaluate(req(token_valid=False, identity=None))
    assert d.effect is Effect.DENY
    assert d.principle == "Verifier explicitement"


def test_jeton_expire_refuse():
    d = evaluate(req(token_expired=True))
    assert d.effect is Effect.DENY
    assert d.principle == "Verifier en continu"


def test_it_ne_peut_pas_ouvrir_la_vanne():
    d = evaluate(req(action="OPEN_VALVE",
                     identity={"user": "j.durand", "role": "admin_it"},
                     source_zone="it"))
    assert d.effect is Effect.DENY
    assert d.principle == "Moindre privilege"


def test_commande_depuis_it_refusee_meme_pour_operateur():
    d = evaluate(req(action="OPEN_VALVE", source_zone="it"))
    assert d.effect is Effect.DENY
    assert d.principle == "Supposer la compromission"


def test_posture_non_maitrisee_refusee():
    d = evaluate(req(action="OPEN_VALVE", device_posture="unmanaged"))
    assert d.effect is Effect.DENY
    assert d.principle == "Verifier explicitement"


def test_operateur_ot_autorise():
    d = evaluate(req(action="OPEN_VALVE"))
    assert d.effect is Effect.ALLOW


def test_maintenance_lecture_seule():
    d = evaluate(req(action="OPEN_VALVE", identity={"user": "p", "role": "maintenance"}))
    assert d.effect is Effect.DENY
    assert d.principle == "Moindre privilege"


def test_lecture_capteurs_autorisee():
    d = evaluate(req(action="READ_SENSORS"))
    assert d.effect is Effect.ALLOW


def test_exfiltration_recettes_refusee_a_tous():
    # Action "engineering" hors de toute matrice RBAC : jamais via le conduit.
    for role in ("admin_it", "operator_ot", "maintenance"):
        d = evaluate(req(action="EXPORT_RECIPES",
                         identity={"user": "x", "role": role}))
        assert d.effect is Effect.DENY
        assert d.principle == "Moindre privilege"
