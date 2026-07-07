"""
Stacks prédéfinies — déploiement de plusieurs ressources en une seule commande.

Chaque stack est une liste de DemandeRessource qui seront générées ensemble.
"""


# Définitions des stacks prédéfinies
STACKS = {
    "lamp": {
        "name": "LAMP Stack",
        "description": "Linux + Apache + MySQL + PHP",
        "resources": [
            {
                "resource_type": "vm",
                "platform": "vsphere",
                "cpu": 2,
                "ram_gb": 4,
                "storage_gb": 40,
                "image": "ubuntu-22.04",
                "network": "default",
                "label": "Serveur Web Apache/PHP (VM)",
            },
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 2,
                "ram_gb": 4,
                "storage_gb": 20,
                "image": "mysql:8.0",
                "network": "default",
                "label": "Base de données MySQL",
            },
        ],
    },
    "wordpress": {
        "name": "WordPress Stack",
        "description": "WordPress + MySQL (conteneurisé)",
        "resources": [
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 2,
                "ram_gb": 2,
                "storage_gb": 10,
                "image": "wordpress:latest",
                "network": "default",
                "label": "WordPress",
            },
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 2,
                "ram_gb": 4,
                "storage_gb": 20,
                "image": "mysql:8.0",
                "network": "default",
                "label": "Base de données MySQL",
            },
        ],
    },
    "monitoring": {
        "name": "Monitoring Stack",
        "description": "Prometheus + Grafana",
        "resources": [
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 2,
                "ram_gb": 4,
                "storage_gb": 50,
                "image": "prom/prometheus:latest",
                "network": "default",
                "label": "Prometheus (Collecte métriques)",
            },
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 1,
                "ram_gb": 2,
                "storage_gb": 10,
                "image": "grafana/grafana:latest",
                "network": "default",
                "label": "Grafana (Tableau de bord)",
            },
        ],
    },
    "cache": {
        "name": "Cache + Reverse Proxy",
        "description": "Redis + Nginx",
        "resources": [
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 1,
                "ram_gb": 2,
                "storage_gb": 5,
                "image": "redis:7",
                "network": "default",
                "label": "Redis (Cache)",
            },
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 1,
                "ram_gb": 1,
                "storage_gb": 5,
                "image": "nginx:stable",
                "network": "default",
                "label": "Nginx (Reverse Proxy)",
            },
        ],
    },
    "elk": {
        "name": "ELK Stack",
        "description": "Elasticsearch + Logstash + Kibana",
        "resources": [
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 4,
                "ram_gb": 8,
                "storage_gb": 100,
                "image": "elasticsearch:8.12.0",
                "network": "default",
                "label": "Elasticsearch (Moteur de recherche)",
            },
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 2,
                "ram_gb": 4,
                "storage_gb": 10,
                "image": "logstash:8.12.0",
                "network": "default",
                "label": "Logstash (Pipeline de données)",
            },
            {
                "resource_type": "container",
                "platform": "openshift",
                "cpu": 1,
                "ram_gb": 2,
                "storage_gb": 5,
                "image": "kibana:8.12.0",
                "network": "default",
                "label": "Kibana (Visualisation)",
            },
        ],
    },
}


# Mots-clés pour la détection de stacks dans le prompt
STACK_KEYWORDS = {
    "lamp": ["lamp", "linux apache mysql", "apache mysql php"],
    "wordpress": ["wordpress", "word press", "wp"],
    "monitoring": ["monitoring", "prometheus", "grafana", "prometheus grafana"],
    "cache": ["cache nginx", "redis nginx", "cache reverse proxy"],
    "elk": ["elk", "elasticsearch", "elastic logstash kibana", "elk stack"],
}


def detecter_stack(prompt: str) -> str | None:
    """
    Détecte si le prompt de l'utilisateur correspond à une stack prédéfinie.

    Args:
        prompt: texte du message utilisateur

    Returns:
        nom de la stack détectée ou None
    """
    prompt_lower = prompt.lower()

    # Vérifier si le mot "stack" est mentionné pour éviter les faux positifs
    has_stack_keyword = any(
        mot in prompt_lower
        for mot in ["stack", "déploie", "deploy", "installe", "install", "monte", "crée", "create"]
    )

    if not has_stack_keyword:
        return None

    for stack_name, keywords in STACK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                return stack_name

    return None


def obtenir_stack(nom: str) -> dict | None:
    """Retourne la définition d'une stack par son nom."""
    return STACKS.get(nom)


def lister_stacks() -> list[dict]:
    """Retourne la liste de toutes les stacks disponibles."""
    return [
        {"id": k, "name": v["name"], "description": v["description"], "count": len(v["resources"])}
        for k, v in STACKS.items()
    ]
