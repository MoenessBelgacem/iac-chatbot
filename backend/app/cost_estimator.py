"""
Estimation de coûts d'infrastructure.

Calcule un coût mensuel estimé basé sur les ressources demandées,
en utilisant une grille tarifaire simplifiée inspirée des prix cloud standards.
"""


# Grille tarifaire simplifiée (prix mensuels en USD)
PRICING = {
    "cpu_per_core": 25.0,       # ~25$/mois par vCPU
    "ram_per_gb": 5.0,          # ~5$/mois par Go de RAM
    "storage_per_gb": 0.10,     # ~0.10$/mois par Go de stockage
    "vm_base_cost": 10.0,       # Coût fixe de base pour une VM
    "container_base_cost": 5.0, # Coût fixe de base pour un conteneur
    "network_cost": 3.0,        # Coût réseau forfaitaire
}

# Multiplicateurs par plateforme
PLATFORM_MULTIPLIERS = {
    "vsphere": 1.0,       # On-premise, coût de base
    "openshift": 1.15,    # Léger surcoût lié à l'orchestration K8s
}


def estimer_cout(demande: dict) -> dict:
    """
    Estime le coût mensuel d'une ressource d'infrastructure.

    Args:
        demande: dict issu de DemandeRessource.model_dump()

    Returns:
        dict avec détail du coût et total mensuel/annuel
    """
    resource_type = demande["resource_type"]
    platform = demande["platform"]
    cpu = demande["cpu"]
    ram_gb = demande["ram_gb"]
    storage_gb = demande["storage_gb"]

    # Calcul par poste
    cout_cpu = cpu * PRICING["cpu_per_core"]
    cout_ram = ram_gb * PRICING["ram_per_gb"]
    cout_stockage = storage_gb * PRICING["storage_per_gb"]
    cout_reseau = PRICING["network_cost"]
    cout_base = (
        PRICING["vm_base_cost"]
        if resource_type == "vm"
        else PRICING["container_base_cost"]
    )

    # Sous-total
    sous_total = cout_cpu + cout_ram + cout_stockage + cout_reseau + cout_base

    # Multiplicateur plateforme
    multiplicateur = PLATFORM_MULTIPLIERS.get(platform, 1.0)
    total_mensuel = round(sous_total * multiplicateur, 2)
    total_annuel = round(total_mensuel * 12, 2)

    return {
        "detail": {
            "cpu": f"{cpu} vCPU × {PRICING['cpu_per_core']}$ = {cout_cpu:.2f}$",
            "ram": f"{ram_gb} Go × {PRICING['ram_per_gb']}$ = {cout_ram:.2f}$",
            "stockage": f"{storage_gb} Go × {PRICING['storage_per_gb']}$ = {cout_stockage:.2f}$",
            "reseau": f"{cout_reseau:.2f}$",
            "base": f"{cout_base:.2f}$ ({'VM' if resource_type == 'vm' else 'Conteneur'})",
        },
        "plateforme": platform,
        "multiplicateur_plateforme": multiplicateur,
        "total_mensuel": total_mensuel,
        "total_annuel": total_annuel,
        "devise": "USD",
    }
