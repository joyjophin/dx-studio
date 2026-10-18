"""Project-owned font/logo imports and portable, reviewed brand kits."""
import base64
import copy
import io
import json
from pathlib import Path
import uuid
from zipfile import ZipFile, ZIP_DEFLATED
from fontTools.ttLib import TTFont, TTLibError
from .paths import contained


def import_font(project,path):
    source=Path(path).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in ('.ttf','.otf') or source.stat().st_size>20*1024*1024:raise ValueError('Choose a TTF/OTF font smaller than 20 MB')
    data=source.read_bytes()
    try:
        font=TTFont(io.BytesIO(data));font.getGlyphSet();coverage=len(font.getBestCmap() or {});font.close()
    except (TTLibError,ValueError,KeyError) as error:raise ValueError('This font could not be read') from error
    name='Brand/'+uuid.uuid4().hex+source.suffix.lower();dest=Path(contained(project.media.assets,name));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    return {'file':name,'name':source.stem,'characters':coverage}


def export_kit(project,values):
    from .brands import capture
    manifest={'format_version':1,'name':project.name,'tokens':capture('Current brand',project.schema,values)['tokens'],'assets':copy.deepcopy(values['__brand_assets'])}
    result=io.BytesIO()
    with ZipFile(result,'w',ZIP_DEFLATED) as archive:
        archive.writestr('brand.json',json.dumps(manifest,ensure_ascii=False))
        for file in sorted({*manifest['assets']['fonts'].values(),*([manifest['assets']['logo']] if manifest['assets'].get('logo') else [])}):
            path=contained(project.media.assets,file)
            if Path(path).stat().st_size>25*1024*1024:raise ValueError('Brand kit assets must be smaller than 25 MB each')
            archive.write(path,'assets/'+file)
    return result.getvalue()


def import_kit(project,data):
    if len(data)>50*1024*1024:raise ValueError('Use a brand kit smaller than 50 MB')
    from .brands import validate,resolve
    with ZipFile(io.BytesIO(data)) as archive:
        if sum(info.file_size for info in archive.infolist())>75*1024*1024 or len(archive.infolist())>100:raise ValueError('Brand kit is too large')
        manifest=json.loads(archive.read('brand.json'));preset=validate(manifest.get('name'),manifest.get('tokens'))
        if manifest.get('format_version')!=1:raise ValueError('Unsupported brand kit version')
        brand=manifest.get('assets',{});mapping={}
        if not isinstance(brand,dict) or not isinstance(brand.get('fonts',{}),dict) or not isinstance(brand.get('credits',{}),dict):raise ValueError('Invalid brand kit assets')
        if any(role not in ('reg','med','semi','bold','xb','med_t','xb_t') or not isinstance(file,str) for role,file in brand.get('fonts',{}).items()) or (brand.get('logo') is not None and not isinstance(brand['logo'],str)):raise ValueError('Invalid brand font or logo reference')
        if any(not isinstance(note,str) or len(note)>20000 for note in brand.get('credits',{}).values()):raise ValueError('Invalid brand credit note')
        for file in {*brand.get('fonts',{}).values(),*([brand['logo']] if brand.get('logo') else [])}:
            # Only declared members are read; no archive extraction or path traversal.
            contained(project.media.assets,file);blob=archive.read('assets/'+file)
            suffix=Path(file).suffix.lower()
            if suffix not in ('.ttf','.otf','.png','.jpg','.jpeg','.webp'):raise ValueError('Brand kit contains an unsupported asset')
            if suffix in ('.ttf','.otf'):
                try:font=TTFont(io.BytesIO(blob));font.getGlyphSet();font.close()
                except Exception as error:raise ValueError('Brand kit font is unreadable') from error
            else:
                from PIL import Image
                with Image.open(io.BytesIO(blob)) as image:image.verify()
            target='Brand/'+uuid.uuid4().hex+suffix;dest=Path(contained(project.media.assets,target));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob);mapping[file]=target
        assets={'fonts':{role:mapping[file] for role,file in brand.get('fonts',{}).items()},'logo':mapping.get(brand.get('logo')),
                'credits':{mapping.get(file,file):str(note)[:10000] for file,note in brand.get('credits',{}).items()}}
        return {'assets':assets,**resolve(preset,project.schema)}
