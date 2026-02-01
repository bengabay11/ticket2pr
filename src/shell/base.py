import subprocess  # nosec B404: subprocess is required to run pre-commit tools
from pathlib import Path

from pydantic import BaseModel


class CommandResult(BaseModel):
    return_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.return_code == 0

    @property
    def output(self) -> str:
        return self.stdout + self.stderr


def run_command(args: list[str], cwd: Path | None = None) -> CommandResult:
    expanded_path = None
    if cwd:
        expanded_path = cwd.expanduser()

    result = subprocess.run(
        args,  # nosec B603: pre_commit_executable is resolved via shutil.which and is trusted
        cwd=expanded_path,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        return_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
