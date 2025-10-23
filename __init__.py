import bpy

bl_info = {
    "name": "Poser Rigger",
    "author": "Jess Green",
    "version": (1, 0),
    "blender": (4, 5, 3),
    "location": "View3D",
    "category": "Object",
}

classes = ()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

