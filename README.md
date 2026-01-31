# Python Template

This project offers a robust, ready-to-use boilerplate, designed to kickstart your new Python projects with confidence. It comes packed with pre-configured best practices and essential tools, letting you dive straight into development.

---

## What's Included

We've bundled the following to get you up and running quickly:

- **⚡️ Speedy Package Management:** Utilizes [uv](https://docs.astral.sh/uv/) for incredibly fast dependency resolution and package installation.
- **✅ Strict Type-Checking:** Enforces code quality with [mypy](https://www.mypy-lang.org/) for robust static type analysis, catching errors early.
- **✨ Blazing-Fast Linting & Formatting:** Leverages [ruff](https://docs.astral.sh/ruff/) for an all-in-one, high-performance linter, code formatter, and more.
- **🚫 Automated Quality Checks:** Integrates [pre-commit](https://pre-commit.com/) hooks for `ruff`, `mypy`, `codespell`, `absolufy-imports`, `uv lock`, and other essential checks, ensuring code consistency before commits.
- **💻 VS Code Integration:** Includes [settings.json](.vscode/settings.json) and [launch.json](.vscode/launch.json) for streamlined development, with editor configurations and debug settings right out of the box.
- **🤖 GitHub Actions Workflow:** Provides automated `pre-commit` checks, unit, and integration testing (on windows/linux/mac).
- **🐳 Container Image Publishing:** Provides a ready-made `Dockerfile` and workflow that builds on every pull request
  and publishes versioned GHCR images when the PR targets `master`.
- **🔗 Git Attributes:** Standardizes [.gitattributes](.gitattributes) for consistent line endings, optimized diffs, and common Git configurations tailored for Python projects.
- **📁 Structured Source Directory:** A clear [src/](src/) directory where your application code resides, complete with an example [main.py](src/main.py) to get you started.
- **⚙️ Flexible Settings System:** Includes a modern, sectioned configuration system powered by Pydantic, supporting TOML, .env, and environment variables, with auto-discovery and type-safe validation (see [settings.py](src/settings.py)).
- **🌈 Enhanced Terminal Logging:** Configured with [colorlog](https://pypi.org/project/colorlog/) to provide highly readable, colored log output directly in your terminal, making debugging a breeze.
- **📄 Standard Project Files:** Includes a [LICENSE](LICENSE) and this [README.md](README.md) for proper project documentation and licensing.

---

## Getting Started

Follow these steps to set up your new project:

### Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher** installed on your system.
- **[uv](https://github.com/astral-sh/uv)**, our recommended tool for dependency management.

### Usage

1. **Clone the Template:**

   ```sh
   git clone https://github.com/bengabay11/python-template.git
   ```

2. **Setup virtual environment:**
   Automatically download the correct Python version, create a virtual environment (`.venv`), and install all dependencies using `uv`:

   ```sh
   uv sync
   ```

3. **Install Pre-Commit Hooks:**
   Set up the pre-commit hooks to automate code quality checks before each commit:

   ```sh
   pre-commit install
   ```

4. **Start Developing:**
   Begin building your awesome Python project within the `src/` directory.

5. **Running:**
   Test your setup by running the entry point:

   ```sh
   python -m src.main
   ```

   Or running the same file using uv:

   ```sh
   uv run -m src.main
   ```

   Alternatively, you can use the pre-configured VS Code debug settings in [launch.json](.vscode/launch.json) for a seamless debugging experience.

---

## Customization

This template is designed to be flexible. Here's how you can tailor it to your needs:

- **Add Your Modules:** Create and organize your application's modules within the `src/` directory.
- **Manage Dependencies:** Update `pyproject.toml` to add or remove project dependencies and adjust metadata.
- **Configure Tools:** Fine-tune `mypy.ini` and `ruff.toml` to align with your specific coding style and static analysis requirements.

---

## Docker Image

Use the provided `Dockerfile` to containerize your application.
The accompanying GitHub Actions workflow builds this image for every pull request.
If the pull request targets `master`, it also publishes the image to [GHCR](https://github.com/features/packages).

- Master pull requests publish tags `latest` and `v<run_number>` (for example, `v1`).
- Images are stored under your repository's namespace, such as `ghcr.io/<OWNER>/<REPO>`.

To build and run the image locally:

```sh
docker build -t ghcr.io/OWNER/REPO:local .
docker run --rm ghcr.io/OWNER/REPO:local
```

---

## Settings

This template features a modern configuration system using [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (see [settings.py](src/settings.py)).

- **Multi-source loading:** Settings are loaded in the following order of precedence:
  1. Direct class initialization
  2. TOML config file (e.g., [config/config.example.toml](config/config.example.toml))
  3. environment variables (including `.env`).

- **Sectioned & Nested:** Settings are organized into logical sections (e.g., `core`, `logging`) for clarity and scalability. Deeply nested environment variables are supported using the `SECTION__PROPERTY` naming convention (e.g., `CORE__APP_NAME`).
- **Auto-discovery:** The config system can automatically find the first TOML file in your [config/](config) directory, making it easy to switch environments or configurations.
- **Type-safe:** All settings are validated and parsed using Pydantic models, ensuring type safety and clear error messages.

Example usage:

```python
from src.settings import settings
print(settings.core.app_name)
print(settings.logging.min_log_level)
```

---

## Logging

Logging is handled via a flexible, colorized, and extensible system (see [logging_setup.py](src/logging_setup.py)).

- **Colorful output:** Uses [colorlog](https://pypi.org/project/colorlog/) for beautiful, readable terminal logs.
- **Configurable handlers:** Supports both stream and file handlers, with easy configuration via settings.
- **Validation:** Log level and handler configuration are validated using Pydantic, with clear error messages for misconfiguration.
- **Extensible:** The handler system is built on an abstract base class, making it easy to add new handler types if needed.

Example usage:

```python
from src.logging_setup import setup_logger, SetupLoggerParams, LoggerHandlerType
from src.settings import settings

setup_logger(
    SetupLoggerParams(
        level=settings.logging.min_log_level,
        handler_types={LoggerHandlerType.STREAM},
        file_path=settings.logging.log_file_path,
    )
)
```

---

## License

This project is open-sourced under the terms of the [LICENSE](LICENSE).
