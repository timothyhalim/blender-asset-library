from importlib import reload
import time

from bpy.types import Panel, Operator
from bpy.utils import register_class, unregister_class
import bpy

from . import callback
from . import properties
from . import utils
from . import globals
from .asset import Asset
from .image import IMG
reload(properties)
reload(callback)
reload(utils)
    
class Library_PT_BasePanel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Asset Library"
    
    @classmethod
    def poll(cls, context):
        return True

class Library_PT_AssetImport(Library_PT_BasePanel):
    bl_label = "Library"
    bl_idname = "Library_PT_AssetImport"

    def draw(self, context):
        ui = context.window_manager.asset_browser
        layout = self.layout
        if not ui.initialized:
            layout.operator(Library_OT_Panel.bl_idname)
        else:
            layout.prop(ui, "open", text="Library", icon='HIDE_OFF' if ui.open else "HIDE_ON")
            layout.prop(ui, "query", text="", icon='VIEWZOOM')

def Library_Header_Draw(self, context):
    '''Top bar menu in 3D view'''
    layout = self.layout
    ui = bpy.context.window_manager.asset_browser
    # the center snap menu is in edit and object mode if tool settings are off.
    if context.space_data.show_region_tool_header == True or context.mode[:4] not in ('EDIT', 'OBJE'):
        layout.separator_spacer()

    if not ui.initialized:
        layout.operator(Library_OT_Panel.bl_idname, text="Start Asset Library", icon="HIDE_ON")
    else:
        layout.prop(ui, "query", text="", icon='VIEWZOOM')
        layout.prop(ui, "open", text="", icon='HIDE_OFF' if ui.open else "HIDE_ON")
        
class Library_OT_Panel(Operator):
    bl_idname = "view3d.asset_library"
    bl_label = "Asset Library Panel"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    # tooltip: bpy.props.StringProperty(default='tooltip')

    # @classmethod
    # def description(cls, context, properties):
    #     return properties.tooltip

    def exit_modal(self, context):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
            context.window_manager.event_timer_remove(self.timer)
        except:
            pass
        properties.reset_library_properties()
        context.area.tag_redraw()

    def modal(self, context, event):
        ui = bpy.context.window_manager.asset_browser

        ui.pointer = [
            event.mouse_region_x,
            event.mouse_region_y
        ]
        # if event.type != "TIMER":
        #     print(event.type)

        if event.type in ["EVT_TWEAK_L", "EVT_TWEAK_M", "EVT_TWEAK_R"]:
            return {"RUNNING_MODAL"}

        if event.type == "ESC":
            print("ESC")
            self.exit_modal(context)
            return {"FINISHED"}

        if event.type == "F5":
            print("Refresh")
            ui.library["assets"] = Asset.get_library()

        if event.type in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")+["SPACE"]:
            if ui.hover_on.isdigit():
                if time.time() - globals.LAST_KEY_TIME > 0.2:
                    globals.LAST_KEY_TIME = time.time()

                    ui.query += " " if event.type == "SPACE" else event.type

                return {"RUNNING_MODAL"}

        if event.type in ["BACK_SPACE"]:
            if ui.hover_on.isdigit():
                if time.time() - globals.LAST_KEY_TIME > 0.2:
                    globals.LAST_KEY_TIME = time.time()
                    ui.query = ui.query[:-1]
                return {"RUNNING_MODAL"}

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                ui.click = True
                ui.drag_length = 0
                ui.click_pos = [
                    event.mouse_region_x,
                    event.mouse_region_y
                ]
                ui.click_on = ui.hover_on
                context.area.tag_redraw()

                return {"PASS_THROUGH"}

            elif event.value == 'RELEASE':
                if ui.drag:
                    if ui.active_asset_index >= 0:
                        asset = ui.library["assets"][ui.active_asset_index]
                        if asset.type in ["Material"]:
                            if ui.hover_object:
                                o = bpy.data.objects.get(ui.hover_object, None)
                                print(o)
                                
                if ui.hover_on == "HANDLE":
                    ui.open = not(ui.open)
                                
                properties.reset_action()
                context.area.tag_redraw()
                return {"PASS_THROUGH"}


        if event.type in ['WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'TRACKPADPAN']:
            if ui.hover_on.isdigit():
                if event.type == 'WHEELUPMOUSE':
                    ui.asset_page = max(0, ui.asset_page-1)
                if event.type == 'WHEELDOWNMOUSE':
                    ui.asset_page = min(len(ui.library["assets"])-1, ui.asset_page+1)
                return {"RUNNING_MODAL"}
        
        if event.type == 'MOUSEMOVE':
            if (ui.hover_on.isdigit() and ui.open) \
            or (ui.drag and ui.click_on.isdigit()):
                context.window.cursor_set("NONE")
            else:
                context.window.cursor_set("DEFAULT")

            if ui.click and ui.open:
                ui.drag_length = abs(ui.click_pos.x - ui.pointer.x) \
                               + abs(ui.click_pos.y - ui.pointer.y)
                if ui.drag_length > 5:
                    ui.drag = True

                    context.area.tag_redraw()
                    return {"RUNNING_MODAL"}

        context.area.tag_redraw()
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        ui = bpy.context.window_manager.asset_browser
        ui.library["assets"] = Asset.get_library()
        if not ui.initialized:
            self.timer = context.window_manager.event_timer_add(
                0.1, window=context.window)
            self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(callback.draw_callback_2d, (self, context), 'WINDOW', 'POST_PIXEL')
            self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(callback.draw_callback_3d, (self, context), 'WINDOW', 'POST_VIEW')
            
            properties.reset_library_properties()
            context.window_manager.modal_handler_add(self)
            ui.initialized = True
            ui.open = True
            context.area.tag_redraw()

        return {"RUNNING_MODAL"}
        
    def execute(self, context):
        return {'RUNNING_MODAL'}



def startup():
    context = bpy.context.copy()
    # bpy.ops.view3d.asset_library("INVOKE_DEFAULT")
    print(bpy.context.scene)
    import os
    if globals.CURSOR_HAND is None:
        globals.CURSOR_HAND = IMG(os.path.join(__file__, "..", "resource", "Hand.png"))
    if globals.CURSOR_GRAB is None:
        globals.CURSOR_GRAB = IMG(os.path.join(__file__, "..", "resource", "Grab.png"))

def register():
    register_class(Library_OT_Panel)
    register_class(Library_PT_AssetImport)
    bpy.types.VIEW3D_MT_editor_menus.append(Library_Header_Draw)

    # Run on startup
    from threading import Timer
    Timer(2, startup, ()).start()

def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(Library_Header_Draw)
    unregister_class(Library_OT_Panel)
    unregister_class(Library_PT_AssetImport)
    