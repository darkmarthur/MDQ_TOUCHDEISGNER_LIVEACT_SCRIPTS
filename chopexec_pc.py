# /DYNAMIC_LOADING_PROJECT/chopexec_pc.py

# Ruta ABSOLUTA al Text DAT con tu script
LIVE_LOADER_DAT = '/DYNAMIC_LOADING_PROJECT/live_loader'

# nombres posibles del canal de Program Change
PC_NAMES = ('program', 'programchange', 'pc', 'prog', 'In0programchange')

def _is_pc(ch):
    n = ch.name.lower()
    return ('program' in n) or (n in PC_NAMES)

def onValueChange(channel, sampleIndex, val, prev):
    if _is_pc(channel):
        try:
            op(LIVE_LOADER_DAT).module.handle_program_change(val)
        except Exception as e:
            print('[chopexec_pc] error:', e)
    return
