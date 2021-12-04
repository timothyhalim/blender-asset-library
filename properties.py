import os.path
import sys
import time
from multiprocessing import Pool, Manager

in_blender = False
if sys.modules.get("bpy"):
    in_blender = True
    import bpy
    from bpy.types import PropertyGroup, WindowManager, AddonPreferences
    from bpy.props import (StringProperty,
                        BoolProperty,
                        PointerProperty,
                        EnumProperty,
                        FloatVectorProperty,
                        IntProperty,
                        FloatProperty
                        )
    from bpy.utils import register_class, unregister_class
    from . import utils
    from . import screen_draw
    
from .image import IMG

def print_error(error):
    print(error)

def load_thumbnail(image, data):
    data.value += image.load()

def asset_page_callback(self, context):
    if self.asset_page >= 0 :
        thumb = self.asset_thumbnail_size
        asset_count = int(self.asset_container_width / thumb) \
                    + int((self.asset_container_width / thumb) % 1 > 0)
        assets = self.library["assets"][self.asset_page:self.asset_page+asset_count+1]
        images = [asset.thumbnail for asset in assets 
                  if not asset.thumbnail.loaded 
                  and not asset.thumbnail.is_loading]
        
        if images:
            start = time.time()
            
            manager = Manager()
            pool = Pool()
            for image in images:
                image.pixels = manager.Value('i', [])
                image.is_loading = True
                image.loaded = False
                pool.apply_async(load_thumbnail, args=(image, image.pixels), error_callback=print_error) 
            pool.close()
        
            print(f"Processed in {time.time() - start} secs")
        

def cursor_move_callback(self, context):
    x, y = self.asset_container_pos
    w, h = self.asset_container_width, self.asset_thumbnail_size
    handle = self.asset_handle_width
    thumb = self.asset_thumbnail_size

    ha = (x, y, x+handle, y+h)
    ca = (ha[0]+handle, ha[1], ha[2]+w, ha[3])

    # Hover over handle
    if self.pointer.x >= ha[0] and self.pointer.x <= ha[2] \
    and self.pointer.y >= ha[1] and self.pointer.y <= ha[3]:
        hover = "HANDLE"

    # Hover over Scroll
    elif self.pointer.x >= ca[2]-(handle*2) and self.pointer.x <= ca[2] \
    and self.pointer.y >= ha[1] and self.pointer.y <= ha[3]:
        hover = "SCROLL"

    # Hover over Asset
    elif self.pointer.x >= ca[0] and self.pointer.x <= ca[2] \
    and self.pointer.y >= ca[1] and self.pointer.y <= ca[3]:
        asset_index = int((self.pointer.x-ca[0]) / thumb) + self.asset_page
        if asset_index > len(self.library["assets"])-1:
            asset_index = "-1"
        self.asset_hover_index = int(asset_index)
        hover = str(self.asset_hover_index)
        if not self.drag:
            self.active_asset_index = int(asset_index)

    # Hover outside of 3d view
    elif self.pointer.x < 0 \
    or self.pointer.x > context.region.width \
    or self.pointer.y < 0 \
    or self.pointer.y > context.region.height:
        hover = "OUTSIDE"
        reset_action()
        
    # Inside of 3d view
    else:
        hover = "INSIDE"
        
    self.hover_on = hover
    if self.drag:
        hit, location, normal, rotation, \
        face_index, object, matrix = screen_draw.mouse_raycast(
            context, self.pointer.x, self.pointer.y
        )
        
        self.bbox_location = location
        self.bbox_min = [-1, -.5, 0] 
        self.bbox_max = [1, .5, 1]
        self.bbox_normal = normal
        self.bbox_rotation = rotation
        self.hover_object = object.name if object else ""
    else:
        self.bbox_location = [0,0,0]
        self.bbox_min = [0,0,0]
        self.bbox_max = [0,0,0]
        self.bbox_normal = [0,0,0]
        self.bbox_rotation = [0,0,0]
        self.hover_object = ""

def toggle_library_callback(self, context):
    self.asset_container_starting_width = self.asset_container_width
    current_time = float(str(time.time())[6:])
    
    if self.open:
        if self.asset_container_max_width < 100:
            self.asset_container_max_width = utils.get_3d_view_size()[0]
            
            for r in context.area.regions:
                if r.type == 'UI':
                    if r.width > 1:
                        self.asset_container_max_width -= self.asset_handle_width
                    break
        self.asset_container_opening = current_time
        self.asset_container_closing = 0
    else:
        self.asset_container_closing = current_time
        self.asset_container_opening = 0

def reset_action():
    browser = bpy.context.window_manager.asset_browser
    
    browser.active_asset_index = 0
    browser.click = False
    browser.click_on = ""
    browser.click_pos = [0, 0]

    browser.drag = False
    browser.drag_length = 0

    browser.bbox_location = [0,0,0]
    browser.bbox_min = [0,0,0]
    browser.bbox_max = [0,0,0]
    browser.bbox_normal = [0,0,0]
    browser.bbox_rotation = [0,0,0]

