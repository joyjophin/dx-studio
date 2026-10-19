# Install DX Studio v1.0

DX Studio is a local Python application with a browser editor. It requires Python
3.10+, Cairo, FFmpeg and FFprobe. The first Python dependency installation needs
internet access. Normal editing/rendering needs no account, API key, GPU or model.
This release is a source/skill/wheel distribution, not a signed standalone app.

## Supported paths

| Platform | Installation and validation |
| --- | --- |
| macOS | Homebrew prerequisites and the local launcher. Launch validation on arm64. |
| Ubuntu / Debian | System packages and the local launcher. Ubuntu CI on Python 3.10 and 3.13. |
| Windows | Use Ubuntu in WSL2; follows Linux setup. No separate WSL2 launch validation; native Windows is not supported for v1.0. |

Use a current desktop Chromium browser. Launch UI review uses the Chromium-based
in-app browser; mobile browsers, Safari and Firefox have not received a separate
v1.0 validation pass.

## 1. Install system prerequisites

macOS, with Homebrew already installed:

```sh
brew install python cairo ffmpeg
```

Ubuntu / Debian / Ubuntu in WSL2:

```sh
sudo apt-get update
sudo apt-get install python3 python3-venv libcairo2 libsndfile1 ffmpeg
```

DX Studio does not install system packages or request administrator access itself.

## 2. Download and open

Download **dx-studio-1.0.0-source.zip** from the GitHub release and extract it.
On macOS, open **Launch DX Studio.command**. On Linux/WSL2, run:

```sh
bash launch.sh
```

The launcher creates `.venv` in that folder, installs the engine's Python packages,
checks imports, FFmpeg/FFprobe and H.264 support, then opens the local dashboard.
Keep its terminal window running while editing. Close the editor server with
Ctrl+C when finished. No system Python modifications, OS font installation or
speech-model downloads occur. Bundled fonts render directly from their outlines.

The launcher recognizes standard Homebrew library paths on macOS. If the first
run fails, read the named fix, install the missing prerequisite and launch again.
For dependency repair use `bash launch.sh --repair`. For checks without opening
an editor use `bash launch.sh --doctor`.

## Manual environment or wheel

From the extracted source folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m dx_studio doctor
python -m dx_studio edit
```

Developers can install `'.[dev]'` for checks. To use a release wheel, replace the
install line with `python -m pip install /path/to/dx_studio-1.0.0-py3-none-any.whl`.
The wheel includes the editor, engine, templates and fonts; use the skill ZIP or
source ZIP for assistant instructions and production scripts. No PyPI publication
is implied. A portable project bundle has its own matching `engine/` installation.

For a nonstandard Cairo location on macOS, run
`DX_STUDIO_CAIRO_LIB=/path/to/library/folder bash launch.sh`. The launcher sets the
native library path after entering the shell, since macOS can strip `DYLD_*`
variables when starting a system shell. For a direct Python command,
`DYLD_FALLBACK_LIBRARY_PATH` can also be set. `doctor --json` prints a shareable report without
project names, local paths, scripts or media. Review it before attaching it to a
bug report. The editor offers the same report in Project menu → Installation & diagnostics.

## First project and upgrades

Choose **Try a sample**, **New project**, or **Open project**. The optional guide
is also available in Project menu → Getting started. See [QUICKSTART](QUICKSTART.md).
For explicit ports use `python -m dx_studio edit --port 8800 --no-browser`.

The server accepts loopback requests only. Do not expose it through a public tunnel.
Scenes execute Python; open trusted projects. See [COMPATIBILITY](COMPATIBILITY.md)
before upgrading a working project, and [SECURITY](../SECURITY.md) for that boundary.
