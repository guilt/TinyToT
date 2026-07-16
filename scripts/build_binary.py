"""
Build a fully self-contained tinytot binary using PyInstaller.

PyInstaller bundles Python, all compiled extensions (.so/.pyd), and all
pure-Python packages into a single executable — no venv required at runtime,
and it works on macOS, Linux, and Windows.

    make build-binary       # → dist/tinytot  (Unix)  or  dist/tinytot.exe  (Windows)

Usage:
    pipenv run python scripts/build_binary.py [--output-dir dist/]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ENTRY_SCRIPT = REPO_ROOT / "scripts" / "_tinytot_entry.py"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build self-contained tinytot binary via PyInstaller",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "dist"),
        help="Output directory (default: dist/)",
    )
    args = parser.parse_args()

    # Write entry script (gitignored, cleaned up after build)
    ENTRY_SCRIPT.write_text(
        "from tinytot.server import main\nmain()\n",
        encoding="utf-8",
    )

    workDir = REPO_ROOT / "build" / "pyinstaller"
    # Clean workpath manually, then copy _data under it so the relative --add-data resolves.
    # (PyInstaller's --clean would delete our copy before Analysis runs.)
    if workDir.exists():
        shutil.rmtree(workDir, ignore_errors=True)
    srcData = REPO_ROOT / "tinytot" / "_data"
    dstData = workDir / "tinytot" / "_data"
    dstData.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        srcData,
        dstData,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".sources", "journal"),
    )
    srcWeb = REPO_ROOT / "tinytot" / "_web"
    dstWeb = workDir / "tinytot" / "_web"
    if srcWeb.exists():
        shutil.copytree(srcWeb, dstWeb, dirs_exist_ok=True)

    sep = ";" if sys.platform == "win32" else ":"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "tinytot",
        "--onefile",
        "--distpath",
        args.output_dir,
        "--workpath",
        str(workDir),
        "--specpath",
        str(workDir),
        "--add-data",
        f"tinytot/_data{sep}tinytot/_data",
        "--add-data",
        f"tinytot/_web{sep}tinytot/_web",
        # uvicorn loads workers dynamically — must be declared explicitly
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.loops.asyncio",
        "--hidden-import",
        "uvicorn.loops.uvloop",
        "--hidden-import",
        "uvicorn.lifespan.on",
        "--hidden-import",
        "uvicorn.lifespan.off",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.http.h11_impl",
        "--hidden-import",
        "uvicorn.protocols.http.httptools_impl",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.websockets_impl",
        "--hidden-import",
        "uvicorn.protocols.websockets.wsproto_impl",
        "--noconfirm",
        "--log-level",
        "WARN",
        str(ENTRY_SCRIPT),
    ]

    print("Running PyInstaller (onefile)...")
    result = subprocess.run(cmd, cwd=REPO_ROOT)

    # Clean up entry script regardless of outcome
    ENTRY_SCRIPT.unlink(missing_ok=True)

    if result.returncode != 0:
        print("\nBuild failed. Make sure PyInstaller is installed: pip install pyinstaller")
        sys.exit(result.returncode)

    suffix = ".exe" if sys.platform == "win32" else ""
    out = Path(args.output_dir) / f"tinytot{suffix}"
    print(f"\nBuilt:  {out}")
    print(f"Run:    {out} -p 'What is pi?'")
    print(f"        {out}   # start server on port 11434")


if __name__ == "__main__":
    main()
