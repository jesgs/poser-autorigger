import bpy
from .generate_base_rig import setup_poser_figure

class OT_GenerateBaseRig_Operator(bpy.types.Operator):
    bl_idname = "poser.generate_base_rig"
    bl_label = "Generate Base Rig"
    bl_description = "Generate Base Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if len(context.scene.objects) == 0:
            return False

        return True

    def execute(self, context):
        setup_poser_figure(context.selected_objects)
        return {'FINISHED'}
