"""Tests pour le module d'estimation de coûts."""

from backend.app.cost_estimator import estimer_cout


def test_estimer_cout_vm_vsphere():
    """Teste l'estimation de coût pour une VM vSphere."""
    demande = {
        "resource_type": "vm",
        "platform": "vsphere",
        "cpu": 4,
        "ram_gb": 8,
        "storage_gb": 50,
        "image": "ubuntu-22.04",
        "network": "default",
    }
    resultat = estimer_cout(demande)

    assert resultat["devise"] == "USD"
    assert resultat["total_mensuel"] > 0
    assert resultat["total_annuel"] == round(resultat["total_mensuel"] * 12, 2)
    assert resultat["multiplicateur_plateforme"] == 1.0
    assert "cpu" in resultat["detail"]
    assert "ram" in resultat["detail"]
    assert "stockage" in resultat["detail"]


def test_estimer_cout_container_openshift():
    """Teste l'estimation pour un conteneur OpenShift (multiplicateur 1.15)."""
    demande = {
        "resource_type": "container",
        "platform": "openshift",
        "cpu": 2,
        "ram_gb": 4,
        "storage_gb": 20,
        "image": "nginx:latest",
        "network": "default",
    }
    resultat = estimer_cout(demande)

    assert resultat["multiplicateur_plateforme"] == 1.15
    assert resultat["total_mensuel"] > 0


def test_cout_augmente_avec_ressources():
    """Vérifie que le coût augmente proportionnellement avec les ressources."""
    petit = estimer_cout({
        "resource_type": "vm", "platform": "vsphere",
        "cpu": 1, "ram_gb": 1, "storage_gb": 10, "image": "test", "network": "default",
    })
    gros = estimer_cout({
        "resource_type": "vm", "platform": "vsphere",
        "cpu": 16, "ram_gb": 64, "storage_gb": 500, "image": "test", "network": "default",
    })

    assert gros["total_mensuel"] > petit["total_mensuel"]
