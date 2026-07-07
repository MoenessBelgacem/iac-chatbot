import pytest
from pydantic import ValidationError
from backend.app.models import DemandeRessource

def test_demande_ressource_valid():
    """Test une demande valide pour un conteneur OpenShift"""
    demande = DemandeRessource(
        resource_type="container",
        platform="openshift",
        cpu=2,
        ram_gb=4,
        storage_gb=20,
        image="nginx:latest"
    )
    assert demande.resource_type == "container"
    assert demande.platform == "openshift"
    assert demande.cpu == 2

def test_demande_ressource_valid_vm_vsphere():
    """Test une demande valide pour une VM vSphere"""
    demande = DemandeRessource(
        resource_type="vm",
        platform="vsphere",
        cpu=4,
        ram_gb=8,
        storage_gb=50,
        image="ubuntu-22.04"
    )
    assert demande.resource_type == "vm"
    assert demande.platform == "vsphere"

def test_demande_ressource_invalid_container_vsphere():
    """Test la validation métier : vSphere ne supporte pas les conteneurs"""
    with pytest.raises(ValidationError) as exc_info:
        DemandeRessource(
            resource_type="container",
            platform="vsphere",
            cpu=1,
            ram_gb=2,
            storage_gb=10,
            image="redis:latest"
        )
    assert "Incohérence : VMware vSphere ne supporte pas les conteneurs" in str(exc_info.value)

def test_demande_ressource_invalid_cpu_range():
    """Test les limites de CPU"""
    with pytest.raises(ValidationError):
        DemandeRessource(
            resource_type="vm",
            platform="openshift",
            cpu=0,  # Trop bas
            ram_gb=4,
            storage_gb=20,
            image="centos:9"
        )
    with pytest.raises(ValidationError):
        DemandeRessource(
            resource_type="vm",
            platform="openshift",
            cpu=64,  # Trop haut (max 32 défini)
            ram_gb=4,
            storage_gb=20,
            image="centos:9"
        )
