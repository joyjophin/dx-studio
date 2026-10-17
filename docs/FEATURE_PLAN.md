# DX Studio: creator workflows and feature plan

Proposal dated 17 October 2026. This is a product backlog, not a list of shipped
features, a delivery schedule or a promise that every item will be built.

## Product direction

**Make a strong explainer with an assistant, then finish every important detail
in DX Editor without rebuilding the whole video.**

DX Studio should make the relationship between the script, voice, visuals and
saved edits understandable. A creator should be able to say “replace this take,”
“make this explanation clearer” or “turn this chapter into a Short,” see the
consequences, and keep control of the result.

The main audience is a solo YouTuber or small team making educational videos,
product explanations, software tutorials and narrated visual essays. Both the
skill and editor should work for beginners, while exposing precise controls when
needed. Channel identity, language, presenter appearance and visual style must be
creator choices. No personal sticker pack or specific AI vendor should be required.

## What exists today

The current source provides an editable scene renderer, a local editor, caption
phrase editing, text/shape/media overlays, layer transforms, visibility, ordering,
keyframes, animation presets, timeline snapping and ripple time edits. It supports
recorded narration, optional speech tools, music ducking, audio mastering and
portable project bundles.

The supplied templates support native 16:9 and 9:16 and presenter reservations.
Those reservations leave room for a talking head; they do not automatically
import, cut out, synchronise or place a presenter recording. Existing scene code
must opt into responsive layout. Saved differences and stable layer IDs help
preserve edits, but there is no conflict-aware AI revision workflow today.

This plan extends those foundations. For example, “better keyframes” means a
visual curve editor and reusable motion, rather than claiming keyframes are new.

## Creator scenarios to design around

| Creator situation | What a good DX Studio experience should allow | Relevant items |
| --- | --- | --- |
| “I have an idea but no script.” | Choose audience and outcome; compare a few openings; review a storyboard before expensive production. | S01–S04 |
| “I recorded eight minutes before making the visuals.” | Import takes, correct the transcript, align visual beats to actual speech, and build around it. | V01–V04, C01 |
| “I need my face in the right half, except during demonstrations.” | Use a real presenter clip and change layout by scene, with safe transitions and readable captions. | P01–P04 |
| “I explain a complicated idea without appearing on camera.” | Combine editable diagrams, evidence, charts, screenshots and purposeful motion. | M01–M04, B02–B03 |
| “I teach software and need viewers to see tiny controls.” | Record the screen, focus on relevant actions, annotate and redact private information. | T01–T04 |
| “The sponsor changed one sentence after I finished.” | Replace only that take, review the timing changes, and preserve unrelated work. | V03–V04, A01–A03, X03 |
| “The generated scene is good, but one diagram is confusing.” | Select that scene, explain the change to an assistant, compare the result and keep manual adjustments. | S02, A01–A03 |
| “I publish this series every week.” | Reuse channel styling, recurring scenes and episode templates without editing code. | B01, B04, M01 |
| “I need three Shorts from this long video.” | Select meaningful excerpts, add needed context and recompose graphics for a small vertical screen. | R02–R03, X02 |
| “I publish in English and Hindi.” | Keep meaning and terminology consistent; review translated text and narration, fonts and timing separately. | C02–C04, V04 |
| “I edit on a modest laptop.” | Use quick previews, proxies and caches, recover work after interruptions, and render reliably. | F01, F04, X02 |
| “An editor or collaborator needs to finish it.” | Share a portable project and timestamped notes, relink media and identify exactly which version was reviewed. | B02–B03, X03 |
| “Viewers leave when this explanation starts.” | Map real retention observations to the relevant scene and test a specific revision. | R01–R02, R04 |
| “I'm ready to upload.” | Catch mistakes, export the right versions and gather captions, chapters, credits and thumbnail candidates. | X01–X04 |

## How the editor should feel

Use three connected views of the same project, not three separate workflows:

- **Story:** scene cards, script, sources and narration. Answer “what are we
  explaining, and in what order?” before adjusting tiny animation details.
- **Edit:** preview, timeline and a contextual inspector. Select something to see
  its useful controls; keep advanced motion and compositing controls expandable.
- **Review and deliver:** notes, version comparisons, preflight and exports. Show
  the exact saved version being reviewed or built.

Keep direct manipulation available throughout. Ordinary caption fixes, layer
visibility, crop, scale, colour and timing changes should not require an assistant
or code. Make suggestion states explicit: proposed, accepted, overridden or
needs review. Explain expensive operations, show progress and offer cancellation.

## Priorities

