# live_loader.py
# ============================================================
# Loader por nombre (SCENE_NAME) con dos Engines: engine_curr / engine_next
# PC=1 -> PREPARE en engine_next (por nombre)
# PC=2 -> LAUNCH (lo preparado pasa a pantalla)
# Bindea los parámetros de la página "Music" por expresión CHOP a MUSIC_INS.
# Soporta lista de escenas en Table DAT 'scene_table' (name, path)
#   o, como fallback, Folder DAT 'scenes'.
# ============================================================

# ---------- CONFIG ----------
ENGINE_CURR   = 'engine_curr'
ENGINE_NEXT   = 'engine_next'

SCENE_NAME_DAT = 'SCENE_NAME'     # Table con col 'name' (fila 1 = nombre actual del clip)
SCENE_TABLE    = 'scene_table'    # Table con cols 'name','path' (fila 0 = headers)
SCENES_FOLDER  = 'scenes'         # Fallback: Folder DAT con los .tox

MUSIC_CHOP     = 'MUSIC_INS'      # CHOP con canales de música
RES_EXPORT_OP  = 'resolution_override'  # TOP/CHOP/ParCHOP que “exporta” resolución

# Aliases posibles del canal de program change dentro de MUSIC_INS
PC_CHANNEL_CANDIDATES = ['program', 'programchange', 'pc', 'prog', 'In0programchange']

# Mapeo de parámetros "Music" (simples: 1 valor)
SINGLE_MAP = {
    'In1bpm'   : 'out1_BPM',
    'In2beat'  : 'out2_BEAT',
    'In6kick'  : 'out6_KICK',
    'In7hihat' : 'out7_HIHAT',
    'In8snare' : 'out8_SNARE',
    'In9percs' : 'out9_PERCS',
}

# Pares (2 valores). (L,R, fallback)
PAIRS_MAP = {
    'In3lows'  : ('out3_LOWS_L',  'out3_LOWS_R',  'out3_LOWS'),
    'In4mids'  : ('out4_MIDS_L',  'out4_MIDS_R',  'out4_MIDS'),
    'In5highs' : ('out5_HIGHS_L', 'out5_HIGHS_R', 'out5_HIGHS'),
    'In10bass' : ('out10_BASS_NOTE_', 'out10_BASS_VEL', 'out10_BASS'),
}
# --------------------------------

OWNER = me.parent()
def _op(p): return OWNER.op(p) or op(p)
def _eng(n): return _op(n)
def _music(): return _op(MUSIC_CHOP)
def _scene_table(): return _op(SCENE_TABLE)
def _scene_folder(): return _op(SCENES_FOLDER)
def _scenename(): return _op(SCENE_NAME_DAT)

# ---------- utils ----------
def _toggle_res(delay_frames=2):
    x = _op(RES_EXPORT_OP)
    if not x: return
    run("n=op('{}'); n.export=False; n.export=True".format(x.path),
        delayFrames=max(0, int(delay_frames)))

def _chan_exists(chop, name):
    if not chop: return False
    try: return chop[name] is not None
    except: return False

def _bind_expr(par, expr):
    try: par.expr = expr
    except Exception as e:
        print('[live_loader] expr fail', par.name, '->', e)

# ---------- binding Music ----------
def _bind_single(engine, par_name, chan_name, chop):
    p = getattr(engine.par, par_name, None)
    if not (p and _chan_exists(chop, chan_name)): return
    _bind_expr(p, "op('{}')['{}']".format(chop.path, chan_name))

def _bind_pair(engine, base, left, right, base_only, chop):
    p1 = getattr(engine.par, base+'1', None)
    p2 = getattr(engine.par, base+'2', None)
    if not (p1 and p2): return
    if left and _chan_exists(chop, left):
        _bind_expr(p1, "op('{}')['{}']".format(chop.path, left))
    elif right and _chan_exists(chop, right):
        _bind_expr(p1, "op('{}')['{}']".format(chop.path, right))
    elif base_only and _chan_exists(chop, base_only):
        _bind_expr(p1, "op('{}')['{}']".format(chop.path, base_only))
    if right and _chan_exists(chop, right):
        _bind_expr(p2, "op('{}')['{}']".format(chop.path, right))
    elif left and _chan_exists(chop, left):
        _bind_expr(p2, "op('{}')['{}']".format(chop.path, left))
    elif base_only and _chan_exists(chop, base_only):
        _bind_expr(p2, "op('{}')['{}']".format(chop.path, base_only))

def bind_music_params(engine):
    if not engine: return
    m = _music()
    if not m:
        print('[live_loader] WARNING: no MUSIC_INS')
        return

    # program change
    pc_par = getattr(engine.par, 'In0programchange', None)
    if pc_par:
        for cand in PC_CHANNEL_CANDIDATES:
            if _chan_exists(m, cand):
                _bind_expr(pc_par, "op('{}')['{}']".format(m.path, cand))
                break

    for par_name, chan in SINGLE_MAP.items():
        _bind_single(engine, par_name, chan, m)

    for base, triple in PAIRS_MAP.items():
        left, right, base_only = (triple + (None,))[:3]
        _bind_pair(engine, base, left, right, base_only, m)

# ---------- escenas por nombre ----------
def _normalize_name(s):
    s = (s or '').strip()
    s = s.rsplit('.', 1)[0]
    return s.upper()

