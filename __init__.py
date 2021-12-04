bl_info = {
    "name" : "Library",
    "author" : "Timothy Halim Septianjaya",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location": "View3D > Properties > Asset Library",
    "warning" : "",
    "category" : "3D View"
}


import sys
import importlib
in_blender = False
if sys.modules.get("bpy"):
    in_blender = True
    
module_names = [ 'properties', 'panel' ] if in_blender else []

module_full_names = [ f"{__name__}.{module}" for module in module_names ]

for module in module_full_names:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        locals()[module] = importlib.import_module(module)
        setattr(locals()[module], 'module_names', module_full_names)

def register():
    for module in module_full_names:
        if module in sys.modules:
            if hasattr(sys.modules[module], 'register'):
                sys.modules[module].register()

def unregister():
    for module in module_full_names:
        if module in sys.modules:
            if hasattr(sys.modules[module], 'unregister'):
                sys.modules[module].unregister()