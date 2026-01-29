from pathlib import Path

import pytest

from src.settings import find_first_toml


def test_find_first_toml_dir_not_exists() -> None:
    with pytest.raises(FileNotFoundError):
        find_first_toml(search_dir=Path("invalid"))


@pytest.mark.parametrize(
    ("search_dir", "patterns"),
    [
        (Path("config"), ["*.invalid"]),
        (Path("tmp_dir"), None),
    ],
)
def test_find_first_toml_no_toml_files(
    search_dir: Path, patterns: list[str], tmp_path_factory: pytest.TempPathFactory
) -> None:
    if not search_dir.exists():
        search_dir = tmp_path_factory.mktemp(search_dir.name)
    with pytest.raises(FileNotFoundError):
        find_first_toml(search_dir, patterns)


def test_find_first_toml() -> None:
    toml_file = find_first_toml(search_dir=Path("config"))
    assert toml_file.is_file()
    assert toml_file.name.endswith(".toml"), "Found file is not a TOML file"