def _scene_name_from_dat():
    d = _scenename()
    if not d or d.numRows < 2: return None
    # intenta por etiqueta de columna
    try:
        return d[1, 'name'].val
    except:
        try: return d[1,3].val
        except: return None

def _find_scene_path_by_name(name):
    """Primero busca en scene_table(name,path). Si no, Folder DAT 'scenes'."""
    nm = _normalize_name(name)

    # 1) scene_table
    t = _scene_table()
    if t and t.numRows > 1:
        # localizar índices
        try:
            ix_name = t.col('name').index(0)  # fuerza excepción -> usamos otro camino
        except:
            # obtén posiciones por etiquetas
            cols = [c.lower() for c in t.colLabels]
            ix_name = cols.index('name') if 'name' in cols else None
            ix_path = cols.index('path') if 'path' in cols else None
        else:
            ix_name = t.colLabels.index('name') if 'name' in t.colLabels else None
            ix_path = t.colLabels.index('path') if 'path' in t.colLabels else None

        if ix_name is not None and ix_path is not None:
            for r in range(1, t.numRows):
                base = _normalize_name(t[r, ix_name].val)
                if base == nm:
                    return t[r, ix_path].val

    # 2) Folder DAT fallback
    f = _scene_folder()
    if f:
        cols = [c.lower() for c in f.colLabels]
        ix_file = None; ix_path = None
        for i,c in enumerate(cols):
            if c in ('name','file','filename'):
                ix_file = i if ix_file is None else ix_file
            if c in ('path','fullpath','file','filepath'):
                ix_path = i if ix_path is None else ix_path
        if ix_file is not None:
            for r in range(1, f.numRows):
                base = _normalize_name(f[r, ix_file].val)
                if base == nm:
                    return f[r, ix_path].val if ix_path is not None else None

    return None

# ---------- API ----------
def init():
    OWNER.store('curr_engine', ENGINE_CURR)
    OWNER.store('next_engine', ENGINE_NEXT)
    OWNER.store('prepared_path', None)
    bind_music_params(_eng(ENGINE_CURR))
    bind_music_params(_eng(ENGINE_NEXT))
    _toggle_res(2)
    debug_dump('init')

def prepare_scene_by_name(name:str):
    path = _find_scene_path_by_name(name)
    if not path:
        print('[live_loader] escena no encontrada:', name)
        return False
    nxt = _eng(ENGINE_NEXT)
    if not nxt:
        print('[live_loader] falta engine_next')
        return False
    nxt.par.file = path
    nxt.par.reload.pulse()
    bind_music_params(nxt)  # por si se resetea al cargar
    OWNER.store('prepared_path', path)
    _toggle_res(2)
    debug_dump('prepared:{}'.format(name))
    return True

def launch_prepared():
    cur = _eng(ENGINE_CURR)
    nxt = _eng(ENGINE_NEXT)
    if not (cur and nxt): return False
    # La escena ya está cargada en nxt y visible al conmutar selects/switches externos.
    # Aquí sólo nos aseguramos de que los parámetros sigan bindeados.
    bind_music_params(cur)
    bind_music_params(nxt)
    _toggle_res(1)
    debug_dump('launch')
    return True

def handle_program_change(val):
    try: pc = int(round(float(val)))
    except: pc = 0
    if pc == 1:
        prepare_scene_by_name(_scene_name_from_dat())
    elif pc == 2:
        launch_prepared()

def engine_ready(which:str):
    eng = _eng(which)
    bind_music_params(eng)
    _toggle_res(1)
    debug_dump('ready:{}'.format(which))

# ---------- DEBUG ----------
def _pv(eng, n):
    p = getattr(eng.par, n, None)
    if not p: return None
    try: return p.eval()
    except: return None

def _eng_summary(e):
    if not e: return 'None'
    parts = []
    for k in ['In1bpm','In2beat','In6kick','In7hihat','In8snare','In9percs']:
        v = _pv(e,k)
        if v is not None: parts.append(f'{k}={v}')
    for base in ['In3lows','In4mids','In5highs','In10bass']:
        v1 = _pv(e, base+'1'); v2 = _pv(e, base+'2')
        if v1 is not None and v2 is not None: parts.append(f'{base}=({v1},{v2})')
    return ', '.join(parts)

def debug_dump(tag=''):
    cur = _eng(ENGINE_CURR)
    nxt = _eng(ENGINE_NEXT)
    print('-'*66)
    print(f'[debug] tag="{tag}" | curr.file="{cur.par.file.eval() if cur else None}" | next.file="{nxt.par.file.eval() if nxt else None}"')
    print('[debug] curr:', _eng_summary(cur))
    print('[debug] next:', _eng_summary(nxt))
    print('-'*66)


# --- utils de nombre de escena y logging ---

def _read_scene_name():
    """Lee el nombre actual desde el DAT SCENE_NAME (fila 1, col 'name')."""
    try:
        d = _owner().op(SCENE_NAME_DAT)
        return d[1, 'name'].val.strip()
    except Exception:
        return ''

def on_scene_name_changed(new_name=None, source='datexec'):
    """
    Llamado desde un DAT Execute al cambiar la tabla SCENE_NAME.
    Solo imprime cuando realmente cambió el valor.
    """
    if new_name is None:
        new_name = _read_scene_name()

    p = _owner()
    prev = p.fetch('last_scene_name', '')

    if new_name != prev:
        print('[live_loader] scene_name changed ({}): "{}" -> "{}"'
              .format(source, prev, new_name))
        p.store('last_scene_name', new_name)