- **A — Trust and control:** everyday editing, recovery, readable layouts and reliable preview/export.
- **B — Signature workflow:** narration-led editing and safe assistant-to-editor revisions.
- **C — Production range:** richer explanations, presenter production, channel reuse and repurposing.
- **D — Expansion:** advanced automation, localisation, review integrations and analytics.

These indicate recommended sequencing. A letter is not an estimate of effort.
Editor controls, engine changes and skill instructions are deliberately called
out: putting advice into a skill cannot substitute for a missing editor feature.

## 1. Everyday editing and reliability

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| F01 | Project home, autosave and recovery | Recent projects, thumbnails and missing-file status. Recover after a browser crash; create named versions such as “Before sponsor change.” Show when changes are safely stored. | Editor + storage / A |
| F02 | Faster timeline and layer editing | Multi-select, lock, solo, search, collapsible groups, trim/split, linked moves and clear ripple controls. Duplicate eligible objects; explain limitations of custom scene elements instead of silently failing. | Editor + engine / A |
| F03 | Better canvas controls | Resize and rotate handles, snapping guides, align/distribute, fit-to-frame and precise numeric controls. Keyboard navigation, visible focus and discoverable shortcuts. Resizable panels suit smaller laptop displays. | Editor / A |
| F04 | Responsive preview | Waveform/thumbnail caches, lower-quality preview modes, media proxies and cached scene ranges. Make dropped frames and loading visible. Use originals for final exports. | Engine + editor / A |

## 2. Story development before animation

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| S01 | A brief that adapts to the creator | Start from an idea, script, voice recording, screen recording or existing project. Capture audience, takeaway, duration, format, tone, language, presenter space, assets and output needs. Remember channel preferences. | Skill + editor setup / B |
| S02 | Script, storyboard and timeline together | Each scene card shows its narration, purpose, evidence, visual idea and rough duration. Reorder or revise a card and preview the affected timing before committing. | Editor + project model + skill / B |
| S03 | Strong openings and clear payoffs | Draft alternative openings grounded in the actual topic; show the viewer's question and when it gets answered. Check that the video delivers the promise, with a clear ending and optional relevant call to action. | Skill + story view / B |
| S04 | Evidence attached to scenes | Store source links, dates, quotations, asset references and verification notes beside claims. Flag missing support for review and produce a credits/source sheet. Human review remains necessary. | Skill + project model + editor / C |

## 3. Narration as the timing backbone

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| V01 | Narration workspace | Import or record voice, see a waveform, select ranges and audition at different speeds. Show takes and recording input levels, with a clear local-file fallback when browser recording is unavailable. | Editor + audio engine / B |
| V02 | Correctable transcript and alignment | Align supplied scripts or transcribe recordings; click a word to jump to it. Correct names without changing audio. Distinguish a spelling correction from an edit that removes spoken material. Flag uncertain alignment. | Speech adapter + editor / B |
| V03 | Take management and pickups | Keep multiple takes for a paragraph; audition and replace a selected sentence. Preview cuts, crossfades and room tone, with easy rollback. Optional voice generation is separate from recorded narration. | Editor + audio engine / B |
| V04 | Visuals anchored to meaning | Attach a reveal to a word or phrase instead of a fixed second. After a new take, propose new positions for visuals, captions and linked SFX. Preserve deliberate holds and locked timing; ask for review when an anchor disappears. | Project model + engine + editor / B |

## 4. Assistant revisions that respect the creator

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| A01 | Ask about the selected scene | “Simplify this chart,” “leave more room for my face” or “give this comparison a different visual.” Include selected IDs, scene context and restrictions in a portable request. External assistants remain usable. | Editor + skill + optional adapter / B |
| A02 | Protect manual decisions | Mark text, timing, layout, brand or whole scenes as protected from assistant revisions. Preserve existing edits; show conflicts between generated changes and creator overrides. Distinguish this protection from a canvas selection lock. | Revision model + editor + skill / B |
| A03 | Compare before applying | Preview changed scenes, list changed words/assets/timings and accept or reject changes by scene. Keep a recoverable version and warn if the project changed since the assistant began. | Engine + editor / B |
| A04 | Open assistant connection | Support a documented local project interface and file-based handoff; optional chat/API adapters show what context leaves the machine and any provider cost. No account or API key for normal editing. | Integration contract + skill / C |

