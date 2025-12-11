import bpy
from .generate_base_rig import setup_poser_figure

class OT_GenerateBaseRig_Operator(bpy.types.Operator):
    bl_idname = "poser.generate_base_rig"
    bl_label = "Generate Base Rig"
    bl_description = "Generate Base Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        setup_poser_figure(context.active_object)
        return {'FINISHED'}

class OT_GenerateFaceRig_Operator(bpy.types.Operator):
    bl_idname = "poser.generate_face_rig"
    bl_label = "Generate Face Rig"
    bl_description = "Generate Face Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'


    def execute(self, context):
        setup_poser_figure(context.active_object)
        return {'FINISHED'}
