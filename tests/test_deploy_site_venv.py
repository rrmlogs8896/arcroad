"""deploy_site.sh uses ~/.venvs/arcroad without a "source" step, and still says what is missing.

Backlog 1: the deploy ran the system python3 and stopped with "Needs ruff and pytest" when the
tools lived only in the venv. These run the script with a fake venv, a fake npx and an empty
repo copy, so nothing is linted for real and nothing is ever deployed.
"""
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "deploy_site.sh"


def fake_python(path, log, has_tools):
    path.parent.mkdir(parents=True)
    fail = "" if has_tools else 'case "$2" in ruff|pytest) exit 1;; esac\n'
    path.write_text(f'#!/bin/bash\necho "venv $*" >> "{log}"\n{fail}exit 0\n')
    path.chmod(0o755)


def run(tmp_path, venv_exists, has_tools=True):
    log = tmp_path / "calls.log"
    log.write_text("")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    npx = bindir / "npx"
    npx.write_text(f'#!/bin/bash\necho "npx $*" >> "{log}"\n')
    npx.chmod(0o755)
    # system python3 with no tools, so falling back to it is visible
    syspy = bindir / "python3"
    syspy.write_text(f'#!/bin/bash\necho "system $*" >> "{log}"\nexit 1\n')
    syspy.chmod(0o755)
    venv = tmp_path / "venv"
    if venv_exists:
        fake_python(venv / "bin" / "python3", log, has_tools)
    env = {**os.environ, "ARCROAD_VENV": str(venv), "PATH": f"{bindir}:/usr/bin:/bin"}
    r = subprocess.run(["/bin/bash", str(SCRIPT)], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    return r, log.read_text()


def test_deploy_uses_venv_python_when_it_exists(tmp_path):
    r, calls = run(tmp_path, venv_exists=True)
    assert r.returncode == 0, r.stderr
    assert "system" not in calls
    assert "venv -m ruff check pipeline tests" in calls
    assert "venv -m pytest -q" in calls
    assert "npx wrangler pages deploy web" in calls


def test_deploy_falls_back_to_system_python_without_venv(tmp_path):
    r, calls = run(tmp_path, venv_exists=False)
    assert r.returncode == 1
    assert "system -m ruff --version" in calls
    assert "Needs the project venv" in r.stdout and "~/.venvs/arcroad" in r.stdout


def test_deploy_still_explains_missing_tools_in_venv_and_never_deploys(tmp_path):
    r, calls = run(tmp_path, venv_exists=True, has_tools=False)
    assert r.returncode == 1
    assert "Needs the project venv" in r.stdout and "~/.venvs/arcroad" in r.stdout
    assert "npx" not in calls


def test_script_is_present():
    assert shutil.which("bash") and SCRIPT.exists()