## 5. A visual explanation toolkit

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| M01 | Editable explanation blocks | Insert comparisons, step sequences, timelines, quote cards, labelled diagrams, number counters and before/after scenes. Edit content and layout directly; choose a calm, editorial or energetic style. | Scene library + editor + skill / C |
| M02 | Motion controls with useful defaults | Visual easing curves, stagger controls, reusable entrances and reusable motion styles. Apply changes across related elements; offer reduced-motion variants and let the creator override presets. | Engine + editor / C |
| M03 | A camera for the explanation | Pan or zoom across grouped graphics, focus on one part of a diagram, dim supporting material, then return to the full view. Keep camera movement separate from each layer's position. | Engine + editor / C |
| M04 | Charts backed by editable data | Paste a table or import CSV; change numbers, labels, units and sources. Animate comparisons honestly, retain scales and data, and expose chart controls instead of flattening the result into an image. | Data model + renderer + editor / C |

## 6. Talking-head production and safe composition

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| P01 | Actual presenter placement | Drop in a presenter recording, trim it and fit/fill it into a chosen region. Adjust crop, border, shadow and volume. Offer an alpha-capable graphics-only export when an external editor will composite the presenter, with compatible container/codec choices. | Media engine + editor / B |
| P02 | Per-scene layout and custom zones | Switch among full graphics, corners, split screen and full presenter. Resize/move reserved regions; keep captions and important visuals out of them. Preview transitions and allow an explicit overlap override. | Layout model + templates + editor / B |
| P03 | Presenter masks and background control | Rounded, circular and freeform masks, chroma key and optional person cutout. Preview difficult edges and provide manual fallback; automatic cutout quality must be reviewed. | Compositor + optional model + editor / C |
| P04 | Sync and planned camera changes | Align a camera recording with separate voice audio, preserve lip sync through edits, and place close-ups or cutaways at chosen moments. Scene changes remain editable rather than random camera switching. | Audio/video timing + editor + skill / C |

## 7. Software tutorials and screen demonstrations

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| T01 | Screen capture and useful edits | Record a window or display with optional mic/camera, or import footage. Trim pauses, crop distractions and replace an outdated clip while preserving surrounding explanation. | Capture adapter + editor / C |
| T02 | Focus on the action | Suggest zooms around a cursor/click or a creator-selected area. Edit focus paths, include context before zooming and check the result at phone size. | Engine + editor + optional detection / C |
| T03 | Attached callouts and annotations | Arrows, highlights, step numbers and keyboard shortcuts follow their target through crop/zoom. Optional tracking helps moving UI; manual keyframes remain available. | Scene model + engine + editor / C |
| T04 | Redaction that survives export | Blur or cover emails, keys, faces and notifications over explicit ranges; track if needed. Review redacted ranges and confirm exports include them. Automated suggestions cannot promise detection of every secret. | Compositor + editor + preflight / C |

## 8. Sound that supports the explanation

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| D01 | Understandable audio mixer | Separate voice, presenter, footage, music and SFX controls; waveform views, mute/solo, fades, level meters and editable ducking. Show loudness and peaks at export. | Audio engine + editor / B |
| D02 | Voice repair with audition | Optional noise reduction, de-essing, EQ and compression. Compare before/after at matched loudness and retain the original take. | Optional processing + editor / C |
| D03 | Sound cues tied to the visual | Audition a reusable, clearly licensed sound library. Attach cues to reveals or actions, vary intensity and inspect the mapping. Muting or moving the visual updates the linked cue. | Library + existing cue engine + editor / C |
| D04 | Reviewed pause and filler edits | Suggest long pauses, repeated takes or filler words; preview each removal and its effect on breathing, visuals and rhythm. Make bulk application reversible. | Speech/timing engine + editor / D |

## 9. Captions, languages and accessibility

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| C01 | Accurate captions with expressive options | Word-level alignment, phrase splitting/merging, punctuation and a reusable pronunciation/name glossary. Select quiet subtitles or highlighted kinetic captions; import/export SRT and VTT. | Caption model + alignment + editor / B |
| C02 | Typography that handles real languages | Font import with coverage checks, fallback families, right-to-left layout and appropriate line breaking. Test complex scripts and mixed languages; flag overflow after translation. | Text engine + editor / C |
| C03 | Language versions of one project | Translate captions and editable on-screen text, manage reviewed terminology and attach alternate narration. Preview each language's reading time and timing; retain independent corrections. | Version model + optional translation + editor / D |
| C04 | Accessible output options | Contrast/readability checks, caption-safe layouts, editable non-speech cues, reduced-motion settings, transcript export and optional audio-description track support. | Renderer + editor + skill / C |

