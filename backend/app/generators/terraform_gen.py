"""
Générateur Terraform pour VMware vSphere.
Produit un main.tf + variables.tf à partir d'une DemandeRessource validée.
"""

import re
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "generated"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _slugify(texte: str) -> str:
    """Transforme un nom d'image en identifiant Terraform valide."""
    texte = texte.lower().split("/")[-1]
    texte = re.sub(r"[:.]+", "-", texte)
    texte = re.sub(r"[^a-z0-9-]", "", texte)
    texte = re.sub(r"-+", "-", texte).strip("-")
    return texte or "resource"


def generer_vsphere_vm(demande: dict) -> dict:
    """
    Génère les fichiers Terraform pour une VM vSphere.

    Returns:
        dict avec type, fichiers, nom_ressource, contenu
    """
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    vm_name = f"vm-{_slugify(demande['image'])}-{horodatage}"

    contexte = {
        "vm_name": vm_name,
        "cpu": demande["cpu"],
        "ram_gb": demande["ram_gb"],
        "storage_gb": demande["storage_gb"],
        "image": demande["image"],
        "network": demande.get("network", "default"),
    }

    tf_content = _env.get_template("vsphere_vm.tf.j2").render(**contexte)
    vars_content = _env.get_template("vsphere_variables.tf.j2").render(**contexte)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dossier_sortie = OUTPUT_DIR / vm_name
    dossier_sortie.mkdir(exist_ok=True)

    fichier_tf = dossier_sortie / "main.tf"
    fichier_vars = dossier_sortie / "variables.tf"
    fichier_tf.write_text(tf_content, encoding="utf-8")
    fichier_vars.write_text(vars_content, encoding="utf-8")

    return {
        "type": "terraform-vsphere",
        "fichiers": [str(fichier_tf), str(fichier_vars)],
        "nom_ressource": vm_name,
        "contenu": {"main.tf": tf_content, "variables.tf": vars_content},
    }
