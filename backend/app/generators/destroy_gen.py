"""
Générateur de code de destruction / rollback.

Génère le code nécessaire pour supprimer des ressources précédemment déployées,
en se basant sur l'historique SQLite.
"""

import json
from pathlib import Path
from datetime import datetime

from backend.app import history

OUTPUT_DIR = Path(__file__).parent.parent.parent / "generated"


def rechercher_ressource(terme: str) -> list[dict]:
    """
    Recherche des ressources dans l'historique par nom ou par type.

    Args:
        terme: terme de recherche (nom de ressource, type, image...)

    Returns:
        list de dict avec les entrées correspondantes
    """
    toutes = history.lister_historique(limit=200)
    resultats = []

    terme_lower = terme.lower()
    for entry in toutes:
        if entry.statut != "success":
            continue
        # Chercher dans le prompt, les fichiers, ou le JSON de la demande
        searchable = f"{entry.prompt} {entry.fichiers_generes or ''} {entry.demande_json or ''}".lower()
        if terme_lower in searchable:
            resultats.append(entry)

    return resultats


def generer_destroy_vsphere(entry: dict) -> dict:
    """
    Génère le script de destruction pour une VM vSphere.

    Returns:
        dict avec type, fichiers, nom_ressource, contenu
    """
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    nom = f"destroy-{horodatage}"

    # Retrouver le dossier Terraform original
    fichiers_originaux = json.loads(entry.fichiers_generes) if entry.fichiers_generes else []
    dossier_original = ""
    for f in fichiers_originaux:
        p = Path(f)
        if p.suffix == ".tf":
            dossier_original = str(p.parent)
            break

    contenu = f"""#!/bin/bash
# ============================================
# Script de destruction - VM vSphere
# Généré automatiquement par le chatbot IaC
# Date : {datetime.now().isoformat()}
# Ressource originale : {entry.prompt}
# ============================================

echo "⚠️  ATTENTION : Vous êtes sur le point de détruire une ressource."
echo "Ressource : {entry.prompt}"
echo ""
read -p "Confirmez la destruction (oui/non) : " confirm

if [ "$confirm" = "oui" ]; then
    cd "{dossier_original}"
    terraform destroy -auto-approve
    echo "✅ Ressource détruite avec succès."
else
    echo "❌ Destruction annulée."
fi
"""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fichier = OUTPUT_DIR / f"{nom}.sh"
    fichier.write_text(contenu, encoding="utf-8")

    return {
        "type": "destroy-vsphere",
        "fichiers": [str(fichier)],
        "nom_ressource": nom,
        "contenu": {f"{nom}.sh": contenu},
    }


def generer_destroy_openshift(entry: dict) -> dict:
    """
    Génère le script de destruction pour une ressource OpenShift.

    Returns:
        dict avec type, fichiers, nom_ressource, contenu
    """
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    nom = f"destroy-{horodatage}"

    fichiers_originaux = json.loads(entry.fichiers_generes) if entry.fichiers_generes else []

    # Construire les commandes oc delete
    delete_commands = []
    for f in fichiers_originaux:
        delete_commands.append(f'oc delete -f "{f}" --ignore-not-found=true')

    contenu = f"""#!/bin/bash
# ============================================
# Script de destruction - OpenShift
# Généré automatiquement par le chatbot IaC
# Date : {datetime.now().isoformat()}
# Ressource originale : {entry.prompt}
# ============================================

echo "⚠️  ATTENTION : Vous êtes sur le point de détruire une ressource."
echo "Ressource : {entry.prompt}"
echo ""
read -p "Confirmez la destruction (oui/non) : " confirm

if [ "$confirm" = "oui" ]; then
{chr(10).join('    ' + cmd for cmd in delete_commands)}
    echo "✅ Ressource détruite avec succès."
else
    echo "❌ Destruction annulée."
fi
"""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fichier = OUTPUT_DIR / f"{nom}.sh"
    fichier.write_text(contenu, encoding="utf-8")

    return {
        "type": "destroy-openshift",
        "fichiers": [str(fichier)],
        "nom_ressource": nom,
        "contenu": {f"{nom}.sh": contenu},
    }
