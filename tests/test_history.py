import pytest
from unittest.mock import patch
from backend.app.history import enregistrer_requete, obtenir_requete, lister_historique, compter_requetes

# Utilise une base en mémoire pour les tests via un mock
@pytest.fixture(autouse=True)
def mock_db_path(tmp_path):
    with patch("backend.app.history.DB_PATH", tmp_path / "test_history.db"):
        yield

def test_enregistrer_et_obtenir_requete():
    entry_id = enregistrer_requete(
        prompt="Créer une VM",
        demande_json='{"resource_type": "vm", "platform": "vsphere"}',
        type_generation="terraform-vsphere",
        fichiers_generes=["main.tf", "variables.tf"],
        statut="success"
    )
    
    entry = obtenir_requete(entry_id)
    assert entry is not None
    assert entry.id == entry_id
    assert entry.prompt == "Créer une VM"
    assert entry.statut == "success"
    assert entry.type_generation == "terraform-vsphere"
    assert "main.tf" in entry.fichiers_generes

def test_lister_historique():
    enregistrer_requete(prompt="Test 1", statut="success")
    enregistrer_requete(prompt="Test 2", statut="error", erreur="Failed")
    enregistrer_requete(prompt="Test 3", statut="clarification")
    
    historique = lister_historique(limit=2)
    assert len(historique) == 2
    assert historique[0].prompt == "Test 3" # Le plus récent en premier
    assert historique[1].prompt == "Test 2"

def test_compter_requetes():
    enregistrer_requete(prompt="Test 1", statut="success")
    enregistrer_requete(prompt="Test 2", statut="success")
    enregistrer_requete(prompt="Test 3", statut="error")
    
    stats = compter_requetes()
    assert stats["total"] >= 3
    assert stats["success"] >= 2
    assert stats["errors"] >= 1
