from . import screen_draw
from . import globals
import time

def draw_container(x, y, w, h, color):
    if globals.EXPAND_START is not None:
        scale = min((time.time()-globals.EXPAND_START)/globals.ANIMATION_DURATION, 1)
        offset = -globals.STARTING_WIDTH/w
    elif globals.EXPAND_CLOSE is not None:
        scale = 1-min((time.time()-globals.EXPAND_CLOSE)/globals.ANIMATION_DURATION, 1)
        offset = 1-globals.STARTING_WIDTH/w
    else:
        scale = 0
        offset = 0
    scale = min(max(scale-offset, 0), 1)

    globals.CONTAINER_WIDTH = w * scale

    screen_draw.draw_rect(
        x, y, globals.CONTAINER_WIDTH, h, 
        color
    )

def draw_callback_2d(self, context):
    ''' Draw snapped bbox while dragging and in the future other blenderkit related stuff. '''
    ui = context.window_manager.asset_browser

    x, y, w, h = globals.CONTAINER_SIZE
    hover = globals.BG_COLOR_HOVER
    normal = globals.BG_COLOR

    # For animation Purpose
    draw_container(
        x+globals.HANDLE_WIDTH, y, w-globals.HANDLE_WIDTH, h, 
        (0,0,0,0)
    )

    # Draw Asset Thumbnails
    for i, asset in enumerate(ui.library["assets"][ui.asset_page:]):
        pos_x = x+(i*globals.THUMBNAIL_SIZE)+globals.HANDLE_WIDTH
        if pos_x < x + globals.HANDLE_WIDTH + globals.CONTAINER_WIDTH:
            screen_draw.draw_rect(
                pos_x, y, globals.THUMBNAIL_SIZE, globals.THUMBNAIL_SIZE, 
                hover if ui.hover_on == str(i+ui.asset_page) else normal
            )
            thumbsize = globals.THUMBNAIL_SIZE * 1.05 if ui.hover_on == str(i+ui.asset_page) else globals.THUMBNAIL_SIZE
            dif = (thumbsize - globals.THUMBNAIL_SIZE)/2
            screen_draw.draw_image(asset.thumbnail, pos_x-dif, y-dif, thumbsize, thumbsize)
            for i in range(3):
                # Shadow, 10 times to make it thick
                screen_draw.draw_text(asset.name, pos_x+5, y+7, 14, color=(0,0,0,1))
            screen_draw.draw_text(asset.name, pos_x+5, y+7, 14)

    # Draw Handle
    screen_draw.draw_rect(
        x, y, globals.HANDLE_WIDTH, h, 
        hover if ui.hover_on == "HANDLE" else (0.1, 0.1, 0.1, 1)
    )
    screen_draw.draw_text("<" if ui.open else ">", x+5, y+h-15, 14)
    screen_draw.draw_text("Asset", x+globals.HANDLE_WIDTH-5, y+5, 14, rotation=90)

    # Draw Drag
    if ui.drag and ui.active_asset_index >= 0 :
        drag_icon_size = globals.THUMBNAIL_SIZE/3
        mouse = ui.pointer
        asset = ui.library["assets"][ui.active_asset_index]
        if asset.type in ["Material"]:
            # Asset Thumbnail
            screen_draw.draw_image(
                asset.thumbnail,
                mouse.x+20, mouse.y-20-drag_icon_size/2, 
                drag_icon_size, drag_icon_size
            )

            # Asset Name
            for i in range(3):
                screen_draw.draw_text(
                    asset.name, 
                    mouse.x+20+drag_icon_size, mouse.y-20, 
                    14, color=(0,0,0,1)
                )
            screen_draw.draw_text(
                asset.name, 
                    mouse.x+20+drag_icon_size, mouse.y-20, 
                14
            )
            
            # Hover Object
            for i in range(3):
                screen_draw.draw_text(
                    ui.hover_object, 
                    mouse.x-10, mouse.y+5, 
                    14, color=(0,0,0,1)
                )
            screen_draw.draw_text(
                ui.hover_object, 
                mouse.x-10, mouse.y+5, 
                14
            )

    if ui.drag or (ui.hover_on.isdigit() and ui.click):
        screen_draw.draw_image(
            globals.CURSOR_GRAB,
            ui.pointer.x, ui.pointer.y-20, 
            20, 20
        )
    else:
        if ui.hover_on.isdigit():
            screen_draw.draw_image(
                globals.CURSOR_HAND,
                ui.pointer.x, ui.pointer.y-20, 
                20, 20
            )

def draw_callback_3d(self, context):
    ''' Draw snapped bbox while dragging and in the future other blenderkit related stuff. '''
    ui = context.window_manager.asset_browser
    if ui.drag and ui.active_asset_index >= 0 :
        asset = ui.library["assets"][ui.active_asset_index]
        if asset.type in ["Model"]:
            screen_draw.draw_bbox(ui.bbox_location, ui.bbox_rotation, ui.bbox_min, ui.bbox_max)
