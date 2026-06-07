import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from niyam.core.cost import load_pricing, get_pricing_path

def test_load_pricing_remote_fetch(tmp_path):
    """Should fetch pricing from remote URL and update local cache."""
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    niyam_yaml = niyam_dir / "niyam.yaml"
    pricing_url = "https://api.example.com/pricing.json"
    
    # Setup niyam.yaml with pricing_url
    config_content = f"""
version: "0.1.0"
saas:
  pricing_url: "{pricing_url}"
"""
    niyam_yaml.write_text(config_content)
    
    # Mock remote data
    remote_pricing = {
        "claude-super": {"input_cost_per_million": 100.0, "output_cost_per_million": 500.0}
    }
    
    with patch("niyam.core.config.find_niyam_root", return_value=tmp_path):
        with patch("urllib.request.urlopen") as mock_urlopen:
            # Mock response
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(remote_pricing).encode("utf-8")
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            # Load pricing
            pricing = load_pricing(root=tmp_path)
            
            # Verify fetch was called
            mock_urlopen.assert_called_once_with(pricing_url, timeout=5)
            
            # Verify pricing is updated
            assert "claude-super" in pricing
            assert pricing["claude-super"]["input_cost_per_million"] == 100.0
            
            # Verify local cache was updated
            pricing_path = get_pricing_path(tmp_path)
            assert pricing_path.exists()
            cached_data = json.loads(pricing_path.read_text())
            assert "claude-super" in cached_data

def test_load_pricing_fetch_failure_fallback(tmp_path):
    """Should fallback to local pricing if remote fetch fails."""
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir(exist_ok=True)
    niyam_yaml = niyam_dir / "niyam.yaml"
    pricing_url = "https://api.example.com/pricing.json"
    
    # Setup local pricing
    local_pricing = {"local-model": {"input_cost_per_million": 1.0, "output_cost_per_million": 2.0}}
    pricing_path = get_pricing_path(tmp_path)
    pricing_path.parent.mkdir(parents=True, exist_ok=True)
    pricing_path.write_text(json.dumps(local_pricing))
    
    # Setup niyam.yaml with pricing_url
    config_content = f"""
version: "0.1.0"
saas:
  pricing_url: "{pricing_url}"
"""
    niyam_yaml.write_text(config_content)
    
    with patch("niyam.core.config.find_niyam_root", return_value=tmp_path):
        with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
            # Load pricing
            pricing = load_pricing(root=tmp_path)
            
            # Verify pricing falls back to local
            assert "local-model" in pricing
            assert "claude-super" not in pricing
