"""
IaC Chatbot — API FastAPI.

Point d'entrée de l'application. Expose :
- POST /chat       → conversation NLU + génération IaC
- GET  /health     → vérification de santé
- GET  /history    → historique des déploiements
- GET  /history/{id} → détail d'une entrée
- GET  /stats      → statistiques
- GET  /report/pdf → rapport PDF téléchargeable
- GET  /stacks     → liste des stacks prédéfinies
"""

import sys
import json
from pathlib import Path

# Ajouter la racine du projet au sys.path pour les imports "backend.app.X"
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
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
from backend.app.cost_estimator import estimer_cout
from backend.app.compliance import verifier_conformite
from backend.app.diagram_gen import generer_diagramme
from backend.app.stacks import detecter_stack, obtenir_stack, lister_stacks
from backend.app.pdf_report import generer_rapport_pdf

app = FastAPI(
    title="IaC Chatbot API",
    version="2.0.0",
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
    1. Détecte si c'est une stack prédéfinie ou une demande de destruction
    2. Extrait les paramètres via Ollama (multi-tours si besoin)
    3. Valide la cohérence métier (Pydantic)
    4. Génère le fichier IaC correspondant
    5. Calcule le coût estimé + conformité sécurité + diagramme
    6. Enregistre dans l'historique
    """
    try:
        # ── Détection de destruction / rollback ──
        prompt_lower = request.message.lower()
        destroy_keywords = ["supprime", "supprimer", "destroy", "détruit", "détruire",
                           "rollback", "delete", "annule", "annuler", "suppression"]
        is_destroy = any(kw in prompt_lower for kw in destroy_keywords)

        if is_destroy:
            return _handle_destroy(request)

        # ── Détection de stacks prédéfinies ──
        stack_name = detecter_stack(request.message)
        if stack_name:
            return _handle_stack(request, stack_name)

        # ── Flux normal : extraction NLU ──
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

        # -- GitOps --
        from backend.app.git_utils import commit_and_push
        msg_commit = f"Auto-provisioning: {resultat.get('nom_ressource', 'Resource')} via Chatbot"
        git_success = commit_and_push(resultat["fichiers"], msg_commit)

        # -- Nouvelles fonctionnalités --
        demande_dict = demande.model_dump()
        cout = estimer_cout(demande_dict)
        conformite = verifier_conformite(demande_dict)
        diagramme = generer_diagramme(demande_dict, resultat["nom_ressource"])

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
            diagram=diagramme,
            cost_estimate=cout,
            compliance=conformite,
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


# ─── Handlers spécialisés ──────────────────────────

def _handle_destroy(request: ChatRequest) -> ChatResponse:
    """Gère les demandes de destruction / rollback."""
    from backend.app.generators.destroy_gen import (
        rechercher_ressource,
        generer_destroy_vsphere,
        generer_destroy_openshift,
    )

    # Rechercher la ressource dans l'historique
    ressources = rechercher_ressource(request.message)

    if not ressources:
        return ChatResponse(
            success=True,
            message="🔍 Je n'ai trouvé aucune ressource correspondant à ta demande dans l'historique. "
                    "Essaye avec un terme plus précis (nom d'image, type de ressource...).",
        )

    # Prendre la plus récente
    derniere = ressources[0]

    # Générer le script de destruction approprié
    if derniere.type_generation and "vsphere" in derniere.type_generation:
        resultat = generer_destroy_vsphere(derniere)
    else:
        resultat = generer_destroy_openshift(derniere)

    history.enregistrer_requete(
        prompt=request.message,
        type_generation=resultat["type"],
        fichiers_generes=resultat["fichiers"],
        statut="success",
    )

    return ChatResponse(
        success=True,
        message=f"🗑️ Script de destruction généré pour la ressource :\n"
                f"• Requête originale : *{derniere.prompt[:80]}*\n"
                f"• Fichier : {Path(resultat['fichiers'][0]).name}\n\n"
                f"⚠️ Exécutez le script manuellement pour confirmer la destruction.",
        generation=GenerationResult(**resultat),
    )


def _handle_stack(request: ChatRequest, stack_name: str) -> ChatResponse:
    """Gère les demandes de déploiement de stacks prédéfinies."""
    stack = obtenir_stack(stack_name)
    if not stack:
        return ChatResponse(success=False, error=f"Stack '{stack_name}' non trouvée.")

    all_results = []
    all_fichiers = []
    total_cost = 0.0
    all_compliance = []
    diagrammes = []

    for res_def in stack["resources"]:
        # Créer une DemandeRessource pour chaque composant
        demande = DemandeRessource(**{k: v for k, v in res_def.items() if k != "label"})
        resultat = generer_iac(demande.model_dump(), namespace=request.namespace)
        all_results.append(GenerationResult(**resultat))
        all_fichiers.extend(resultat["fichiers"])

        # Coût et compliance pour chaque composant
        cout = estimer_cout(demande.model_dump())
        total_cost += cout["total_mensuel"]
        all_compliance.extend(verifier_conformite(demande.model_dump()))
        diagrammes.append(generer_diagramme(demande.model_dump(), resultat["nom_ressource"]))

    # Enregistrer dans l'historique
    history.enregistrer_requete(
        prompt=request.message,
        demande_json=json.dumps({"stack": stack_name, "count": len(stack["resources"])}),
        type_generation=f"stack-{stack_name}",
        fichiers_generes=all_fichiers,
        statut="success",
    )

    # GitOps
    from backend.app.git_utils import commit_and_push
    commit_and_push(all_fichiers, f"Auto-provisioning: Stack {stack['name']} via Chatbot")

    # Message récapitulatif
    composants = "\n".join(
        f"  • {res_def.get('label', res_def['image'])} ({res_def['resource_type']}/{res_def['platform']})"
        for res_def in stack["resources"]
    )

    message = (
        f"🧱 **Stack {stack['name']}** déployée avec succès !\n"
        f"📝 {stack['description']}\n\n"
        f"**Composants générés ({len(stack['resources'])}) :**\n{composants}\n\n"
        f"💰 Coût mensuel total estimé : **{total_cost:.2f}$**"
    )

    return ChatResponse(
        success=True,
        message=message,
        generations=all_results,
        stack_name=stack_name,
        cost_estimate={"total_mensuel": total_cost, "total_annuel": round(total_cost * 12, 2), "devise": "USD"},
        compliance=all_compliance,
        diagram=diagrammes[0] if diagrammes else None,
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
        raise HTTPException(status_code=404, detail="Entrée non trouvée")
    return entry


@app.get("/stats")
def get_stats():
    """Retourne des statistiques sur l'historique."""
    return history.compter_requetes()


# ─── Rapport PDF ────────────────────────────────────

@app.get("/report/pdf")
def download_report():
    """Génère et retourne un rapport PDF des déploiements."""
    pdf_bytes = generer_rapport_pdf()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=iac-chatbot-report.pdf"},
    )


# ─── Stacks prédéfinies ────────────────────────────

@app.get("/stacks")
def get_stacks():
    """Retourne la liste des stacks prédéfinies disponibles."""
    return lister_stacks()


# ─── Lancement ──────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
