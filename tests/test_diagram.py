"""Tests pour le module de génération de diagrammes Mermaid."""

from backend.app.diagram_gen import generer_diagramme


def test_diagramme_vsphere_vm():
    """Teste la génération de diagramme pour une VM vSphere."""
    demande = {
        "resource_type": "vm",
        "platform": "vsphere",
        "cpu": 4,
        "ram_gb": 8,
        "storage_gb": 50,
        "image": "ubuntu-22.04",
        "network": "default",
    }
    diagramme = generer_diagramme(demande, "vm-ubuntu-test")

    assert "graph TD" in diagramme
    assert "vSphere" in diagramme
    assert "4 vCPU" in diagramme
    assert "8 Go RAM" in diagramme
    assert "50 Go" in diagramme


def test_diagramme_openshift_container():
    """Teste la génération de diagramme pour un conteneur OpenShift."""
    demande = {
        "resource_type": "container",
        "platform": "openshift",
        "cpu": 2,
        "ram_gb": 4,
        "storage_gb": 20,
        "image": "nginx:latest",
        "network": "default",
    }
    diagramme = generer_diagramme(demande, "nginx-test")

    assert "graph TD" in diagramme
    assert "OpenShift" in diagramme
    assert "Deployment" in diagramme
    assert "Service" in diagramme
    assert "PVC" in diagramme


def test_diagramme_kubevirt():
    """Teste la génération de diagramme pour une VM KubeVirt."""
    demande = {
        "resource_type": "vm",
        "platform": "openshift",
        "cpu": 2,
        "ram_gb": 4,
        "storage_gb": 20,
        "image": "centos-stream-9",
        "network": "default",
    }
    diagramme = generer_diagramme(demande, "vm-centos-test")

    assert "graph TD" in diagramme
    assert "VirtualMachine" in diagramme
    assert "Cloud-Init" in diagramme
