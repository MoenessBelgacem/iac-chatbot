import pytest
from unittest.mock import patch, MagicMock
from backend.app.git_utils import commit_and_push

@patch("backend.app.git_utils.subprocess.run")
def test_commit_and_push_success(mock_run):
    """Teste que les commandes Git sont bien appelées dans l'ordre."""
    
    # Simuler le fait qu'il y a des changements à commiter (stdout ne contient pas nothing to commit)
    mock_run.return_value = MagicMock(stdout=b"1 file changed")
    
    result = commit_and_push(["/path/to/generated/main.tf"], "Test commit")
    
    assert result is True
    assert mock_run.call_count == 4 # pull, add, commit, push
    
    calls = mock_run.call_args_list
    assert calls[0][0][0] == ["git", "pull", "--rebase", "origin", "main"]
    assert calls[1][0][0] == ["git", "add", "/path/to/generated/main.tf"]
    assert calls[2][0][0] == ["git", "commit", "-m", "Test commit"]
    assert calls[3][0][0] == ["git", "push", "origin", "main"]

@patch("backend.app.git_utils.subprocess.run")
def test_commit_and_push_nothing_to_commit(mock_run):
    """Teste le cas où git indique qu'il n'y a rien à commiter."""
    
    def side_effect(*args, **kwargs):
        mock_result = MagicMock()
        if "commit" in args[0]:
            mock_result.stdout = b"nothing to commit, working tree clean"
        else:
            mock_result.stdout = b"ok"
        return mock_result
        
    mock_run.side_effect = side_effect
    
    result = commit_and_push(["/fake/file"], "Test")
    
    assert result is True
    # Ne doit pas appeler 'push' car on a intercepté le nothing to commit
    assert mock_run.call_count == 3 

@patch("backend.app.git_utils.subprocess.run")
def test_commit_and_push_error(mock_run):
    """Teste le comportement en cas d'échec du subprocess (ex: réseau coupé)."""
    import subprocess
    
    # On fait échouer le "add" par exemple
    def side_effect(*args, **kwargs):
        if "add" in args[0]:
            raise subprocess.CalledProcessError(1, cmd="git add", stderr=b"fatal error")
        return MagicMock()
        
    mock_run.side_effect = side_effect
    
    result = commit_and_push(["/fake/file"], "Test")
    assert result is False
