# Security

DX Editor is a loopback-only, single-user local tool. It is not designed for
internet exposure. A project scene is executable Python and runs with your
account's permissions. Review scene code or use an isolated environment before
opening projects from people you do not trust. Importing a zip is not sandboxing.

Use supported Python/dependency versions and keep your local FFmpeg current.
Request-size limits, path containment and same-origin checks reduce accidental
exposure; they do not make arbitrary scene code safe.

For a vulnerability, use the repository's private vulnerability reporting feature
when enabled, or contact the maintainer through their GitHub profile. Avoid public
issues containing exploit payloads or private files. The initial supported series
is 0.1.x; fixes are released through GitHub.
