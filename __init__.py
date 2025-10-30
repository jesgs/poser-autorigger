import bpy
from .generate_base_rig import *

bl_info = {
    "name": "Poser Rigger",
    "author": "Jess Green",
    "version": (1, 0),
    "blender": (4, 5, 3),
    "location": "View3D",
    "category": "Object",
}


classes = [RigPoserArmature_PT_Panel, OT_GenerateBaseRig_Operator]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
