"""
IaC Chatbot — API FastAPI.

Point d'entrée de l'application. Expose :
- POST /chat       → conversation NLU + génération IaC
- GET  /health     → vérification de santé
- GET  /history    → historique des déploiements
- GET  /history/{id} → détail d'une entrée
- GET  /stats      → statistiques
"""

import sys
import json
from pathlib import Path

# Ajouter la racine du projet au sys.path pour les imports "backend.app.X"
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import ValidationError

from backend.app.models import (
    ChatRequest,
    ChatResponse,
    DemandeRessource,
    GenerationResult,
    HistoryEntry,
)
from backend.app.nlu import extraire_demande
from backend.app.generators import generer_iac
from backend.app import history

app = FastAPI(
    title="IaC Chatbot API",
    version="1.0.0",
    description="Infrastructure as Code & Automation pilotée par Chatbot Intelligent",
)

# CORS — autorise le frontend à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir le frontend (version React compilée)
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend-react" / "dist"


@app.on_event("startup")
def mount_frontend():
    """Monte les dossiers statiques du frontend (React Vite)."""
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/")
def serve_index():
    """Sert la page d'accueil du frontend."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "IaC Chatbot API is running. Frontend not found — use /docs for API."}


# ─── Health ─────────────────────────────────────────

@app.get("/health")
def health_check():
    """Vérifie que l'API et Ollama répondent correctement."""
    try:
        import ollama
        ollama.list()
        ollama_ok = True
    except Exception:
        ollama_ok = False
    return {"api": "ok", "ollama": "ok" if ollama_ok else "unreachable"}


# ─── Chat principal ─────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Reçoit un message en langage naturel et :
    1. Extrait les paramètres via Ollama (multi-tours si besoin)
    2. Valide la cohérence métier (Pydantic)
    3. Génère le fichier IaC correspondant
    4. Enregistre dans l'historique
    """
    try:
        session_id, demande, relance, raw_output = extraire_demande(
            request.message, session_id=request.session_id
        )

        # Cas 1 : paramètres manquants → relance
        if demande is None and relance:
            history.enregistrer_requete(
                prompt=request.message,
                statut="clarification",
                erreur=relance,
            )
            return ChatResponse(
                success=True,
                message=relance,
                needs_clarification=True,
                session_id=session_id,
                raw_model_output=raw_output,
            )

        # Cas 2 : extraction réussie → génération IaC
        resultat = generer_iac(demande.model_dump(), namespace=request.namespace)

        history.enregistrer_requete(
            prompt=request.message,
            demande_json=demande.model_dump_json(),
            type_generation=resultat["type"],
            fichiers_generes=resultat["fichiers"],
            statut="success",
        )

        # -- Intégration GitOps --
        from backend.app.git_utils import commit_and_push
        msg_commit = f"Auto-provisioning: {resultat.get('nom_ressource', 'Resource')} via Chatbot"
        git_success = commit_and_push(resultat["fichiers"], msg_commit)
        
        message_succes = _generer_message_succes(demande, resultat)
        if not git_success:
            message_succes += "\n\n⚠️ *L'IaC a été générée localement, mais le push vers GitHub a échoué.*"

        return ChatResponse(
            success=True,
            message=message_succes,
            data=demande,
            generation=GenerationResult(**resultat),
            session_id=session_id,
            raw_model_output=raw_output,
        )

    except ValidationError as e:
        messages_erreur = "; ".join([err["msg"] for err in e.errors()])
        history.enregistrer_requete(
            prompt=request.message,
            statut="error",
            erreur=messages_erreur,
        )
        return ChatResponse(
            success=False,
            error=f"La demande contient une incohérence : {messages_erreur}",
            raw_model_output=raw_output if "raw_output" in dir() else None,
        )

    except json.JSONDecodeError:
        history.enregistrer_requete(
            prompt=request.message,
            statut="error",
            erreur="JSON invalide du modèle",
        )
        return ChatResponse(
            success=False,
            error="Le modèle n'a pas réussi à générer un JSON valide. Reformule ta demande.",
        )

    except Exception as e:
        history.enregistrer_requete(
            prompt=request.message,
            statut="error",
            erreur=str(e),
        )
        return ChatResponse(
            success=False,
            error=f"Erreur inattendue : {str(e)}",
        )


def _generer_message_succes(demande: DemandeRessource, resultat: dict) -> str:
    """Génère un message de confirmation lisible."""
    type_label = "une VM" if demande.resource_type == "vm" else "un conteneur"
    platform_label = "vSphere" if demande.platform == "vsphere" else "OpenShift"
    return (
        f"✅ J'ai généré le code IaC pour {type_label} sur {platform_label} :\n"
        f"• Image : {demande.image}\n"
        f"• CPU : {demande.cpu} | RAM : {demande.ram_gb} Go | Stockage : {demande.storage_gb} Go\n"
        f"• Réseau : {demande.network}\n"
        f"• Fichiers : {', '.join(Path(f).name for f in resultat['fichiers'])}"
    )


# ─── Historique ─────────────────────────────────────

@app.get("/history", response_model=list[HistoryEntry])
def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Retourne les dernières entrées de l'historique."""
    return history.lister_historique(limit=limit, offset=offset)


@app.get("/history/{entry_id}", response_model=HistoryEntry)
def get_history_entry(entry_id: int):
    """Retourne une entrée spécifique de l'historique."""
    entry = history.obtenir_requete(entry_id)
    if not entry:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Entrée non trouvée")
    return entry


@app.get("/stats")
def get_stats():
    """Retourne des statistiques sur l'historique."""
    return history.compter_requetes()


# ─── Lancement ──────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
