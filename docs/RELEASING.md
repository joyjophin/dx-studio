# Maintainer release

Before publishing, run the contribution checks, review representative frames for
both formats, and confirm source/skill archives contain no personal media, secrets
or build caches. Keep imported fonts under their original licence.

```sh
python -m pytest
python scripts/smoke_test.py
python -m build
python scripts/package_release.py --output ../release-artifacts
```

The source zip and dx-studio-video.zip are alternative distributions of the same
public source. The skill zip has a `dx-studio-video/SKILL.md` entry point and its
local engine/resources. The wheel installs the engine/editor/templates; use the
repository or skill bundle for agent instructions, production guides and helpers.

Create the public repository as **dx-studio**, without an initial README or licence,
then push the prepared local repository. Enable Actions and private vulnerability
reporting. Review the repository description, screenshots and licence display.

For v0.1.0, attach the wheel, source distribution, source zip, skill zip and checksum
file to a GitHub release. Do not publish to PyPI without first checking ownership
and availability of the package name. A distribution name in pyproject.toml does
not mean the package is already registered on PyPI.

Suggested description: “AI-authored explainer videos that stay editable. Python
renderer, DX Editor, and a skill for Claude, ChatGPT and coding assistants.”
Suggested topics: motion-graphics, explainer-video, video-editor, python, agent-skills,
claude, chatgpt, open-source.

Before refreshing README visuals, see [GALLERY.md](GALLERY.md). Capture real editor
controls in a wide viewport, label the example, and regenerate rendered output
from its source. Keep available capabilities separate from roadmap items.
