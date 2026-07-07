"""Tests pour le module de stacks prédéfinies."""

from backend.app.stacks import detecter_stack, obtenir_stack, lister_stacks


def test_detecter_stack_wordpress():
    """Teste la détection de la stack WordPress."""
    assert detecter_stack("Déploie une stack WordPress") == "wordpress"
    assert detecter_stack("deploy wordpress") == "wordpress"


def test_detecter_stack_lamp():
    """Teste la détection de la stack LAMP."""
    assert detecter_stack("Crée une stack LAMP") == "lamp"


def test_detecter_stack_monitoring():
    """Teste la détection de la stack Monitoring."""
    assert detecter_stack("Déploie une stack monitoring") == "monitoring"
    assert detecter_stack("Installe Prometheus et Grafana") == "monitoring"


def test_detecter_stack_elk():
    """Teste la détection de la stack ELK."""
    assert detecter_stack("Déploie une stack ELK") == "elk"


def test_detecter_stack_aucune():
    """Teste qu'une requête normale ne déclenche pas de stack."""
    assert detecter_stack("Je veux une VM Ubuntu sur vSphere") is None
    assert detecter_stack("Bonjour comment ça va ?") is None


def test_obtenir_stack_existante():
    """Teste la récupération d'une stack existante."""
    stack = obtenir_stack("wordpress")
    assert stack is not None
    assert stack["name"] == "WordPress Stack"
    assert len(stack["resources"]) == 2


def test_obtenir_stack_inexistante():
    """Teste la récupération d'une stack qui n'existe pas."""
    assert obtenir_stack("inexistante") is None


def test_lister_stacks():
    """Teste le listing de toutes les stacks."""
    stacks = lister_stacks()
    assert len(stacks) >= 5
    noms = [s["id"] for s in stacks]
    assert "wordpress" in noms
    assert "lamp" in noms
    assert "monitoring" in noms
    assert "elk" in noms
    assert "cache" in noms
