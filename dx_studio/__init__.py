"""DX Studio: author editable motion graphics. Public scene API loads lazily."""
from importlib import import_module
__version__ = "0.1.0"
_EXPORTS = {
    **{k:'core' for k in ['PI','WHITE','BLACK','clamp','eo','eio','ei','lin','P','lerp','mixc','window','back_ease','hexc','hex_of']},
    **{k:'text' for k in ['FONTS','shape','tw','text','ktext']},
    **{k:'draw' for k in ['rrect','fill','fillp','stroke','shadow','card','check','star','glow','arrow_curve','make_bg','to_surface','sparks','Motes']},
    **{k:'stickers' for k in ['draw_avatar','draw_walker','draw_gif','avatar_surf']},
    'draw_captions':'captions','Layer':'layers','render_layers':'layers','VoiceTimes':'voice','cairo':'_cairo',
}
__all__ = list(_EXPORTS)
def __getattr__(name):
    if name in _EXPORTS:
        module = import_module('.'+_EXPORTS[name], __name__)
        value = getattr(module,name)
        # Importing a submodule also sets a package attribute of the same name.
        # Keep the original public `text()` callable when resolving any text export.
        if _EXPORTS[name] == 'text': globals()['text'] = module.text
        globals()[name] = value
        return value
    raise AttributeError(name)