def reset_library_properties():
    browser = bpy.context.window_manager.asset_browser
    
    browser.initialized = False
    browser.open = False
    browser.asset_page = -1
    browser.tooltip = ''
    browser.query = ""
    reset_action()

if in_blender:
    class AssetLibraryBrowser(PropertyGroup):
        query : StringProperty(
                name="Search",
                description="Query to search",
                default=""
                )

        # sort_by : EnumProperty(
        #         name="Sort by",
        #         items=get_sorting_options,
        #         description="Sort ",
        #         )

        # sort_reverse : BoolProperty(default=False)

        tooltip: StringProperty(
            name="Tooltip",
            description="asset preview info",
            default="")

        # Toggle Drawing
        initialized: BoolProperty(name="Library Initialized", default=False)
        open: BoolProperty(name="Open Library", default=True, update=toggle_library_callback)

        pointer: FloatVectorProperty(name="Cursor Pos", default=(0,0), subtype="COORDINATES", size=2, update=cursor_move_callback)
        click: BoolProperty(name="Mouse Clicked", default=False)
        click_pos: FloatVectorProperty(name="Click Pos", default=(0,0), subtype="COORDINATES", size=2)
        click_on: StringProperty(name="Click On", default="")

        hover_on: StringProperty(name="Hover on widget", default="")
        hover_object: StringProperty(name="Hover on Object")

        # Drag draw
        drag: BoolProperty(name="Dragging", default=False)
        drag_length: IntProperty(name="Drag length", default=0)

        # BBox Placement
        bbox_location: FloatVectorProperty(name="BBox Location", default=(0, 0, 0))
        bbox_min: FloatVectorProperty(name="BBox Min", default=(0, 0, 0))
        bbox_max: FloatVectorProperty(name="BBox Max", default=(0, 0, 0))
        bbox_normal: FloatVectorProperty(name="BBox Normal", default=(0, 0, 0))
        bbox_rotation: FloatVectorProperty(name="BBox Rotation", default=(0, 0, 0), subtype='QUATERNION')
        
        # Appearance Settings
        asset_handle_width : IntProperty(name="Asset Handle Width", default=20, min=20 )
        asset_handle_click_pos : FloatVectorProperty(name="Cursor Pos", default=(0,0), subtype="COORDINATES", size=2)
        asset_thumbnail_size : IntProperty(name="Asset Thumbnail Size", default=100, min=80 )
        asset_container_max_width : FloatProperty(name="Asset Container Width", default=0)
        asset_container_pos : FloatVectorProperty(name="Asset Container Position", default=(0,0), subtype="COORDINATES", size=2)
        asset_container_color : FloatVectorProperty(name="Asset Container Color", default=(.2, .2, .2, .5), min=0, max=1, subtype="COLOR", size=4)
        asset_container_color_hover : FloatVectorProperty(name="Asset Container Hover Color", default=(.4, .4, .4, .5), min=0, max=1, subtype="COLOR", size=4)
        asset_container_anim_duration : FloatProperty(name="Asset Container Animation Duration in second", default=0.5)
        
        # Animation Data
        asset_container_width : FloatProperty(name="Asset Container Width", default=0)
        asset_container_starting_width : FloatProperty(name="Asset Container Starting Width", default=-1)
        asset_container_opening : FloatProperty(name="Asset Container Opening Width", default=-1)
        asset_container_closing : FloatProperty(name="Asset Container Closing Width", default=-1)

        # Panel Interaction
        icons = {
            "hand" : IMG(os.path.normpath(os.path.join(__file__, "..", "resource", "Hand.png"))),
            "grab" : IMG(os.path.normpath(os.path.join(__file__, "..", "resource", "Grab.png")))
        }

        # Asset 
        asset_hover_index : IntProperty(name="Asset Hover Index", default=0)
        asset_page : IntProperty(name="Asset Library Page", default=-1, update=asset_page_callback)
        active_asset_index : IntProperty(name="Active Asset Index", default=-1)
        library = {"assets":[], "current":None}


    class AssetLibraryPreference(AddonPreferences):
        bl_idname = __package__

        library_path: StringProperty(
            name="Library Path",
            default=os.path.normpath(os.path.join(__file__, "..", "assets")),
            subtype='FILE_PATH',
        )

        def draw(self, context):
            layout = self.layout
            layout.prop(self, "library_path")

def register():
    if in_blender:
        register_class(AssetLibraryPreference)
        register_class(AssetLibraryBrowser)
        WindowManager.asset_browser = PointerProperty(type=AssetLibraryBrowser)
        reset_library_properties()

def unregister():
    if in_blender:
        del WindowManager.asset_browser
        unregister_class(AssetLibraryBrowser)
        unregister_class(AssetLibraryPreference)