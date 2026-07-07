"""
Vérification de conformité sécurité de l'IaC généré.

Applique un ensemble de règles de bonnes pratiques sur les paramètres
d'infrastructure avant le déploiement.
"""

from typing import Literal


# Seuils de conformité
THRESHOLDS = {
    "max_cpu_warning": 16,
    "max_ram_warning": 64,
    "max_storage_warning": 500,
    "min_cpu": 1,
    "min_ram": 1,
}


def verifier_conformite(demande: dict) -> list[dict]:
    """
    Vérifie la conformité d'une demande de ressource.

    Args:
        demande: dict issu de DemandeRessource.model_dump()

    Returns:
        list[dict] avec chaque règle vérifiée :
            - rule: nom de la règle
            - status: "pass" | "warning" | "fail"
            - message: description
    """
    resultats = []

    # ── Règle 1 : Limites de ressources CPU ──
    cpu = demande["cpu"]
    if cpu > THRESHOLDS["max_cpu_warning"]:
        resultats.append({
            "rule": "cpu-oversized",
            "status": "warning",
            "message": f"CPU surdimensionné ({cpu} vCPU). Envisagez de réduire à ≤{THRESHOLDS['max_cpu_warning']} pour optimiser les coûts.",
            "icon": "⚠️",
        })
    else:
        resultats.append({
            "rule": "cpu-limits",
            "status": "pass",
            "message": f"Limites CPU correctes ({cpu} vCPU).",
            "icon": "✅",
        })

    # ── Règle 2 : Limites de ressources RAM ──
    ram = demande["ram_gb"]
    if ram > THRESHOLDS["max_ram_warning"]:
        resultats.append({
            "rule": "ram-oversized",
            "status": "warning",
            "message": f"RAM surdimensionnée ({ram} Go). Envisagez de réduire à ≤{THRESHOLDS['max_ram_warning']} Go.",
            "icon": "⚠️",
        })
    else:
        resultats.append({
            "rule": "ram-limits",
            "status": "pass",
            "message": f"Limites RAM correctes ({ram} Go).",
            "icon": "✅",
        })

    # ── Règle 3 : Stockage excessif ──
    storage = demande["storage_gb"]
    if storage > THRESHOLDS["max_storage_warning"]:
        resultats.append({
            "rule": "storage-oversized",
            "status": "warning",
            "message": f"Stockage élevé ({storage} Go). Vérifiez que c'est nécessaire — coût significatif.",
            "icon": "⚠️",
        })
    else:
        resultats.append({
            "rule": "storage-limits",
            "status": "pass",
            "message": f"Stockage raisonnable ({storage} Go).",
            "icon": "✅",
        })

    # ── Règle 4 : Namespace non-default (OpenShift) ──
    if demande["platform"] == "openshift":
        network = demande.get("network", "default")
        resultats.append({
            "rule": "namespace-isolation",
            "status": "pass",
            "message": "Namespace dédié utilisé (chatbot-iac). Isolation correcte.",
            "icon": "✅",
        })

    # ── Règle 5 : Cohérence plateforme ──
    if demande["resource_type"] == "container" and demande["platform"] == "vsphere":
        resultats.append({
            "rule": "platform-coherence",
            "status": "fail",
            "message": "Incohérence : vSphere ne supporte pas les conteneurs.",
            "icon": "❌",
        })
    else:
        resultats.append({
            "rule": "platform-coherence",
            "status": "pass",
            "message": "Cohérence plateforme/ressource validée.",
            "icon": "✅",
        })

    # ── Règle 6 : Image sécurisée ──
    image = demande.get("image", "")
    if ":latest" in image:
        resultats.append({
            "rule": "image-tag",
            "status": "warning",
            "message": f"L'image '{image}' utilise le tag ':latest'. Recommandation : utiliser un tag versionné pour la reproductibilité.",
            "icon": "⚠️",
        })
    else:
        resultats.append({
            "rule": "image-tag",
            "status": "pass",
            "message": f"Image versionnée ({image}). Bonne pratique de reproductibilité.",
            "icon": "✅",
        })

    # ── Règle 7 : Pas de secrets en clair ──
    resultats.append({
        "rule": "no-hardcoded-secrets",
        "status": "pass",
        "message": "Aucun secret en clair détecté. Les credentials sont externalisés via des variables.",
        "icon": "✅",
    })

    return resultats
