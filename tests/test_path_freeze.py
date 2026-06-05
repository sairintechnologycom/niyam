import stat
from pathlib import Path
from niyam.mission.executor import apply_path_freeze, restore_path_freeze


def test_apply_and_restore_path_freeze(tmp_path: Path):
    # Setup test workspace
    frozen_dir = tmp_path / "frozen_dir"
    frozen_dir.mkdir()
    frozen_file = frozen_dir / "frozen.txt"
    frozen_file.write_text("frozen content", encoding="utf-8")

    normal_file = tmp_path / "normal.txt"
    normal_file.write_text("normal content", encoding="utf-8")

    # Relative paths to freeze
    frozen_paths = ["frozen_dir"]

    # Apply freeze
    original_modes = apply_path_freeze(frozen_paths, tmp_path)

    # Assert S_IWRITE flag was removed
    assert (frozen_file.stat().st_mode & stat.S_IWRITE) == 0

    # Restore freeze
    restore_path_freeze(original_modes)

    # Check that permissions are restored and file is writable again
    assert (frozen_file.stat().st_mode & stat.S_IWRITE) != 0
    with open(frozen_file, "w", encoding="utf-8") as f:
        f.write("restored write")
    assert frozen_file.read_text(encoding="utf-8") == "restored write"
