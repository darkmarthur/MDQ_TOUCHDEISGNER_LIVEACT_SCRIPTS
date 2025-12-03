# /DYNAMIC_LOADING_PROJECT/exec_live_loader.py
# Ruta ABSOLUTA al Text DAT con tu script
LIVE_LOADER_DAT = '/DYNAMIC_LOADING_PROJECT/live_loader'

def onStart():
    # Dale 2 frames para que todo exista y luego llama a init()
    run("op('{}').module.init()".format(LIVE_LOADER_DAT), delayFrames=2)
    return

def onProjectLoad():
    # Igual al abrir el .toe
    run("op('{}').module.init()".format(LIVE_LOADER_DAT), delayFrames=2)
    return
