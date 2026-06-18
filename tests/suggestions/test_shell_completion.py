from niyam.suggestions.shell import generate_completion_script, install_completion_script

def test_generate_completion_script():
    bash_script = generate_completion_script("bash")
    assert "complete -F _niyam_completion niyam" in bash_script
    
    zsh_script = generate_completion_script("zsh")
    assert "compdef _niyam_completion niyam" in zsh_script
    
    fish_script = generate_completion_script("fish")
    assert "complete -c niyam" in fish_script
    
    ps_script = generate_completion_script("powershell")
    assert "Register-ArgumentCompleter" in ps_script

def test_install_completion_script(monkeypatch, tmp_path):
    monkeypatch.setattr("niyam.suggestions.shell.Path.home", lambda: tmp_path)
    
    # Test bash installation
    install_completion_script("bash")
    bashrc = tmp_path / ".bash_profile"  # since .bashrc doesn't exist
    assert bashrc.exists()
    assert "niyam completion script" in bashrc.read_text()
    
    # Test zsh installation
    install_completion_script("zsh")
    zshrc = tmp_path / ".zshrc"
    assert zshrc.exists()
    assert "niyam completion script" in zshrc.read_text()
