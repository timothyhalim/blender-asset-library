import bpy

def get_3d_view_size():
    if hasattr(bpy.context, "screen"):
        screen = bpy.context.screen

        for area in screen.areas:
            if area.type == "VIEW_3D":
                for region in area.regions:
                    if region.type == "WINDOW":
                        return (region.width, region.height)
    return (0, 0)