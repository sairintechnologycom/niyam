from pathlib import Path

BASH_COMPLETION = """
_niyam_completion() {
    local cur
    cur="${COMP_WORDS[*]:1}"
    COMPREPLY=( $(niyam suggest "$cur" 2>/dev/null) )
}
complete -F _niyam_completion niyam
"""

ZSH_COMPLETION = """
#compdef niyam
_niyam_completion() {
    local -a completions
    local cur
    cur=${words[2,-1]}
    completions=("${(@f)$(niyam suggest "$cur" 2>/dev/null)}")
    compadd -a completions
}
compdef _niyam_completion niyam
"""

FISH_COMPLETION = """
function _niyam_completion
    set -l cmd (commandline -cp)
    set -l niyam_cmd (string replace -r '^niyam ' '' -- $cmd)
    niyam suggest "$niyam_cmd"
end
complete -c niyam -f -a "(_niyam_completion)"
"""

POWERSHELL_COMPLETION = """
Register-ArgumentCompleter -Native -CommandName niyam -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    $cmd = $commandAst.ToString() -replace '^niyam ?', ''
    niyam suggest "$cmd" | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }
}
"""

def generate_completion_script(shell: str) -> str:
    shell = shell.lower()
    if shell == "bash":
        return BASH_COMPLETION
    elif shell == "zsh":
        return ZSH_COMPLETION
    elif shell == "fish":
        return FISH_COMPLETION
    elif shell == "powershell":
        return POWERSHELL_COMPLETION
    else:
        # Fallback to bash
        return BASH_COMPLETION

def install_completion_script(shell: str) -> None:
    shell = shell.lower()
    home = Path.home()
    if shell == "bash":
        rc_file = home / ".bashrc"
        if not rc_file.exists():
            rc_file = home / ".bash_profile"
        script = '\n# Niyam autocomplete\neval "$(niyam completion script --shell bash)"\n'
        with open(rc_file, "a", encoding="utf-8") as f:
            f.write(script)
    elif shell == "zsh":
        rc_file = home / ".zshrc"
        script = '\n# Niyam autocomplete\neval "$(niyam completion script --shell zsh)"\n'
        with open(rc_file, "a", encoding="utf-8") as f:
            f.write(script)
    elif shell == "fish":
        config_dir = home / ".config" / "fish" / "completions"
        config_dir.mkdir(parents=True, exist_ok=True)
        completion_file = config_dir / "niyam.fish"
        with open(completion_file, "w", encoding="utf-8") as f:
            f.write(FISH_COMPLETION)
    elif shell == "powershell":
        # Usually profile is in Documents/PowerShell/Microsoft.PowerShell_profile.ps1
        import platform
        if platform.system() == "Windows":
            profile_dir = home / "Documents" / "PowerShell"
        else:
            profile_dir = home / ".config" / "powershell"
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profile_dir / "Microsoft.PowerShell_profile.ps1"
        script = '\n# Niyam autocomplete\nInvoke-Expression (& niyam completion script --shell powershell)\n'
        with open(profile_file, "a", encoding="utf-8") as f:
            f.write(script)
    else:
        raise ValueError(f"Unsupported shell: {shell}")