## 10. Channel identity, reusable assets and ownership

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| B01 | A real channel brand kit | Import logos, colours and fonts; define headline, caption, spacing and motion styles. Preview project-wide changes and keep intentional exceptions. | Token model + editor + skill / C |
| B02 | Media library and relinking | Search assets, inspect duration/resolution, replace a file while keeping crop/timing, and relink moved folders. Show missing assets before export. | Media index + editor / A |
| B03 | Asset provenance and credits | Store creator, source, licence and attribution with each imported asset. Offer a generic built-in pack and user-owned packs. Warn about missing information without pretending to certify reuse rights. | Asset model + skill + editor / C |
| B04 | Reusable channel templates | Save intro/outro, sponsor segment, lower thirds and recurring explanation scenes with exposed fields. Let instances inherit template updates or detach; show the update scope. Community templates declare dependencies and required rights. | Template model + library + editor / C |

## 11. Attention, meaningful variants and repurposing

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| R01 | An explainable review assistant | Point to specific dense captions, unreadable text, long static passages, missing visual support or unresolved story promises. Explain each suggestion and let the creator dismiss it. Avoid invented “viral” or retention scores. | Measurable checks + skill + editor / C |
| R02 | Alternate cuts and openings | Branch a video to compare different hooks, pacing, examples or endings. Preserve the original and show duration/content differences. Export variants without duplicating every asset. | Version model + editor / C |
| R03 | Deliberate long-form to Shorts conversion | Choose a chapter or transcript range; suggest a self-contained opening and ending. Reflow text/diagrams for 9:16, crop footage separately and retain per-format overrides. Show unsupported scenes that need manual recomposition. | Story + layout + timing + editor + skill / C |
| R04 | Learn from actual audience behaviour | Import creator-provided retention observations/data and map them to the exact published project version. Compare patterns and document hypotheses for the next episode. Add optional platform integrations only where available and authorised. | Analytics adapter + version links + skill / D |

## 12. Delivery, feedback and publishing preparation

| ID | Feature | Creator experience | Delivery / priority |
| --- | --- | --- | --- |
| X01 | Preflight with actionable fixes | Find missing media/fonts, clipped text, accidental gaps, unsafe overlaps, caption timing issues, failed frames and audio clipping. Link each finding to its scene/range. Allow intentional exceptions and distinguish warnings from blocking failures. | Engine checks + editor / A |
| X02 | Dependable export workspace | Choose format, resolution, frame rate and caption mode; export selected ranges or queue variants. Show progress, cancellation and errors. Add resumable rendering and parallelism only where cache validity and deterministic output can be verified. | Job system + engine + editor / A |
| X03 | Feedback tied to a version | Local timestamped notes, resolve/reopen status, contact-sheet reviews and exportable feedback. Portable handoff includes settings and asset status. Optional hosted review comes later, with a separate access and privacy design. | Version model + editor / C; hosted / D |
| X04 | A complete upload package | Gather final MP4, optional clean version, captions, transcript, chapters, credits, draft title/description and editable thumbnail candidates. Generate language deliverables when available. Upload/publishing remains a separate explicit creator action. | Exporter + skill + editor / C |

## The first complete workflow to build

Build a **narration revision workflow**, rather than several disconnected AI
buttons. Use this fixture: a 90-second landscape explainer with six scenes,
recorded voice, captions, a right-half presenter layout and an editable diagram.
The creator has moved the diagram and corrected two captions manually.

1. Import a replacement take for the third scene and inspect its transcript.
2. Correct a misheard product name without pretending the spoken audio changed.
3. Preview the proposed duration, anchor, caption and SFX changes. Keep explicit
   layout/text protections and manual positions intact.
4. Ask an external assistant to simplify that scene's diagram. Carry scene IDs,
   relevant sources, the current version and protected decisions in the request.
5. Compare the returned revision, surface conflicts and accept only that scene.
6. Save a named version, close/reopen the editor and confirm the same result.
7. Render the modified range for review, then export the complete video after
   preflight. Return to the earlier version if the creator prefers it.

This workflow validates V01–V04, C01 and A01–A03 on top of the A foundations. It
should be broken into small deliverable increments, not attempted as one large
rewrite. Begin with the waveform/transcript workspace and manual timing changes;
add word anchors and revision merging after their contracts are tested.

### Acceptance criteria

- Saved text, position, visibility and protected timing survive take replacement,
  assistant revisions, reopen and export, or produce an explicit conflict.
- All dependent tracks stay aligned after a reviewed timing change. A missing
  phrase never silently jumps to another occurrence.
- The creator can audition, reject and undo the change without losing the old take.
- Preview and export use the same saved revision and composition.
- Failed or cancelled builds do not replace a valid previous output.
- Recovery works after interruption; errors say what can be retried or repaired.
- No provider account is required to import, edit, review or export local material.

Measure task completion, correction time, recovery success and preview/export
performance on declared hardware and fixture projects. Set numerical targets
after collecting a baseline; do not turn unmeasured aspirations into claims.

