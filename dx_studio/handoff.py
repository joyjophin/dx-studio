"""Provider-independent AI brief: constraints, editable state and source, never an MP4."""
import copy
from datetime import datetime, timezone
from pathlib import Path
from .paths import contained
from .history import atomic_json

INSTRUCTIONS = [
    'Work in the existing project folder when it is accessible. Continue in the same chat for creative context; folder access must be granted separately.',
    'Read project.json, scene.py, settings.json and this handoff before changing anything. Effective values include the creator’s saved edits.',
    'Respect canvas dimensions, duration, safe areas and presenter reservations. Keep essential graphics and captions out of the presenter area.',
    'Preserve existing layer IDs, parameter keys, imported media, manual transforms, protected decisions and saved settings unless the user asks to change them.',
    'Use the storyboard and existing editable title/media elements as the skeleton. Add new artwork as named editable layers, not a flattened video.',
    'Use the DX Studio skill and matching installed engine. Write complete files atomically, inspect affected frames and render an MP4 when requested.',
    'For a settings-only revision, prefer the reviewable patch contract in reference/ASSISTANT_REVISIONS.md.',
    'Return a summary of changed files. Ask the creator to use Reload AI changes in DX Editor after the files are complete. Never claim to access a folder you cannot access.',
    'If you cannot access the folder, request a portable project bundle and return an updated project folder. This JSON does not embed binary media or the engine.',
]


def document(project, request='', revision=None, source_revision=None):
    if not isinstance(request,str) or len(request)>20000:raise ValueError('Keep the assistant brief under 20,000 characters')
    from .relink import references
    source_names={'project.json',project.cfg.get('scene','scene.py'),project.cfg.get('captions','captions.json'),'settings.json'}
    # Include local helper code as context, without following symlinks outside the project.
    source_names.update(p.name for p in Path(project.path).glob('*.py'))
    files={}
    for name in sorted(source_names):
        path=Path(contained(project.path,name))
        if path.is_file():files[name]=path.read_text(encoding='utf-8')
    from .composition import layout_for
    layout=layout_for(project.width,project.height,project.values['__composition'],project.cfg.get('safe_area'))
    data={
        'format_version':1, 'kind':'dx-studio-ai-handoff',
        'created_at':datetime.now(timezone.utc).isoformat(),
        'request':request.strip(), 'project_folder':project.path,
        'project':{'name':project.name,'configuration':copy.deepcopy(project.cfg)},
        'constraints':{'width':project.width,'height':project.height,'fps':project.fps,
            'source_duration_seconds':project.base_duration,'output_duration_seconds':project.duration,
            'presenter':project.values['__composition'],'layout':layout,
            'scene_presenter_layouts':copy.deepcopy(project.values.get('__presenter',{})),
            'protected':copy.deepcopy(project.values.get('__protected',[]))},
        'storyboard':copy.deepcopy(project.values.get('__story',[])),
        'editable_values':copy.deepcopy(project.values),
        'layers':copy.deepcopy(project.layer_meta),
        'media': [{'file':Path(path).relative_to(project.path).as_posix(),'kind':kind,
                   'available':Path(path).is_file()} for path,kind in references(project).items()],
        'files':files, 'revision':revision,'source_revision':source_revision,
        'instructions':INSTRUCTIONS,
        'skill':'https://github.com/joyjophin/dx-studio/blob/main/SKILL.md',
        'delivery':{'editable_project':True,'mp4':'when requested','preserve_saved_edits':True},
    }
    return data


def export(project,request='',revision=None,source_revision=None):
    data=document(project,request,revision,source_revision)
    # The local copy is the source checkpoint for this handoff. It contains the
    # files and edits above, not an independent backup of large media assets.
    import uuid
    folder=Path(project.path)/'.dx-studio'/'ai-handoffs';folder.mkdir(parents=True,exist_ok=True)
    atomic_json(folder/(uuid.uuid4().hex+'.json'),data)
    atomic_json(Path(project.path)/'dx-ai-handoff.json',data)
    return data


def prompt(project_folder,request=''):
    return (f'Use the DX Studio video skill to continue the project in this folder:\n{project_folder}\n\n'
            f'Read dx-ai-handoff.json, project.json, scene.py and settings.json first.\n\n{request.strip()}\n\n'
            'Keep the existing canvas, duration, presenter reservation, layer IDs and my manual edits. '
            'Build on the titles and storyboard in the handoff. Save the updated editable project in the same folder, '
            'inspect the affected frames, and tell me when I can use Reload AI changes in DX Editor. '
            'If you do not have access to this folder, say so and ask for the portable project bundle.')
