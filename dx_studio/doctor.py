"""Actionable dependency diagnostics; no installs or network requests."""
import importlib
import platform
import subprocess
from importlib.metadata import version,PackageNotFoundError


def report():
    from . import __version__
    checks=[]
    modules=[('dx_studio._cairo','cairocffi','Install Cairo: macOS brew install cairo; Ubuntu/WSL sudo apt install libcairo2. Relaunch after installation.'),('uharfbuzz','uharfbuzz','Run the launcher again to repair Python dependencies.'),('fontTools','fonttools','Run the launcher again to repair Python dependencies.'),('numpy','numpy','Run the launcher again to repair Python dependencies.'),('scipy','scipy','Run the launcher again to repair Python dependencies.'),('PIL','Pillow','Run the launcher again to repair Python dependencies.'),('soundfile','soundfile','Run the launcher again to repair Python dependencies; Linux may also need libsndfile1.')]
    for module,package,fix in modules:
        try:
            importlib.import_module(module)
            try:installed=version(package)
            except PackageNotFoundError:installed='available'
            checks.append({'name':package,'ok':True,'version':installed})
        except Exception:checks.append({'name':package,'ok':False,'fix':fix})
    for tool in ('ffmpeg','ffprobe'):
        try:
            result=subprocess.run([tool,'-version'],capture_output=True,text=True,timeout=10,check=True)
            checks.append({'name':tool,'ok':True,'version':result.stdout.splitlines()[0].split(' Copyright')[0]})
        except (OSError,subprocess.SubprocessError,IndexError):checks.append({'name':tool,'ok':False,'fix':'Install FFmpeg: macOS brew install ffmpeg; Ubuntu/WSL sudo apt install ffmpeg. Then relaunch.'})
    try:
        result=subprocess.run(['ffmpeg','-hide_banner','-encoders'],capture_output=True,text=True,timeout=10,check=True)
        supported='libx264' in result.stdout
        checks.append({'name':'H.264 encoder','ok':supported,**({'version':'libx264 available'} if supported else {'fix':'Use a FFmpeg build that includes the libx264 encoder.'})})
    except (OSError,subprocess.SubprocessError):pass
    return {'version':__version__,'python':platform.python_version(),'system':platform.system(),'architecture':platform.machine(),'ok':all(c['ok'] for c in checks),'checks':checks}

def doctor(json_output=False):
    data=report()
    if json_output:
        import json
        print(json.dumps(data,indent=2))
    else:
        print(f"DX Studio {data['version']} · Python {data['python']} · {data['system']} {data['architecture']}")
        for check in data['checks']:
            print(f"  {'OK' if check['ok'] else 'FIX'} {check['name']}: {check.get('version',check.get('fix',''))}")
        print('Ready to open DX Studio.' if data['ok'] else 'Fix the items above, then run the launcher again. See docs/INSTALL.md.')
    return 0 if data['ok'] else 1
