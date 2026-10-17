# Install DX Studio

DX Studio 0.1 is an initial open source release. Python 3.10+ and a native Cairo
library are required. Export and footage decoding require FFmpeg (including ffprobe).
No hosted service, account, GPU, paid API or voice model is needed for the demo.

## macOS

```sh
brew install python cairo ffmpeg
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m dx_studio doctor
```

## Ubuntu / Debian

```sh
sudo apt-get update
sudo apt-get install python3 python3-venv libcairo2 ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m dx_studio doctor
```

Run these commands inside an extracted or cloned repository. Prefer a virtual
environment; the setup never uses `--break-system-packages`, installs fonts
system-wide, or downloads models automatically during ordinary installation.
Fonts render directly from bundled outlines and need no OS font registration.

## Windows

Use Ubuntu in WSL2 and follow the Linux instructions. Native Windows installation
has not been validated for this release. The editor is a local browser interface.

## First project

```sh
python -m dx_studio init projects/hello --format 9:16
python -m dx_studio check projects/hello
python -m dx_studio edit projects/hello
```

DX Editor opens on localhost. Save edits, then use **Build video** or run
`python -m dx_studio build projects/hello`. For landscape create a separate project
with `--format 16:9`. Use `--port 8800 --no-browser` when needed.

If Cairo cannot be found on macOS, confirm Homebrew's library path is visible to
the Python interpreter. `DYLD_FALLBACK_LIBRARY_PATH=$(brew --prefix)/lib` can be set
for that command. `doctor` diagnoses imports and command-line dependencies without
installing anything. Do not expose the editor through a public tunnel.
