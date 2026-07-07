"""Tests pour le module de conformité sécurité."""

from backend.app.compliance import verifier_conformite


def test_conformite_cas_normal():
    """Teste une demande raisonnable — tout doit passer."""
    demande = {
        "resource_type": "container",
        "platform": "openshift",
        "cpu": 2,
        "ram_gb": 4,
        "storage_gb": 20,
        "image": "nginx:1.25",
        "network": "default",
    }
    resultats = verifier_conformite(demande)

    assert len(resultats) > 0
    statuts = [r["status"] for r in resultats]
    assert "fail" not in statuts
    # L'image versionnée devrait passer
    image_rules = [r for r in resultats if r["rule"] == "image-tag"]
    assert image_rules[0]["status"] == "pass"


def test_conformite_cpu_surdimensionne():
    """Teste le warning pour un CPU surdimensionné."""
    demande = {
        "resource_type": "vm",
        "platform": "vsphere",
        "cpu": 24,
        "ram_gb": 4,
        "storage_gb": 50,
        "image": "ubuntu-22.04",
        "network": "default",
    }
    resultats = verifier_conformite(demande)
    cpu_rules = [r for r in resultats if r["rule"] == "cpu-oversized"]
    assert len(cpu_rules) == 1
    assert cpu_rules[0]["status"] == "warning"


def test_conformite_image_latest():
    """Teste le warning pour l'utilisation du tag :latest."""
    demande = {
        "resource_type": "container",
        "platform": "openshift",
        "cpu": 2,
        "ram_gb": 4,
        "storage_gb": 20,
        "image": "redis:latest",
        "network": "default",
    }
    resultats = verifier_conformite(demande)
    image_rules = [r for r in resultats if r["rule"] == "image-tag"]
    assert len(image_rules) == 1
    assert image_rules[0]["status"] == "warning"


def test_conformite_stockage_eleve():
    """Teste le warning pour un stockage élevé."""
    demande = {
        "resource_type": "vm",
        "platform": "vsphere",
        "cpu": 2,
        "ram_gb": 8,
        "storage_gb": 1000,
        "image": "ubuntu-22.04",
        "network": "default",
    }
    resultats = verifier_conformite(demande)
    storage_rules = [r for r in resultats if r["rule"] == "storage-oversized"]
    assert len(storage_rules) == 1
    assert storage_rules[0]["status"] == "warning"