## Recommended build sequence and gates

| Stage | Scope | Gate before moving on |
| --- | --- | --- |
| A: dependable editor | F01–F04, B02, X01–X02. Improve existing interactions; establish recoverable project revisions and reliable job state. | Reopen after interruption, relink media, make precise edits and reproduce the export from saved state on the supported test platforms. |
| B: signature workflow | S01–S03, V01–V04, A01–A03, C01, D01, P01–P02. Deliver the narration revision fixture in increments. | Finish the first complete workflow above with no silent loss of edits and explain every conflict. |
| C: useful production breadth | Prioritise M01, B01 and B04, then presenter/tutoring tools and R03 based on creator testing. Introduce remaining C items as complete workflows. | A creator makes a full episode and its vertical excerpt, with their brand and presenter, without code changes for ordinary finishing work. |
| D: informed expansion | Language versioning, advanced speech edits, real analytics and optional hosted review. | Validate demand, model quality, data access and maintenance cost; keep the local workflow intact. |

## Foundations to bake in before adding automation

These are engineering requirements supporting the backlog, not extra UI features:

- **Stable identities and revisions:** scenes, media, words/anchors and layers need
  persistent IDs, migrations and recoverable snapshots. Generated changes must
  identify their base revision and scope. Reject stale patches or surface conflicts.
- **Explicit timing:** distinguish source media time, scene time and final sequence
  time. Word anchors need repeated-word disambiguation, confidence and fallback
  behaviour. Edits must update linked tracks together while respecting locks.
- **Declared layout:** scenes declare graphics/caption/presenter regions, anchors
  and minimum readable sizes. Use per-format overrides when responsive reflow is
  insufficient. Custom code can declare limited capabilities honestly.
- **Safe round trips:** preserve creator overrides, removed/renamed layer history
  and unfamiliar fields. Template/engine upgrades need documented migrations.
- **Correct caches and builds:** invalidate by source, assets, settings, fonts,
  renderer and relevant model versions. Workers should render an immutable revision
  and publish output atomically. Parallel rendering must preserve determinism.
- **Modular editor and adapters:** separate timeline, inspector, transcript, jobs
  and project state as scope grows. Keep speech, translation, assistant and media
  services optional, with documented capabilities, licences and failure paths.
- **Project trust:** current scene files execute Python. Keep that clear; future
  review or plugin features need an explicit trust boundary before running
  third-party code or moving project data to a remote service.

## What belongs in the skill

The skill should maintain the brief, evidence, script, storyboard and visual
intent, expose editability, follow layout constraints, preserve IDs and respect
creator protections. It should choose a visual because it explains something,
review dense frames and pacing, and deliver a usable project and output package.

It should not promise transcription accuracy, invent research, assume any
sticker/model is freely redistributable, silently overwrite saved work, or claim
an editor control exists before it ships. In-editor and external-assistant
workflows should share the same project contract.

## Scope discipline

Start with complete explainer workflows. A full film colour-grading suite,
general 3D compositor, stock marketplace, social scheduler and cloud team platform
would each expand the product substantially. Revisit them only when a validated
creator need justifies the complexity. Optional integrations can provide breadth
while DX Studio concentrates on editable explanations and dependable revisions.

## Research notes

Official product documentation was checked on 17 October 2026. These establish
useful workflow expectations; they do not prove that a proposed DX feature is
implemented or that it will improve audience retention.

- [Adobe: Text-Based Editing](https://helpx.adobe.com/premiere/desktop/edit-projects/edit-video-using-text-based-editing/overview-of-text-based-editing.html)
  describes transcript-linked cutting. DX's proposed design additionally needs
  explicit relationships between words, generated graphics and creator overrides.
- [Adobe: Auto Reframe](https://helpx.adobe.com/premiere/desktop/add-video-effects/commonly-used-effects/auto-reframe-overview.html)
  describes reframing footage. DX must also recompose editable text and diagrams;
  changing crop alone is insufficient for an explainer.
- [Adobe: Create proxies](https://helpx.adobe.com/premiere/desktop/organize-media/ingest-proxy-workflow/create-proxies.html)
  documents lower-resolution media copies for editing performance.
- [YouTube: Multi-language features](https://support.google.com/youtube/answer/13338784)
  documents alternate audio and localised thumbnails. Availability depends on
  platform eligibility; DX can first prepare reviewed language deliverables.
- [YouTube: A/B test titles and thumbnails](https://support.google.com/youtube/answer/16391400)
  documents actual platform experiments. DX can prepare variants and record
  observations; suggested hooks are not measured test results.
