from pathlib import Path

from pydantic import BaseModel, ConfigDict
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

DEFAULT_CONFIG_DIR = Path.home() / ".ticket2pr"


def find_first_toml(search_dir: Path, patterns: list[str] | None = None) -> Path:
    """Search for the first TOML file in the specified directory.

    Args:
        search_dir (Path): The directory to search for TOML files.
        patterns (list[str], optional): List of glob patterns to match files,
        Defaults to ["*.toml"].

    Returns:
        Path: The path to the first TOML file found.

    Raises:
        `FileNotFoundError`: If the directory does not exist or no matching TOML file is found.

    """
    if patterns is None:
        patterns = ["*.toml"]

    if not search_dir.exists():
        msg = f"Config directory '{search_dir}' does not exist."
        raise FileNotFoundError(msg)

    for pattern in patterns:
        for toml_path in search_dir.glob(pattern):
            if toml_path.is_file():
                return toml_path
    msg = f"No TOML file found in {search_dir} matching {patterns}"
    raise FileNotFoundError(msg)


class LoggingSettings(BaseModel):
    min_log_level: str = "INFO"
    log_file_path: Path = Path("ticket2pr.log")

    model_config = ConfigDict(extra="forbid")


class AppCoreSettings(BaseModel):
    workspace_path: Path
    base_branch: str

    model_config = ConfigDict(extra="forbid")


class JiraSettings(BaseModel):
    base_url: str
    username: str
    api_token: str

    model_config = ConfigDict(extra="forbid")


class GitHubSettings(BaseModel):
    api_token: str
    repo_full_name: str

    model_config = ConfigDict(extra="forbid")


class AppSettings(BaseSettings):
    """Application settings loaded from environment, `toml` file, and class initialization.

    Settings are loaded in the following order of precedence
    (as defined in `settings_customise_sources`):
    1. Initialization arguments (init settings)
    2. `toml` configuration file
    3. Environment variables (including `.env` file)

    NOTE: For deeply nested environment variables, use the `{SECTION}__{PROPERTY}`
    naming convention (e.g., `CORE__WORKSPACE_PATH`).
    The delimiter defined in `model_config.env_nested_delimiter`
    """

    core: AppCoreSettings
    logging: LoggingSettings = LoggingSettings()
    jira: JiraSettings
    github: GitHubSettings

    model_config = SettingsConfigDict(
        # env_file is kept for CWD support. Per Pydantic settings documentation, it only checks the
        # CWD and won't check parent directories. load_dotenv() is called in the entry point to
        # handle parent folders.
        env_file=".env",
        env_file_encoding="utf-8",
        # Important for deeply nested env vars.
        # Properties should be named as `{SECTION}__{PROPERTY}` in `.env`.
        # For example: `CORE__WORKSPACE_PATH`.
        env_nested_delimiter="__",
        extra="forbid",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        toml_file = find_first_toml(DEFAULT_CONFIG_DIR)
        # Customize the order of settings sources.(init > toml > env)
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=toml_file),
            env_settings,
        )
