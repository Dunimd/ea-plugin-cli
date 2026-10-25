#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2025-2026 Wenze Wei. All Rights Reserved.
#
# This file is part of Encre Agent.
# The Encre Agent project belongs to the Dunimd Team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# DISCLAIMER: Users must comply with applicable AI regulations.
# Non-compliance may result in service termination or legal liability.

from __future__ import annotations

"""encre-plugin — the Encre Agent plugin market unified CLI.

Commands:
    init <name>        Scaffold an ea-plugin-* package directory
    sdk [--out DIR]    Materialise the plugin UI SDK package
    build [pkg_dir]    Frontend compile + policy-check + wheel/sdist + digests
    verify [pkg_dir]   Isolated install + entry-point smoke test
    publish [pkg_dir]  PyPI upload + registry PR
    catalog regen|check  Rebuild or validate catalog.json

Build info (``dist/ea-build-info.json``) is the handoff between stages:
it carries the catalog entry with per-artifact sha256 digests so the
registry CI and the market installer never have to re-hash by hand.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC
from pathlib import Path
from typing import Any

from .rules import (
    PACKAGE_PREFIX,
    RESERVED_PREFIXES,
    VENDOR_TIERS,
    build_catalog_entry,
    find_ea_entrypoint,
    merge_catalog,
    normalize_module,
    read_pyproject,
    sha256_file,
    validate_for_publish,
)

BUILD_INFO = "ea-build-info.json"

_PROBE = """
import importlib, json, sys
module_name, _, factory = sys.argv[1].partition(":")
plugin = getattr(importlib.import_module(module_name), factory)()
print(json.dumps(plugin.manifest.to_dict()))
"""


def _fail(msg: str, code: int = 1) -> None:
    """Print an error message to stderr and exit with the given code."""
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def _host_python() -> str:
    """Resolve the Python interpreter the CLI shells out to for build/verify/publish.

    A PyInstaller-frozen executable is not itself a Python interpreter, so
    the compiled ``encre-plugin`` binary searches PATH for a real Python
    >= 3.11.  An unfrozen run (dev environments with editable installs or
    project venvs) keeps ``sys.executable`` unchanged.
    """
    if not getattr(sys, "frozen", False):
        return sys.executable
    probe = "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
    for name in ("python", "python3", "py"):
        cand = shutil.which(name)
        if cand and subprocess.run([cand, "-c", probe], capture_output=True).returncode == 0:
            return cand
    _fail("no Python 3.11+ interpreter found on PATH — the downloaded encre-plugin shells out to a real Python for build/verify/publish")
    return ""  # unreachable; _fail raises


def _ensure_pytools(py: str, *mods: str) -> None:
    """Install missing PyPA helper modules into the host interpreter on first use.

    The download-and-run promise: nobody pip-installs a toolchain before
    using the exe, so a missing helper (build / twine) is installed into
    the host interpreter silently when absent.  ``--user`` is tried first;
    if refused (inside a venv) it falls back to a plain install.
    """
    missing = [m for m in mods if subprocess.run([py, "-c", f"import {m}"], capture_output=True).returncode != 0]
    if not missing:
        return
    print(f"one-time setup: installing {', '.join(missing)} for the publishing toolchain ...")
    r = _run([py, "-m", "pip", "install", "--quiet", "--user", *missing])
    if r.returncode != 0:
        # --user is refused inside venvs; fall back to a plain install.
        r = _run([py, "-m", "pip", "install", "--quiet", *missing])
    if r.returncode != 0:
        _fail(
            f"could not install {', '.join(missing)} into {py} — install manually:\n  {py} -m pip install {' '.join(missing)}\n{r.stderr}"
        )


def _run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess, capturing stdout/stderr without raising on failure."""
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False, env=env)


