"""
Routeur de génération IaC.
Dispatch vers le bon générateur selon resource_type + platform.
"""

from backend.app.generators.terraform_gen import generer_vsphere_vm
from backend.app.generators.openshift_gen import (
    generer_openshift_container,
    generer_kubevirt_vm,
)


def generer_iac(demande: dict, namespace: str = "chatbot-iac") -> dict:
    """
    Point d'entrée unique pour la génération IaC.

    Args:
        demande: dict issu de DemandeRessource.model_dump()
        namespace: namespace OpenShift cible (ignoré pour vSphere)

    Returns:
        dict avec type, fichiers, nom_ressource, contenu
    """
    resource_type = demande["resource_type"]
    platform = demande["platform"]

    if resource_type == "vm" and platform == "vsphere":
        return generer_vsphere_vm(demande)

    elif resource_type == "vm" and platform == "openshift":
        return generer_kubevirt_vm(demande, namespace=namespace)

    elif resource_type == "container" and platform == "openshift":
        return generer_openshift_container(demande, namespace=namespace)

    else:
        raise ValueError(
            f"Combinaison non supportée : resource_type={resource_type}, platform={platform}"
        )
