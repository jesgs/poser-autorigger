import bpy

class RigPoserArmature_PT_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Rig Poser"
    bl_category = "Rig Poser"
    bl_idname = "VIEW3D_PT_RigPoserArmature_PT_Panel"

    def draw(self, context):
        layout = self.layout
        op_row = layout.row(align=True)
        op_row.scale_y = 1.5

        op_row.operator("poser.generate_base_rig", icon="POSE_HLT")