def _load_manifest(pkg_dir: Path) -> dict[str, Any]:
    """Run the package's entry-point factory in a subprocess and return its manifest dict.

    The frozen CLI exe has no ``encre`` importable inside it, so the
    factory is invoked as a subprocess against the host interpreter.
    The market never imports plugin code this way — it reads the catalog
    entry baked at build time instead.
    """
    py = read_pyproject(pkg_dir)
    ep = find_ea_entrypoint(py)
    if ep is None:
        _fail('no [project.entry-points."ea.plugins"] entry found')
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(pkg_dir), os.environ.get("PYTHONPATH")]))}
    r = subprocess.run([_host_python(), "-c", _PROBE, ep[1]], cwd=str(pkg_dir), env=env, text=True, capture_output=True)
    if r.returncode != 0:
        _fail(f"loading plugin factory {ep[1]!r} failed:\n{r.stderr}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        _fail(f"factory {ep[1]!r} printed non-JSON: {r.stdout[:200]!r} ({exc})")
        return {}  # unreachable


# ── plugin UI SDK / frontend compilation ─────────────────────────────

UI_SOURCES = ("ui/src/index.ts", "ui/src/index.tsx", "ui/src/index.js", "ui/src/index.mjs")
UI_OUTPUT = "ui/plugin.js"
UI_INLINE_MAX = 512 * 1024
_UI_ROW_TYPES = {"toggle", "select", "text", "number", "textarea", "color", "button"}


def _sdk_dir() -> Path:
    """Locate the embedded SDK distribution (source checkout or frozen exe)."""
    here = Path(__file__).resolve().parent
    candidates = [here / "sdk_dist"]
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.insert(0, Path(sys._MEIPASS) / "ea_plugin_cli" / "sdk_dist")  # type: ignore[attr-defined]
    candidates.append(Path(__file__).resolve().parents[2] / "sdk" / "dist")
    for cand in candidates:
        if (cand / "contract.json").is_file():
            return cand
    _fail("plugin UI SDK is missing (sdk_dist/contract.json not found); reinstall ea-plugin-cli")
    return Path()  # unreachable


def _ui_contract() -> dict[str, Any]:
    try:
        return json.loads((_sdk_dir() / "contract.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"cannot read plugin UI contract: {exc}")
        return {}


def _esbuild_cmd(pkg_dir: Path) -> list[str]:
    """Resolve an esbuild invocation without requiring a pinned install."""
    env_bin = os.environ.get("ENCRE_ESBUILD")
    if env_bin and Path(env_bin).is_file():
        return [env_bin]
    on_path = shutil.which("esbuild")
    if on_path:
        return [on_path]
    repo = Path(__file__).resolve().parents[2]
    names = ("esbuild.cmd", "esbuild") if os.name == "nt" else ("esbuild",)
    for root in (pkg_dir / "node_modules/.bin", repo / "desktop/node_modules/.bin"):
        for name in names:
            cand = root / name
            if cand.is_file():
                return [str(cand)]
    npx = shutil.which("npx")
    if npx:
        if os.name == "nt" and npx.lower().endswith((".cmd", ".bat")):
            return [os.environ.get("COMSPEC", "cmd.exe"), "/c", npx, "--yes", "esbuild@0.28.0"]
        return [npx, "--yes", "esbuild@0.28.0"]
    _fail("esbuild not found — install it (`npm i -D esbuild`) or set ENCRE_ESBUILD")
    return []  # unreachable


def _validate_ui_contract(pkg_dir: Path, source: Path, output: Path) -> dict[str, Any]:
    """Check plugin UI code against the host's single contract.

    Unknown `ea-ui-*` classes, RPC names and slot ids fail the build: shipping
    a typo produces an unstyled or dead control at runtime, which is exactly
    the failure this SDK is meant to prevent.
    """
    contract = _ui_contract()
    classes = set((contract.get("classes") or {}).keys())
    modules = set(contract.get("modules") or [])
    rpc = set(contract.get("rpc") or [])
    slots = set((contract.get("slots") or {}).values())
    text = source.read_text(encoding="utf-8", errors="replace") + "\n" + output.read_text(encoding="utf-8", errors="replace")

    used_classes = set(re.findall(r"\bea-ui-[a-z0-9-]+", text))
    unknown_classes = sorted(used_classes - classes - modules)
    if unknown_classes:
        _fail(
            "unknown plugin UI class(es): " + ", ".join(unknown_classes)
            + "\n  these names are not in the host contract; use EA_UI_CLASS_MAP / EA_UI_MODULE_NAMES"
        )

    # Only dotted names are checked: plain `call("myAction")` is plugin code,
    # not an EA-UI RPC.
    used_rpc = set(re.findall(r"\bcall\s*\(\s*[\"']([a-z0-9-]+\.[a-z0-9-]+)[\"']", text))
    unknown_rpc = sorted(used_rpc - rpc)
    if unknown_rpc:
        _fail("unknown EA-UI RPC method(s): " + ", ".join(unknown_rpc) + "\n  see EA_UI_RPC_NAMES")

    used_slots = set(re.findall(r"\bsetSlot\s*\(\s*[\"']([a-z0-9_.-]+)[\"']", text))
    used_slots |= set(re.findall(r"\bslot\s*:\s*[\"']([a-z0-9_.-]+)[\"']", text))
    unknown_slots = sorted(used_slots - slots)
    if unknown_slots:
        _fail("unknown plugin slot id(s): " + ", ".join(unknown_slots) + "\n  see PLUGIN_SLOTS")
    return {
        "classes": sorted(used_classes),
        "rpc": sorted(used_rpc),
        "slots": sorted(used_slots),
    }


def _module_dir(pkg_dir: Path) -> Path:
    """Locate the Python package directory that owns `ui/` assets."""
    try:
        py = read_pyproject(pkg_dir)
    except SystemExit:
        py = {}
    except Exception:
        py = {}
    name = normalize_module(str((py.get("project") or {}).get("name", "")))
    cand = pkg_dir / name
    if name and cand.is_dir():
        return cand
    for found in pkg_dir.glob("*/ui"):
        if found.is_dir():
            return found.parent
    for found in pkg_dir.glob("*/ui/src/index.*"):
        return found.parent.parent
    return pkg_dir


def _resolve_ui_asset(pkg_dir: Path, rel: str) -> Path | None:
    """Resolve a manifest UI path against the module dir first, then project root."""
    for base in (_module_dir(pkg_dir), pkg_dir):
        target = (base / rel).resolve()
        if target.is_file():
            return target
    return None


def _build_frontend(pkg_dir: Path) -> dict[str, Any] | None:
    """Compile `ui/src/index.*` into the prebuilt `ui/plugin.js` asset.

    The install side never runs a build; this is the only place plugin
    frontend code is compiled.
    """
    module_dir = _module_dir(pkg_dir)
    source = next((module_dir / rel for rel in UI_SOURCES if (module_dir / rel).is_file()), None)
    if source is None:
        return None
    output = module_dir / UI_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = _esbuild_cmd(pkg_dir) + [
        str(source),
        "--bundle",
        "--format=iife",
        "--platform=browser",
        "--target=es2020",
        "--legal-comments=none",
        f"--outfile={output}",
    ]
    r = _run(cmd, cwd=pkg_dir)
    if r.returncode != 0:
        _fail(f"plugin frontend build failed:\n{r.stdout}\n{r.stderr}")
    if not output.is_file() or output.stat().st_size == 0:
        _fail("plugin frontend build produced no output")
    if output.stat().st_size > UI_INLINE_MAX:
        _fail(f"{UI_OUTPUT} is {output.stat().st_size} bytes; the runtime inline limit is {UI_INLINE_MAX}")
    report = _validate_ui_contract(pkg_dir, source, output)
    print(f"frontend: {source.relative_to(pkg_dir)} -> {output.relative_to(pkg_dir)} ({output.stat().st_size} bytes)")
    return {
        "source": str(source.relative_to(pkg_dir)),
        "output": str(output.relative_to(pkg_dir)),
        "bytes": output.stat().st_size,
        **report,
    }


def _validate_ui_references(manifest: dict[str, Any], pkg_dir: Path) -> None:
    """Validate the manifest's declarative UI entries before packaging."""
    contributes = manifest.get("contributes") if isinstance(manifest, dict) else None
    entries = (contributes or {}).get("ui_contributions") if isinstance(contributes, dict) else None
    if not entries:
        return
    if not isinstance(entries, list):
        _fail("contributes.ui_contributions must be a list")
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            _fail(f"ui_contributions[{idx}] must be an object")
        kind = str(entry.get("kind", "") or "")
        spec = entry.get("spec")
        if not kind or not isinstance(spec, dict):
            _fail(f"ui_contributions[{idx}] needs kind + object spec")
        if kind not in {"theme", "settings", "context_menu", "search_mode", "ui_override", "js_module"}:
            _fail(f"ui_contributions[{idx}] has unknown kind {kind!r}")
        if kind == "js_module":
            if spec.get("code"):
                continue
            rel = spec.get("path")
            if not isinstance(rel, str) or not rel:
                _fail(f"ui_contributions[{idx}] js_module needs path (or inline code)")
            if _resolve_ui_asset(pkg_dir, rel) is None:
                _fail(f"ui_contributions[{idx}] js_module path does not exist: {rel}")
        elif kind == "ui_override":
            if not spec.get("slot"):
                _fail(f"ui_contributions[{idx}] ui_override needs slot")
            if spec.get("template"):
                continue
            rel = spec.get("template_path")
            if not isinstance(rel, str) or not rel:
                _fail(f"ui_contributions[{idx}] ui_override needs template or template_path")
            if _resolve_ui_asset(pkg_dir, rel) is None:
                _fail(f"ui_contributions[{idx}] template_path does not exist: {rel}")
        elif kind == "settings":
            rows = spec.get("rows")
            if not isinstance(rows, list) or not rows:
                _fail(f"ui_contributions[{idx}] settings needs rows")
            for r_i, row in enumerate(rows):
                if not isinstance(row, dict) or not row.get("id") or not row.get("label"):
                    _fail(f"ui_contributions[{idx}].rows[{r_i}] needs id + label")
                if row.get("type") not in _UI_ROW_TYPES:
                    _fail(f"ui_contributions[{idx}].rows[{r_i}] has invalid type {row.get('type')!r}")
                if row.get("type") == "select" and not isinstance(row.get("options"), list):
                    _fail(f"ui_contributions[{idx}].rows[{r_i}] select needs options")
        elif kind == "theme":
            if not isinstance(spec.get("css"), str) or not spec.get("css").strip():
                _fail(f"ui_contributions[{idx}] theme needs non-empty css")
        elif kind == "context_menu":
            if not spec.get("label"):
                _fail(f"ui_contributions[{idx}] context_menu needs label")
        elif kind == "search_mode":
            if not spec.get("id") or not spec.get("label"):
                _fail(f"ui_contributions[{idx}] search_mode needs id + label")


def _ui_module_referenced(manifest: dict[str, Any], rel: str) -> bool:
    contributes = manifest.get("contributes") if isinstance(manifest, dict) else None
    entries = (contributes or {}).get("ui_contributions") if isinstance(contributes, dict) else None
    for entry in entries or []:
        if not isinstance(entry, dict) or entry.get("kind") != "js_module":
            continue
        spec = entry.get("spec") if isinstance(entry.get("spec"), dict) else {}
        if isinstance(spec.get("path"), str) and spec["path"].replace("\\", "/").lstrip("/") == rel:
            return True
    return False


def _verify_wheel_ui_assets(wheel: Path, manifest: dict[str, Any]) -> None:
    """Ensure every file-backed UI reference is actually inside the wheel."""
    contributes = manifest.get("contributes") if isinstance(manifest, dict) else None
    entries = (contributes or {}).get("ui_contributions") if isinstance(contributes, dict) else None
    if not entries:
        return
    with zipfile.ZipFile(wheel) as zf:
        names = set(zf.namelist())
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        spec = entry.get("spec") if isinstance(entry.get("spec"), dict) else {}
        rel = spec.get("path") if entry.get("kind") == "js_module" else spec.get("template_path")
        if not isinstance(rel, str) or not rel:
            continue
        wanted = rel.replace("\\", "/").lstrip("/")
        if not any(name == wanted or name.endswith("/" + wanted) for name in names):
            _fail(f"wheel is missing declared UI asset: {rel}")


# ── init ──────────────────────────────────────────────────────────────

_PYPROJECT_TMPL = """\
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{dist}"
version = "0.1.0"
description = "{title}"
readme = "README.md"
requires-python = ">=3.11"
authors = [{{ name = "Author", email = "author@example.com" }}]
license = {{ text = "Apache-2.0" }}
dependencies = ["encre-harness>=0.5.0"]

[project.entry-points."ea.plugins"]
{ep_name} = "{module}.plugin:create_plugin"

[tool.setuptools.packages.find]
where = ["."]
include = ["{module}*"]

[tool.setuptools.package-data]
{module} = ["ui/**/*", "skills/**/*"]
"""

_PLUGIN_PY = '''"""{title} — Encre Agent plugin."""

from __future__ import annotations

from encre.plugins.types import EncrePlugin, PluginManifest


class {cls}Plugin(EncrePlugin):
    manifest = PluginManifest(
        name="{name}",
        version="0.1.0",
        display_name="{title}",
        description="{title}",
        icon="",  # the plugin's own glyph: asset path, lucide name, or emoji
        author="Author",
        license="Apache-2.0",
        tags=["example"],
        tier="user",
        min_ea_version="0.5.0",
        permissions=["tools:register", "ui:register"],
        provides_tools=[],
        contributes={{
            "ui_contributions": [
                {{"kind": "js_module", "spec": {{"path": "ui/plugin.js"}}}},
            ]
        }},
    )

    def get_tools(self):
        return []


def create_plugin() -> {cls}Plugin:
    """Entry point factory (ea.plugins)."""
    return {cls}Plugin()
'''

_README_TMPL = """\
# {dist}

Encre Agent plugin `{name}`, built with `encre-plugin`.

- `encre-plugin build` — policy check + wheel/sdist + sha256 digests
- `encre-plugin verify` — isolated install smoke test
- `encre-plugin publish` — PyPI upload + registry PR

Frontend assets (if any) must be PREBUILT into `{module}/ui/` before
publishing; the installer never runs a build step.

- `{module}/ui/src/index.ts` — plugin UI source (SDK vendored beside it)
- `encre-plugin build` compiles it to `{module}/ui/plugin.js` and validates
  every `ea-ui-*` class / RPC name against the host contract
"""

_UI_ENTRY_TMPL = """\
import {{ definePluginUi }} from "../vendor/encre-plugin-ui-sdk/index.js";

// Runs inside the host's sandboxed worker. `render` replaces this plugin's
// own root; `actions.send()` reaches the plugin's backend handler.
definePluginUi({{
  render: () => `
    <div class="ea-ui-card" style="padding:12px;max-width:320px">
      <div class="ea-ui-row">
        <div class="ea-ui-row-info">
          <div class="ea-ui-row-title">{title}</div>
          <div class="ea-ui-row-desc">Rendered by the Encre plugin UI SDK.</div>
        </div>
        <span class="ea-ui-switch"><span class="ea-ui-switch-slider"></span></span>
      </div>
    </div>`,
}});
"""

_UI_README_TMPL = """\
# {title} UI

`src/index.ts` is compiled by `encre-plugin build` into `../plugin.js`.

- Import controls from `vendor/encre-plugin-ui-sdk/`.
- Use `ea-ui-*` classes; the SDK contract lists every valid name.
- Slots: `PLUGIN_SLOTS` (session.row, model.provider-row).
- Backend calls: `actions.send(kind, action, payload)`.
- Host capabilities: `call("dialog.confirm", ...)` (worker only for
  element-scoped RPCs; iframe providers get the safe subset).
"""


def cmd_init(args: argparse.Namespace) -> None:
    """Scaffold a new ea-plugin-* package directory with pyproject.toml, plugin.py, and README.

    The distribution name is auto-prefixed with ``ea-plugin-`` when the user
    omits it.  The module name is derived from the distribution name via
    PEP 508 normalisation.  Templates are string-substituted; no further
    code generation occurs.
    """
    name = args.name
    dist = name if name.startswith(PACKAGE_PREFIX) else f"{PACKAGE_PREFIX}{name}"
    module = normalize_module(dist)
    root = (Path(args.dir) if args.dir else Path.cwd()) / dist
    if root.exists():
        _fail(f"{root} already exists")
    title = name.replace("-", " ").strip().capitalize()
    cls = "".join(part.capitalize() for part in module.replace("_", " ").split() if part.isalnum()) or "Plugin"
    (root / module).mkdir(parents=True)
    (root / module / "ui").mkdir()
    (root / module / "ui" / ".gitkeep").write_text("", encoding="utf-8")
    (root / module / "ui" / "src").mkdir()
    (root / module / "ui" / "src" / "index.ts").write_text(_UI_ENTRY_TMPL.format(title=title), encoding="utf-8")
    (root / module / "ui" / "README.md").write_text(_UI_README_TMPL.format(title=title), encoding="utf-8")
    vendor = root / module / "ui" / "vendor" / "encre-plugin-ui-sdk"
    shutil.copytree(_sdk_dir(), vendor)
    (root / "pyproject.toml").write_text(_PYPROJECT_TMPL.format(dist=dist, title=title, ep_name=name, module=module), encoding="utf-8")
    (root / module / "__init__.py").write_text(f'"""{dist}."""\n', encoding="utf-8")
    (root / module / "plugin.py").write_text(_PLUGIN_PY.format(title=title, cls=cls, name=name), encoding="utf-8")
    (root / "README.md").write_text(_README_TMPL.format(dist=dist, name=name, module=module), encoding="utf-8")
    print(f"created {dist}/ (module {module}) - edit {module}/plugin.py + {module}/ui/src/index.ts, then run: encre-plugin build {dist}")


# ── sdk ───────────────────────────────────────────────────────────────


def cmd_sdk(args: argparse.Namespace) -> None:
    """Materialise the plugin UI SDK for frontend development."""
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        _fail(f"{out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    src = _sdk_dir()
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, out / item.name)
    contract = _ui_contract()
    print(
        f"plugin UI SDK {contract.get('sdk_version', '?')} -> {out}\n"
        f"  {len(contract.get('classes') or {})} classes, "
        f"{len(contract.get('modules') or [])} modules, "
        f"{len(contract.get('rpc') or [])} RPC methods, "
        f"{len(contract.get('slots') or {})} slots"
    )


# ── build ─────────────────────────────────────────────────────────────


def _build_one(pkg_dir: Path, *, allowed_tiers: tuple[str, ...] | None = None, no_isolation: bool = False) -> dict[str, Any]:
    """Validate policy, build the wheel/sdist, and return the catalog entry dict.

    Writes ``dist/ea-build-info.json`` alongside the wheel so the publish
    stage never re-hashes.  ``allowed_tiers`` widens the gate for the vendor
    pipeline; ``no_isolation`` skips the per-package venv/setuptools download
    (the batch build reuses the interpreter's already-present build backend).
    Raises SystemExit on policy or build failure.
    """
    py = read_pyproject(pkg_dir)
    manifest = _load_manifest(pkg_dir)
    group = (py.get("project", {}).get("entry-points") or {}).get("ea.plugins") or {}
    problems = validate_for_publish(py, manifest, extra_entry_points=max(0, len(group) - 1), allowed_tiers=allowed_tiers)
    if problems:
        print(f"publish policy violations ({pkg_dir.name}):")
        for p in problems:
            print(f"  - {p}")
        raise SystemExit(1)
    dist = str(py["project"]["name"])
    # Compile plugin frontend first: the manifest may reference ui/plugin.js,
    # and the wheel must contain the compiled asset (installs never build).
    frontend = _build_frontend(pkg_dir)
    _validate_ui_references(manifest, pkg_dir)
    if frontend and not _ui_module_referenced(manifest, UI_OUTPUT):
        _fail(
            f"compiled {UI_OUTPUT} is not referenced by the manifest; declare "
            f'{{"kind":"js_module","spec":{{"path":"{UI_OUTPUT}"}}}} in contributes.ui_contributions'
        )
    host = _host_python()
    if no_isolation:
        # A no-isolation build runs the backend in the host interpreter, so
        # wheel/setuptools must be importable there (the batch build relies
        # on this to skip a per-package venv + network fetch 249 times over).
        _ensure_pytools(host, "build", "wheel", "setuptools")
    else:
        _ensure_pytools(host, "build")
    dist_dir = pkg_dir / "dist"
    # Clean stale distributions from earlier builds: leftover old-version
    # wheels would otherwise leak into the artifacts dict and make twine
    # re-upload files PyPI already has ("file already exists" abort).
    if dist_dir.is_dir():
        for stale in dist_dir.iterdir():
            if stale.suffix in {".whl", ".gz"} or stale.name == BUILD_INFO:
                stale.unlink()
    cmd = [host, "-m", "build", "--outdir", "dist"] + (["--no-isolation"] if no_isolation else [])
    # PYTHONSAFEPATH: `python -m build` otherwise prepends the package dir to
    # sys.path, where a repo-level build.py would shadow pypa-build.
    r = _run(cmd, cwd=pkg_dir, env={**os.environ, "PYTHONSAFEPATH": "1"})
    if r.returncode != 0:
        print(f"python -m build failed:\n{r.stdout}\n{r.stderr}", file=sys.stderr)
        raise SystemExit(1)
    artifacts = {
        f.name: {"sha256": sha256_file(f), "size": f.stat().st_size}
        for f in sorted((pkg_dir / "dist").iterdir())
        if f.suffix in {".whl", ".gz"} and f.name != BUILD_INFO
    }
    if not artifacts:
        print("build produced no wheel/sdist", file=sys.stderr)
        raise SystemExit(1)
    entry = build_catalog_entry(manifest, pypi_package=dist, artifacts=artifacts, published_at=_now())
    info = pkg_dir / "dist" / BUILD_INFO
    info.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return entry


def cmd_build(args: argparse.Namespace) -> None:
    """Build a single package: policy-check, produce wheel/sdist, write build-info JSON."""
    entry = _build_one(Path(args.pkg_dir).resolve())
    print(f"built {len(entry['artifacts'])} artifact(s); catalog entry -> dist/{BUILD_INFO}")


# ── vendor (batch build the official packages) ────────────────────────


def cmd_vendor(args: argparse.Namespace) -> None:
    """Batch-build every official EA package into a registry-ready staging directory.

    Walks ``--src`` for ``ea-tool-*`` / ``ea-skill-*`` / ``ea-plugin-*``
    directories, builds each wheel with the vendor tier gate (bundled
    ``system-default`` allowed), and drops ``catalog.d/<name>.json`` + the
    wheels under ``--out``.  This is a GENERATOR: it never uploads to PyPI
    or opens a PR — run ``encre-plugin publish`` (or the registry PR flow)
    per package after reviewing the staging output.
    """
    src = Path(args.src).resolve()
    out = Path(args.out).resolve()
    catalog_dir = out / "catalog.d"
    wheels_dir = out / "wheels"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    wheels_dir.mkdir(parents=True, exist_ok=True)
    if not src.is_dir():
        _fail(f"no such package source: {src}")

    dirs = [
        d
        for d in sorted(src.iterdir())
        if d.is_dir()
        and (d / "pyproject.toml").is_file()
        and d.name.startswith(RESERVED_PREFIXES)
        and (not args.filter or any(f in d.name for f in args.filter))
    ]
    if not dirs:
        _fail(f"no {RESERVED_PREFIXES} packages under {src}")

    built, failed = 0, []
    for pkg in dirs:
        try:
            entry = _build_one(pkg, allowed_tiers=VENDOR_TIERS, no_isolation=not args.isolation)
        except SystemExit:
            failed.append(pkg.name)
            if not args.keep_going:
                _fail(f"{pkg.name} failed (use --keep-going to continue past failures)")
            continue
        name = str(entry["name"])
        (catalog_dir / f"{name}.json").write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for fname in entry["artifacts"]:
            src_file = pkg / "dist" / fname
            if src_file.is_file():
                shutil.copy2(src_file, wheels_dir / fname)
        built += 1

    print(f"vendor build: {built} built, {len(failed)} failed -> {out}")
    if failed:
        print("failed packages: " + ", ".join(failed), file=sys.stderr)
    print(
        "next: review catalog.d/, then `encre-plugin publish` each wheel "
        "(twine + registry PR); or point the registry CI at this staging dir."
    )


# ── verify ────────────────────────────────────────────────────────────


def cmd_verify(args: argparse.Namespace) -> None:
    """Install the built wheel into an isolated venv and probe the entry-point factory.

    The probe venv uses ``--system-site-packages`` so the Encre Agent SDK
    (not yet on PyPI during the 0.5.x transition) remains visible.  The
    probe imports the entry-point factory, constructs the plugin, and
    verifies its manifest has name and version set.
    """
    pkg_dir = Path(args.pkg_dir).resolve()
    py = read_pyproject(pkg_dir)
    source_manifest = _load_manifest(pkg_dir)
    _validate_ui_references(source_manifest, pkg_dir)
    ep = find_ea_entrypoint(py)
    if ep is None:
        _fail("no ea.plugins entry point to verify")
    wheels = sorted((pkg_dir / "dist").glob("*.whl"))
    if not wheels:
        _fail("no wheel in dist/ — run `encre-plugin build` first")
    _verify_wheel_ui_assets(wheels[-1], source_manifest)
    tmp = Path(tempfile.mkdtemp(prefix="ea-verify-"))
    try:
        py_bin = "Scripts/python.exe" if os.name == "nt" else "bin/python"
        host = _host_python()
        # System site-packages stay visible: the probe venv must prove the
        # WHEEL is well-formed, not re-resolve the Encre Agent SDK (which is
        # not on PyPI yet during the 0.5.x transition — a bare venv could
        # only fail for reasons unrelated to the package under test).
        r = _run([host, "-m", "venv", "--system-site-packages", str(tmp)])
        if r.returncode != 0:
            _fail(f"venv creation failed: {r.stderr}")
        venv_py = tmp / py_bin
        r = _run([str(venv_py), "-m", "pip", "install", "--quiet", str(wheels[-1])] + (["--no-deps"] if args.no_deps else []))
        if r.returncode != 0:
            _fail(f"wheel install failed:\n{r.stderr}")
        r = _run([str(venv_py), "-c", _PROBE, ep[1]])
        if r.returncode != 0:
            hint = ""
            if "No module named 'encre'" in r.stderr or "ModuleNotFoundError" in r.stderr:
                hint = (
                    "\n  hint: the probe venv cannot see the Encre Agent SDK — until "
                    "`encre-harness` is on PyPI, run verify with\n        PYTHONPATH "
                    "pointing at your local harness/ and core/ source trees."
                )
            _fail(f"entry point probe failed:\n{r.stderr}{hint}")
        manifest = json.loads(r.stdout)
        if not manifest.get("name") or not manifest.get("version"):
            _fail("probe manifest is missing name/version")
        print(f"verify ok: {manifest.get('name')} v{manifest.get('version')} imports and declares a valid manifest")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── publish ───────────────────────────────────────────────────────────

# Canonical registry (central repository) for the Encre Agent plugin market.
REGISTRY_URL = "https://github.com/mf2023/ea-cwh.git"


def _registry_cache_dir() -> Path:
    """Return the persistent home directory for the CLI-managed registry clone."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME")
    root = Path(base) if base else Path.home() / ".cache"
    return root / "encre-plugin-cli" / "registry"


def _resolve_registry(args: argparse.Namespace) -> Path:
    """Resolve or create a local registry checkout for the PR operation.

    A missing cache clone is fetched shallowly from ``--registry-url``; an
    existing one is re-synced onto the remote's default branch so the entry
    commit is always cut from current main.
    """
    import re

    url = args.registry_url
    if not re.fullmatch(r"(https?://|file://|ssh://|git@)[^\s]+", url or ""):
        _fail(f"--registry-url does not look like a git remote: {url!r}")
    if args.registry_dir:
        registry = Path(args.registry_dir).resolve()
        if not (registry / ".git").exists():
            _fail(f"{registry} is not a git checkout")
    else:
        registry = _registry_cache_dir()
        if not (registry / ".git").exists():
            registry.parent.mkdir(parents=True, exist_ok=True)
            r = _run(["git", "clone", "--quiet", url, str(registry)])
            if r.returncode != 0:
                _fail(f"cloning the registry failed:\n{r.stderr}")
    for cmd in (
        ["git", "fetch", "--quiet", "origin"],
        ["git", "checkout", "--quiet", "-f", "main"],
        ["git", "reset", "--quiet", "--hard", "origin/main"],
    ):
        r = _run(cmd, cwd=registry)
        if r.returncode != 0:
            _fail(f"`{' '.join(cmd)}` in {registry} failed:\n{r.stderr}")
    return registry


def cmd_publish(args: argparse.Namespace) -> None:
    """Upload the built wheel to PyPI and open a catalog PR against the registry.

    Reads ``dist/ea-build-info.json`` (produced by ``build``) for the catalog
    entry and artifact list.  ``--dry-run`` prints the payload without acting.
    ``--no-upload`` skips twine and only opens the registry PR.
    """
    pkg_dir = Path(args.pkg_dir).resolve()
    info_path = pkg_dir / "dist" / BUILD_INFO
    if not info_path.exists():
        _fail(f"dist/{BUILD_INFO} missing — run `encre-plugin build` first")
    entry = json.loads(info_path.read_text(encoding="utf-8"))
    dist_files = [str(f) for f in sorted((pkg_dir / "dist").iterdir()) if f.suffix in {".whl", ".gz"}]
    if args.dry_run:
        print(f"[dry-run] would upload: {dist_files}")
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return
    if args.no_upload:
        print("skipping PyPI upload (--no-upload); registry PR half only")
    else:
        host = _host_python()
        _ensure_pytools(host, "twine")
        r = _run([host, "-m", "twine", "upload", *dist_files])
        if r.returncode != 0:
            _fail(f"twine upload failed:\n{r.stdout}\n{r.stderr}")
        print(f"uploaded {entry['pypi_package']} {entry['version']} to PyPI")
    registry = _resolve_registry(args)
    _registry_pr(registry, entry)


def _registry_pr(registry: Path, entry: dict[str, Any]) -> None:
    """Drop the catalog entry into the registry checkout and open a PR via gh CLI.

    The branch is cut from origin/main BEFORE the entry is written, so the
    PR can only ever carry the single catalogue file — never leftover
    worktree state.  If ``gh pr create`` fails, the branch is left pushed
    so the author can open the PR manually.
    """
    name, version = str(entry["name"]), str(entry["version"])
    branch = f"publish/{name}-{version}"
    r = _run(["git", "checkout", "-B", branch, "origin/main"], cwd=registry)
    if r.returncode != 0:
        _fail(f"cannot branch the registry checkout:\n{r.stderr}")
    cdir = registry / "catalog.d"
    cdir.mkdir(exist_ok=True)
    target = cdir / f"{name}.json"
    target.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rel = str(target.relative_to(registry))
    for cmd in (
        ["git", "add", rel],
        ["git", "commit", "-m", f"catalog: {name} {version}"],
        ["git", "push", "-u", "origin", branch],
    ):
        r = _run(cmd, cwd=registry)
        if r.returncode != 0:
            print(f"warning: `{' '.join(cmd)}` failed:\n{r.stderr}", file=sys.stderr)
            print("entry written locally; open the PR manually", file=sys.stderr)
            return
    body = (
        f"Published `{entry['pypi_package']}=={version}` to PyPI.\n\n"
        f"CI verifies the merged catalog schema and every artifact digest "
        f"against PyPI before this may merge."
    )
    r = _run(["gh", "pr", "create", "--fill", "--title", f"catalog: {name} {version}", "--body", body, "--head", branch], cwd=registry)
    if r.returncode != 0:
        print(f"warning: gh pr create failed:\n{r.stderr}", file=sys.stderr)
        print(f"branch `{branch}` pushed — open the PR manually", file=sys.stderr)
    else:
        print(r.stdout.strip())


# ── catalog ───────────────────────────────────────────────────────────


def cmd_catalog_regen(args: argparse.Namespace) -> None:
    """Merge all catalog.d/*.json entry files into a single catalog.json document.

    Imports ``validate_catalog`` from the ``ea_cwh`` package.  Refuses to
    write when validation reports violations.  Sorting by name keeps diffs
    stable across regenerations.
    """
    from ea_cwh import validate_catalog

    registry = Path(args.registry)
    files = sorted((registry / "catalog.d").glob("*.json"))
    if not files:
        _fail(f"no entry files under {registry / 'catalog.d'}")
    entries = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    doc = merge_catalog(entries, registry_url=args.registry_url)
    problems = validate_catalog(doc)
    if problems:
        print("catalog violations (refusing to write):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        raise SystemExit(1)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(doc['plugins'])} entries -> {out}")


def cmd_catalog_check(args: argparse.Namespace) -> None:
    """Validate a catalog.json file against the ea-cwh schema and exit non-zero on violation."""
    from ea_cwh import validate_catalog

    doc = json.loads(Path(args.file).read_text(encoding="utf-8"))
    problems = validate_catalog(doc)
    for p in problems:
        print(f"  - {p}")
    if problems:
        raise SystemExit(1)
    print("catalog ok")


# ── plumbing ──────────────────────────────────────────────────────────


def _now() -> str:
    """Return the current UTC time as an ISO-8601 timestamp with second precision."""
    from datetime import datetime

    return datetime.now(UTC).isoformat(timespec="seconds")


def main(argv: list[str] | None = None) -> None:
    """Top-level CLI entry point: parse subcommands and dispatch to the matching handler.

    Subcommands are registered via argparse subparsers.  Each handler is
    a module-level function referenced by a ``set_defaults(fn=...)`` entry.
    When invoked under ``__main__``, ``sys.exit(main())`` is called so
    SystemExit propagates naturally.
    """
    parser = argparse.ArgumentParser(prog="encre-plugin", description="Encre Agent plugin market unified CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="scaffold an ea-plugin-* package")
    p.add_argument("name")
    p.add_argument("--dir", help="parent directory (default: cwd)")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("sdk", help="materialise the plugin UI SDK package")
    p.add_argument("--out", default="encre-plugin-ui-sdk")
    p.set_defaults(fn=cmd_sdk)

    p = sub.add_parser("build", help="policy check + plugin UI compile + wheel/sdist + sha256 digests")
    p.add_argument("pkg_dir", nargs="?", default=".")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("vendor", help="batch-build the official EA packages into a registry-ready staging dir")
    p.add_argument("--src", default="core/ea_tools", help="official package source tree (default: core/ea_tools)")
    p.add_argument("--out", default="dist/vendor", help="staging output dir (default: dist/vendor)")
    p.add_argument("--filter", action="append", help="only packages whose name contains this substring (repeatable)")
    p.add_argument("--keep-going", action="store_true", help="continue past per-package failures")
    p.add_argument("--isolation", action="store_true", help="build each wheel in a fresh isolated env (slower, needs network)")
    p.set_defaults(fn=cmd_vendor)

    p = sub.add_parser("verify", help="isolated install + entry-point smoke test")
    p.add_argument("pkg_dir", nargs="?", default=".")
    p.add_argument("--no-deps", action="store_true", help="skip dependency resolution")
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("publish", help="upload to PyPI + registry PR")
    p.add_argument("pkg_dir", nargs="?", default=".")
    p.add_argument("--registry-dir", help="existing registry checkout (default: cached clone of --registry-url)")
    p.add_argument("--registry-url", default=REGISTRY_URL, help=f"registry git remote (default: {REGISTRY_URL})")
    p.add_argument("--no-upload", action="store_true", help="skip twine; open the registry PR only")
    p.add_argument("--dry-run", action="store_true", help="print instead of uploading")
    p.set_defaults(fn=cmd_publish)

    p = sub.add_parser("catalog", help="central index maintenance")
    csub = p.add_subparsers(dest="catalog_command", required=True)
    c = csub.add_parser("regen", help="merge catalog.d/*.json into catalog.json")
    c.add_argument("--registry", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--registry-url", default="https://pypi.org")
    c.set_defaults(fn=cmd_catalog_regen)
    c = csub.add_parser("check", help="validate a catalog.json file")
    c.add_argument("file")
    c.set_defaults(fn=cmd_catalog_check)

    args = parser.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
