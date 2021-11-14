
import os.path
import bpy
from bpy.types import PropertyGroup, WindowManager, AddonPreferences
from bpy.props import (StringProperty,
                       BoolProperty,
                       PointerProperty,
                       EnumProperty,
                       FloatVectorProperty,
                       IntProperty
                       )
from bpy.utils import previews, register_class, unregister_class
from . import globals
from . import utils
from . import screen_draw
import time
import math

def check_pointer(self, context):
    x, y, w, h = globals.CONTAINER_SIZE

    ha = (x, y, x+globals.HANDLE_WIDTH, y+h)
    ca = (ha[0]+globals.HANDLE_WIDTH, ha[1], ha[2]+w, ha[3])

    # Hover over handle
    if self.pointer.x >= ha[0] and self.pointer.x <= ha[2] \
    and self.pointer.y >= ha[1] and self.pointer.y <= ha[3]:
        hover = "HANDLE"

    # Hover over Asset
    elif self.pointer.x >= ca[0] and self.pointer.x <= ca[2] \
    and self.pointer.y >= ca[1] and self.pointer.y <= ca[3]:
        asset_index = math.floor((self.pointer.x-ca[0]) / globals.THUMBNAIL_SIZE) + self.asset_page
        globals.CURRENT_ASSET_INDEX = int(asset_index)
        hover = str(globals.CURRENT_ASSET_INDEX)
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

def toggle_library(self, context):
    globals.CONTAINER_SIZE = [globals.CONTAINER_SPACING, globals.CONTAINER_SPACING, 
                utils.get_3d_view_size()[0]-(globals.CONTAINER_SPACING*3), globals.THUMBNAIL_SIZE]

    globals.STARTING_WIDTH = globals.CONTAINER_WIDTH
    if self.open:
        globals.EXPAND_CLOSE = None
        if globals.EXPAND_START is None:
            globals.EXPAND_START = time.time()
    else:
        globals.EXPAND_START = None
        if globals.EXPAND_CLOSE is None:
            globals.EXPAND_CLOSE = time.time()

def reset_action():
    browser = bpy.context.window_manager.asset_browser
    
    browser.active_asset_index = -1
    browser.click = False
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
    browser.asset_page = 0
    browser.tooltip = ''
    reset_action()


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
    open: BoolProperty(name="Open Library", default=True, update=toggle_library)

    pointer: FloatVectorProperty(name="Cursor Pos", default=(0,0), subtype="COORDINATES", size=2, update=check_pointer)
    click: BoolProperty(name="Mouse Clicked", default=False)
    click_pos: FloatVectorProperty(name="Click Pos", default=(0,0), subtype="COORDINATES", size=2)

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
    

    asset_page : IntProperty(name="Asset Library Page", default=0)
    active_asset_index : IntProperty(name="Active Asset Index", default=-1)
    library = {"assets":[], "current":None}
    # thumbnails = previews.new()

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
    register_class(AssetLibraryPreference)
    register_class(AssetLibraryBrowser)
    WindowManager.asset_browser = PointerProperty(type=AssetLibraryBrowser)
    reset_library_properties()

def unregister():
    del WindowManager.asset_browser
    unregister_class(AssetLibraryBrowser)
    unregister_class(AssetLibraryPreference)