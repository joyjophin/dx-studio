# Export jobs

Profiles, frame rates, caption modes, selected ranges and sampled quality review are documented in [the creator workflow](CREATOR_WORKFLOW.md#export-what-you-need).

Available in DX Studio v1.0.

**Export → Build this export** saves the current settings, runs file/caption preflight and starts
an export. The job captures those saved editor settings. Further edits can be
saved while it runs without changing that settings snapshot.

Choose **Keep editing** to leave the progress panel. **Project menu → Last export** reopens
the active job, including after a browser reload while the local server remains
running. A completed job appears as **Last export ready**. The progress panel
shows whether it is preparing audio, rendering frames or finishing the MP4.
Export details contain the underlying logs for troubleshooting.

## Cancel without losing a completed video

**Cancel export** stops the job's process group, including its encoder processes.
Cancellation targets the displayed job ID, so a stale page cannot accidentally
cancel a different job. One job can run per project in a running editor server.
A cancelled or failed job keeps the previous completed MP4, with a link to open
it. The project and its saved edits are preserved.

Successful jobs publish the complete MP4 with an atomic file replacement. The
CLI also uses isolated audio/video intermediates and only replaces its target
after encoding and muxing succeed. Preview audio and exports do not share a
partially written mix. Media caches use writer locks and publish completed frames
and audio atomically, so concurrent preview/export readers do not use incomplete
cache output.

The editor reports when newer edits have been saved since a completed export.
Rebuild to include them. Normal editor shutdown cancels active jobs. This is not
resumable rendering after a server restart; interrupted disposable files may
remain in `.build`. Source code and source files should stay stable while a job
uses them; the captured snapshot covers editor settings.

## Command-line output

```sh
dx-studio build projects/my-video
dx-studio build projects/my-video --output exports/review.mp4
```

Custom output paths must stay inside the project, use `.mp4`, and must not replace
a referenced media/audio source. Parent folders are created when needed. Advanced
workflows can pass `--settings` with a settings snapshot inside the project.
For a separate no-narration version after building the same saved settings:

```sh
python scripts/novoice.py projects/my-video outputs/no-voice.mp4
# Also silence imported footage when needed:
python scripts/novoice.py projects/my-video outputs/no-voice.mp4 --mute-footage
```

The helper reuses the completed MP4's video stream and builds its own temporary
audio. It preserves the voiced master and needs no shared build intermediates.
Footage audio is retained unless explicitly muted with the option above.

Source/1080p/720p profiles, output frame rates, caption modes and selected-range
exports are included. Render queues and restart-resumable rendering remain planned.

Before publication, FFprobe checks the temporary MP4 dimensions, frame rate, duration
and presence of audio/video streams. Failed validation keeps the previous completed
video. Preflight also checks available working space, writable output folders, source
collisions and clip source trims. File-size requirements depend on the project; the
space warning is not an exact storage estimate. Downloads stream in bounded chunks.

![Cancelled export keeps the previous completed video](images/export-jobs.png)

![Completed export](images/export-ready.png)
