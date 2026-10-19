# Projects and layer controls

## Start with a project

Run `dx-studio edit` to open project home. Choose **Create with AI** for external
assistant instructions, **Start from a template** for Make it click or Proof point,
or **Start blank** to set dimensions, duration and presenter space before adding
titles and story notes. Expand **Save location** to choose the parent folder.
Existing folders are never overwritten. Follow the [three workflows](AI_WORKFLOW.md)
for same-chat AI revisions and the JSON skeleton handoff.

To continue an assistant-created video, paste its project folder in **Open a
project**. Open trusted projects: scene files run Python. Search recent projects
by name or path. Removing a recent item only removes its entry, keeping all files.
Missing folders are marked so you can find and open their new location.

Use the **Back to projects** arrow in the editor to save pending changes and return home. Each
project has a separate URL, browser recovery draft, history, media and saved
settings. Opening the same project in two tabs still uses stale-save protection.
The library stores paths and metadata locally. Browsing recents does not execute
scene code; thumbnails for unopened projects use a previously cached preview.

![Project home](images/workflow-dashboard.jpg)

See [the editor layout guide](EDITOR_LAYOUT.md) for the tool rail, contextual
inspector and expandable timeline tracks.

## Work with layers together

In **Media → Layers**, search by label, ID or group. Matching children retain parent
context. Use the checkboxes or Shift/Ctrl/Command-click to select several layers.
**Select results** or Ctrl/Command+A selects the unlocked search results.
**Clear** clears the selection. Renaming changes the display label and keeps
stable IDs used by scene code.

Move selected layers together on the canvas or drag their timeline bars. Selecting
both a parent and its child moves the hierarchy once. Arrow nudges use the same
selection; hold Alt for nudging, with Shift for ten pixels. Bulk actions can show,
hide, lock, duplicate added text/shapes/media, or delete added layers. Scene-defined
layers are hidden instead of removed from source.

A locked layer stays visible but cannot be moved, retimed or changed with its
layer controls. A locked parent protects its children; unlock the parent first.
Locks protect editor gestures, not global scene parameters or changes to Python
source. **Solo graphics** isolates selected graphics in the preview. **Exit solo**
returns to the whole composition. Solo is temporary and does not change exports.

## Compose deliberately

Choose the alignment reference: selection bounds, full frame or graphics safe
zone. Align left, centre, right, top, middle or bottom. For one selected layer,
selection bounds falls back to the full frame. **Space H/V** distributes at least
three visible layers with equal gaps. The playhead must show all selected layers.
A single layer also has **Fit graphics safe zone**, which scales and centres it
inside the reserved graphics area.

**Snap** (S) controls timeline and canvas snapping. Hold Alt during a
drag to temporarily disable snapping. The rendered preview updates throughout
continuous dragging and slider input; heavier scenes may preview at a lower rate.
Undo/redo and autosave apply to these edits.
See [saving and recovery](SAVING.md) for restore and version controls.

![Bulk layer controls](images/editor-bulk.png)

## Persistent selection groups

Select multiple layers, then choose **Group selection** in the inspector. Give the
group a name. Selecting a member selects the group for moving, alignment, timing,
visibility and lock actions. Saved groups survive closing, reopening and project
handoffs. **Ungroup** exposes individual selection again. This is selection
membership, not a new nested transform or a merge of scene source. Locked members
remain protected. Find named groups in Media → Layers → Selection groups.
