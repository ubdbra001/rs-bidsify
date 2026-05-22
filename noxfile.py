from nox import Session, options
from nox_uv import session

options.default_venv_backend = "uv"

@session(
    python=["3.12", "3.13", "3.14"],
    uv_groups=["test"],
)
def test(s: Session) -> None:
    s.run("python", "-m", "pytest")

@session(uv_groups=["type_check"], uv_extras=["cli"])
def type_check(s: Session) -> None:
    s.run("pyright", "src")

@session(uv_only_groups=["lint"])
def lint(s: Session) -> None:
    s.run("ruff", "check", ".")
    s.run("ruff", "format", "--check", ".")