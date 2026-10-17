"""One Cairo API for scenes, with a wheel-only Python binding by default."""
try:
    import cairo
except ImportError:
    try:
        import cairocffi as cairo
    except OSError as exc:
        raise RuntimeError("Cairo is missing. macOS: brew install cairo; Ubuntu: apt install libcairo2. See docs/INSTALL.md.") from exc
