"""
Modèles Pydantic partagés — source unique de vérité.
Utilisé par le NLU, l'API, le générateur IaC et l'historique.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional
from datetime import datetime


class DemandeRessource(BaseModel):
    """Paramètres d'infrastructure extraits d'une requête en langage naturel."""

    resource_type: Literal["vm", "container"]
    platform: Literal["vsphere", "openshift"]
    cpu: int = Field(ge=1, le=32)
    ram_gb: int = Field(ge=1, le=128)
    storage_gb: int = Field(ge=1, le=2000)
    image: str
    network: Optional[str] = "default"

    @model_validator(mode="after")
    def verifier_coherence_plateforme(self):
        """VMware vSphere ne supporte pas les conteneurs — uniquement OpenShift."""
        if self.resource_type == "container" and self.platform == "vsphere":
            raise ValueError(
                "Incohérence : VMware vSphere ne supporte pas les conteneurs. "
                "Un conteneur doit être déployé sur OpenShift."
            )
        return self


class ChatRequest(BaseModel):
    """Requête entrante depuis le frontend."""

    message: str
    session_id: Optional[str] = None
    namespace: Optional[str] = "chatbot-iac"


class GenerationResult(BaseModel):
    """Résultat de la génération IaC."""

    type: str
    fichiers: list[str]
    nom_ressource: str
    contenu: Optional[dict[str, str]] = None  # nom_fichier -> contenu


class ChatResponse(BaseModel):
    """Réponse structurée vers le frontend."""

    success: bool
    message: Optional[str] = None  # message conversationnel du bot
    data: Optional[DemandeRessource] = None
    generation: Optional[GenerationResult] = None
    generations: Optional[list[GenerationResult]] = None  # Pour les stacks multi-ressources
    error: Optional[str] = None
    raw_model_output: Optional[str] = None
    needs_clarification: bool = False
    session_id: Optional[str] = None
    # Nouvelles fonctionnalités
    diagram: Optional[str] = None           # Code Mermaid du diagramme d'architecture
    cost_estimate: Optional[dict] = None    # Estimation de coûts
    compliance: Optional[list[dict]] = None # Résultats de conformité sécurité
    stack_name: Optional[str] = None        # Nom de la stack si applicable


class HistoryEntry(BaseModel):
    """Entrée dans l'historique des déploiements."""

    id: int
    timestamp: str
    prompt: str
    demande_json: Optional[str] = None
    type_generation: Optional[str] = None
    fichiers_generes: Optional[str] = None
    statut: str  # "success", "error", "clarification"
    erreur: Optional[str] = None
