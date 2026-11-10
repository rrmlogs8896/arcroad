"""The research container installs every third-party module its jobs import.

4 Nov 2026 night run: the bengaluru job failed at once with "No module named 'shapely'",
after the other jobs had used most of the night. This checks the Dockerfile's pip line
against the imports of the code the container runs, so a missing module fails in CI.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STDLIB_OR_LOCAL = {"pipeline", "__future__"}
PIP_NAME = {"osmium": "osmium", "numpy": "numpy", "pandas": "pandas", "scipy": "scipy",
            "tabulate": "tabulate", "rasterio": "rasterio", "shapely": "shapely"}


def third_party_imports(paths):
    import sys
    std = set(sys.stdlib_module_names)
    found = set()
    for p in paths:
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) and node.module and node.level == 0 else []
            for n in names:
                top = n.split(".")[0]
                if top not in std and top not in STDLIB_OR_LOCAL:
                    found.add(top)
    return found


def test_container_installs_every_module_the_jobs_import():
    pip = re.search(r"RUN pip install[^\n]*", (ROOT / "research" / "runner" / "Dockerfile").read_text()).group(0)
    app = ROOT / "research" / "runner" / "app"
    local = {p.stem for p in app.glob("*.py")} | {p.stem for p in (ROOT / "tools").glob("*.py")}
    code = list(app.glob("*.py")) + list((ROOT / "pipeline").glob("*.py")) + [ROOT / "tools" / "multicity_collect.py"]
    missing = [m for m in sorted(third_party_imports(code) - local) if PIP_NAME.get(m, m) not in pip]
    assert not missing, missing


def test_container_does_not_install_packages_no_job_imports():
    """Image-size fix (backlog 2): pandas and tabulate were installed but nothing the runner runs imports them,
    and they pushed the pip layer to about 138 MB, which made Cloudflare pushes time out."""
    pip = re.search(r"RUN pip install[^\n]*", (ROOT / "research" / "runner" / "Dockerfile").read_text()).group(0)
    installed = set(re.findall(r'"([A-Za-z0-9_.-]+)\s*[><=~!]', pip))
    app = ROOT / "research" / "runner" / "app"
    local = {p.stem for p in app.glob("*.py")} | {p.stem for p in (ROOT / "tools").glob("*.py")}
    code = list(app.glob("*.py")) + list((ROOT / "pipeline").glob("*.py")) + [ROOT / "tools" / "multicity_collect.py"]
    imported = third_party_imports(code) - local
    unused = sorted(i for i in installed if i not in {PIP_NAME.get(m, m) for m in imported})
    assert installed and not unused, unused


def test_remote_runs_after_the_jobs_it_reads():
    src = (ROOT / "research" / "runner" / "app" / "server.py").read_text()
    order = re.findall(r'\("(\w+)", job_', src[src.index("JOBS = ["):])
    assert order.index("remote") > order.index("routercheck") and order.index("remote") > order.index("mapwatch")
