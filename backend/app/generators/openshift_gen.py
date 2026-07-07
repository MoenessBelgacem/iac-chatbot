"""
Générateur YAML pour OpenShift.
Produit des manifestes Kubernetes/KubeVirt à partir d'une DemandeRessource validée.

Deux cas :
- Conteneur → Deployment + PVC + Service
- VM KubeVirt → VirtualMachine + PVC
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

# Mapping image -> (port applicatif par défaut, chemin de montage)
IMAGE_DEFAULTS = {
    "nginx": {"port": 80, "mount_path": "/usr/share/nginx/html"},
    "postgres": {"port": 5432, "mount_path": "/var/lib/postgresql/data"},
    "redis": {"port": 6379, "mount_path": "/data"},
    "mysql": {"port": 3306, "mount_path": "/var/lib/mysql"},
    "mongo": {"port": 27017, "mount_path": "/data/db"},
    "httpd": {"port": 80, "mount_path": "/usr/local/apache2/htdocs"},
    "node": {"port": 3000, "mount_path": "/app"},
    "python": {"port": 8000, "mount_path": "/app"},
}
DEFAULT_IMAGE_CONFIG = {"port": 8080, "mount_path": "/data"}


def _slugify(texte: str) -> str:
    """Transforme un nom d'image en identifiant Kubernetes valide."""
    texte = texte.lower().split("/")[-1]
    texte = re.sub(r"[:.]+", "-", texte)
    texte = re.sub(r"[^a-z0-9-]", "", texte)
    texte = re.sub(r"-+", "-", texte).strip("-")
    return texte or "resource"


def _deduire_config_image(image: str) -> dict:
    """Déduit port et chemin de montage à partir du nom de l'image."""
    image_base = image.split(":")[0].split("/")[-1].lower()
    for cle, config in IMAGE_DEFAULTS.items():
        if cle in image_base:
            return config
    return DEFAULT_IMAGE_CONFIG


def generer_openshift_container(demande: dict, namespace: str = "chatbot-iac") -> dict:
    """
    Génère les manifestes YAML pour un conteneur OpenShift.

    Returns:
        dict avec type, fichiers, nom_ressource, contenu
    """
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    app_name = f"{_slugify(demande['image'])}-{horodatage}"
    config_image = _deduire_config_image(demande["image"])

    contexte = {
        "app_name": app_name,
        "namespace": namespace,
        "cpu": demande["cpu"],
        "ram_gb": demande["ram_gb"],
        "storage_gb": demande["storage_gb"],
        "image": demande["image"],
        "container_port": config_image["port"],
        "mount_path": config_image["mount_path"],
    }

    yaml_content = _env.get_template("openshift_container.yaml.j2").render(**contexte)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fichier_yaml = OUTPUT_DIR / f"{app_name}.yaml"
    fichier_yaml.write_text(yaml_content, encoding="utf-8")

    return {
        "type": "container-openshift",
        "fichiers": [str(fichier_yaml)],
        "nom_ressource": app_name,
        "contenu": {f"{app_name}.yaml": yaml_content},
    }


def generer_kubevirt_vm(demande: dict, namespace: str = "chatbot-iac") -> dict:
    """
    Génère les manifestes YAML pour une VM KubeVirt sur OpenShift.

    Returns:
        dict avec type, fichiers, nom_ressource, contenu
    """
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    vm_name = f"vm-{_slugify(demande['image'])}-{horodatage}"

    contexte = {
        "vm_name": vm_name,
        "namespace": namespace,
        "cpu": demande["cpu"],
        "ram_gb": demande["ram_gb"],
        "storage_gb": demande["storage_gb"],
        "image": demande["image"],
        "network": demande.get("network", "default"),
    }

    yaml_content = _env.get_template("kubevirt_vm.yaml.j2").render(**contexte)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fichier_yaml = OUTPUT_DIR / f"{vm_name}.yaml"
    fichier_yaml.write_text(yaml_content, encoding="utf-8")

    return {
        "type": "kubevirt-openshift",
        "fichiers": [str(fichier_yaml)],
        "nom_ressource": vm_name,
        "contenu": {f"{vm_name}.yaml": yaml_content},
    }
