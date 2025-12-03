# /DYNAMIC_LOADING_PROJECT/exec_scene_name  (DAT Execute)

LIVE_LOADER_DAT = '/DYNAMIC_LOADING_PROJECT/live_loader'

def _emit(tag, dat):
    try:
        name = dat[1, 'name'].val.strip() if dat.numRows > 1 else ''
    except Exception:
        name = ''
    try:
        op(LIVE_LOADER_DAT).module.on_scene_name_changed(name, source=tag)
    except Exception as e:
        print('[exec_scene_name] error:', tag, e)

def onCellChange(dat, cells):
    # Cambia una o varias celdas -> dispara
    _emit('SCENE_NAME(cell)', dat)
    return

def onDATChange(dat):
    # El DAT cambió por cualquier motivo (recook del Select, etc.)
    _emit('SCENE_NAME(dat)', dat)
    return
