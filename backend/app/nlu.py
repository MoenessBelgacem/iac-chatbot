"""
NLU — Extraction de paramètres d'infrastructure via Ollama.

Gère :
- L'extraction structurée (sortie JSON forcée via Pydantic schema)
- La conversation multi-tours (relance si paramètres manquants/ambigus)
- Le contexte de session en mémoire
"""

import uuid
import json
from typing import Optional

import ollama
from pydantic import ValidationError

from backend.app.models import DemandeRessource

SYSTEM_PROMPT = """\
Tu es un assistant spécialisé en infrastructure IT. Tu aides les utilisateurs à déployer des VMs et des conteneurs.

Quand l'utilisateur fait une demande de déploiement, extrait STRICTEMENT les paramètres suivants :

Règles d'extraction :
- resource_type = "container" si l'utilisateur mentionne un conteneur, container, pod, ou une application applicative (nginx, postgres, redis, etc.)
- resource_type = "vm" si l'utilisateur mentionne explicitement une VM, machine virtuelle, ou un OS complet (ubuntu, windows server, centos comme OS de VM)
- platform = "vsphere" ou "openshift" selon ce qui est mentionné
- IMPORTANT : VMware vSphere ne supporte QUE les VMs, jamais les conteneurs. Si l'utilisateur demande un conteneur sans préciser la plateforme, utilise "openshift" par défaut.
- Si platform n'est pas mentionnée : "vsphere" pour les VMs, "openshift" pour les conteneurs
- Si storage_gb n'est pas précisé, utilise 20 comme valeur par défaut
- Si cpu n'est pas précisé, utilise 2 comme valeur par défaut
- Si ram_gb n'est pas précisé, utilise 4 comme valeur par défaut
- image doit être un nom d'image réaliste correspondant à la demande (ex: "nginx:latest", "postgres:15", "ubuntu-22.04")
- network : utilise "default" si non précisé
"""

CLARIFICATION_PROMPT = """\
Tu es un assistant infrastructure IT. L'utilisateur a fait une demande mais il manque des informations.
Voici ce que tu as compris jusqu'ici : {context}
Voici l'erreur de validation : {error}

Génère une question courte et naturelle (en français) pour demander les informations manquantes.
Ne pose qu'UNE seule question à la fois, la plus importante.
Réponds UNIQUEMENT avec la question, sans préambule.
"""

# Sessions en mémoire : session_id -> list[dict] (historique messages)
_sessions: dict[str, list[dict]] = {}


def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, list[dict]]:
    """Récupère ou crée une session de conversation."""
    if session_id and session_id in _sessions:
        return session_id, _sessions[session_id]
    new_id = session_id or str(uuid.uuid4())
    _sessions[new_id] = []
    return new_id, _sessions[new_id]


def cleanup_old_sessions(max_sessions: int = 100):
    """Supprime les sessions les plus anciennes si on dépasse le max."""
    if len(_sessions) > max_sessions:
        oldest_keys = list(_sessions.keys())[: len(_sessions) - max_sessions]
        for key in oldest_keys:
            del _sessions[key]


def extraire_demande(
    prompt_utilisateur: str,
    session_id: Optional[str] = None,
) -> tuple[str, Optional[DemandeRessource], Optional[str], str]:
    """
    Extrait les paramètres d'infrastructure depuis un prompt utilisateur.

    Returns:
        tuple: (session_id, demande_validée_ou_None, message_relance_ou_None, raw_output)
    """
    sid, messages = get_or_create_session(session_id)

    # Ajouter le nouveau message au contexte
    messages.append({"role": "user", "content": prompt_utilisateur})

    # Construire la conversation complète pour le LLM
    llm_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    # Appel Ollama avec sortie structurée
    reponse = ollama.chat(
        model="llama3.1",
        messages=llm_messages,
        format=DemandeRessource.model_json_schema(),
        options={"temperature": 0},
    )
    raw_output = reponse.message.content

    # Tenter la validation Pydantic
    try:
        demande = DemandeRessource.model_validate_json(raw_output)
        # Succès — nettoyer la session
        if sid in _sessions:
            del _sessions[sid]
        cleanup_old_sessions()
        return sid, demande, None, raw_output

    except ValidationError as e:
        # Générer une question de relance
        question = _generer_relance(raw_output, str(e))
        messages.append({"role": "assistant", "content": question})
        return sid, None, question, raw_output


def _generer_relance(contexte_json: str, erreur: str) -> str:
    """Génère une question de relance contextuelle via Ollama."""
    try:
        reponse = ollama.chat(
            model="llama3.1",
            messages=[
                {
                    "role": "user",
                    "content": CLARIFICATION_PROMPT.format(
                        context=contexte_json, error=erreur
                    ),
                }
            ],
            options={"temperature": 0.3},
        )
        return reponse.message.content.strip()
    except Exception:
        return (
            "Je n'ai pas réussi à comprendre tous les paramètres. "
            "Peux-tu préciser le type de ressource (VM ou conteneur), "
            "la plateforme (vSphere ou OpenShift), et les specs (CPU, RAM, stockage) ?"
        )
