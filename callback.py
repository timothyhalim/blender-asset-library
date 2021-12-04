from . import draw
from . import utils
import time

def draw_container(x, y, w, h, color, ui):
    current_time = float(str(time.time())[6:])
    if ui.asset_container_opening:
        ui.asset_container_closing = 0
        scale = min((current_time-ui.asset_container_opening)/ui.asset_container_anim_duration, 1)
        offset = -ui.asset_container_starting_width/w
        if scale >= 1:
            ui.asset_container_opening = 0
    elif ui.asset_container_closing:
        ui.asset_container_opening = 0
        scale = 1-min((current_time-ui.asset_container_closing)/ui.asset_container_anim_duration, 1)
        offset = 1-ui.asset_container_starting_width/w
        if scale <= 0:
            ui.asset_container_closing = 0
    else:
        scale = int(ui.open)
        offset = 0
    scale = min(max(scale-offset, 0), 1)
    ui.asset_container_width = w * scale

    draw.rect_2d(
        x, y, ui.asset_container_width, h, 
        color
    )

def draw_callback_2d(self, context):
    ui = context.window_manager.asset_browser

    x, y = ui.asset_container_pos
    w, h = ui.asset_container_max_width, ui.asset_thumbnail_size
    hover = ui.asset_container_color_hover
    normal = ui.asset_container_color
    handle = ui.asset_handle_width
    thumb = ui.asset_thumbnail_size

    # For animation Purpose
    draw_container(
        x+handle, y, w-handle, h, 
        (0,0,0,0), ui
    )
    
    # Draw Asset Thumbnails

    assets = ui.library["assets"][ui.asset_page:]
    
    asset_count = int(ui.asset_container_width / thumb) \
                + int((ui.asset_container_width / thumb) % 1 > 0)
    for i in range(asset_count):
        if ui.asset_container_width < handle or i > len(assets)-1:
            break
        asset = assets[i]
        
        pos_x = x+(i*thumb)+handle
        space_left = thumb + (x + handle + ui.asset_container_width) \
                   - (pos_x + thumb) - handle
        if pos_x + thumb > x + handle + ui.asset_container_width - handle:
            draw.rect_2d(pos_x, y, space_left, thumb, normal)
            draw.image(
                asset.thumbnail, pos_x, y, space_left, 
                thumb, crop=(0,0,space_left/thumb, 1)
            )
            break
        
        draw.rect_2d(
            pos_x, y, thumb, thumb, 
            hover if ui.hover_on == str(i+ui.asset_page) else normal
        )
        if ui.hover_on == str(i+ui.asset_page):
            continue

        draw.image(asset.thumbnail, pos_x, y, thumb, thumb)
        for _ in range(3):
            draw.text(asset.name, pos_x+5, y+7, int(thumb/6), color=(0,0,0,0.25))
        draw.text(asset.name, pos_x+5, y+7, int(thumb/6), color=(1,1,1,0.25))
    
    # Draw Scrollbar 
    if ui.asset_container_width > handle\
    and asset_count < len(assets)+1: 
        draw.rect_2d(
            pos_x+space_left, y, handle, h, 
            hover if ui.hover_on == "SCROLL" else (0.1, 0.1, 0.1, 1)
        )
        draw.text("▼ ▼ ▼", pos_x+space_left+handle-5, y+5, handle-6, rotation=90)

    # Draw Hover Asset
    # Make sure above other asset
    if ui.hover_on.isdigit() \
    and int(ui.hover_on) >= 0 \
    and int(ui.hover_on) < len(ui.library["assets"]):
        asset = ui.library["assets"][int(ui.hover_on)]
        hover_i = ui.library["assets"].index(asset)-ui.asset_page
        hover_x = x+(hover_i*thumb)+handle
        thumb_scale = thumb * 1.05 
        dif = (thumb_scale - thumb)/2
        draw.image(asset.thumbnail, hover_x-dif, y-dif, thumb_scale, thumb_scale)
        for _ in range(3):
            draw.text(asset.name, hover_x+5, y+7, int(thumb_scale/6), color=(0,0,0,1))
        draw.text(asset.name, hover_x+5, y+7, int(thumb_scale/6))
        

    # Draw Handle
    draw.rect_2d(
        x, y, handle, h, 
        hover if ui.hover_on == "HANDLE" else (0.1, 0.1, 0.1, 1)
    )
    draw.text("<" if ui.open else ">", x+handle/3, y+h-15, handle-6)
    draw.text("Asset", x+handle-5, y+5, handle-6, rotation=90)

    # Draw Drag
    if ui.drag and ui.active_asset_index >= 0 :
        drag_icon_size = 20 #thumb/3
        mouse = ui.pointer
        asset = ui.library["assets"][ui.active_asset_index]
        if asset.type in ["Material"]:
            # Asset Thumbnail
            draw.image(
                asset.thumbnail,
                mouse.x+20, mouse.y-drag_icon_size-1,
                drag_icon_size, drag_icon_size
            )

            # Asset Name
            for i in range(3):
                draw.text(
                    asset.name, 
                    mouse.x+20+drag_icon_size, mouse.y-drag_icon_size+6, 
                    12, color=(0,0,0,1)
                )
            draw.text(
                asset.name, 
                mouse.x+20+drag_icon_size, mouse.y-drag_icon_size+6, 
                12
            )
            
            # Hover Object
            for i in range(3):
                draw.text(
                    ui.hover_object, 
                    mouse.x, mouse.y+5, 
                    12, color=(0,0,0,1)
                )
            draw.text(
                ui.hover_object, 
                mouse.x, mouse.y+5, 
                12
            )

    if (ui.drag or ui.click) and ui.click_on.isdigit():
        draw.image(
            ui.icons["grab"],
            ui.pointer.x, ui.pointer.y-20, 
            20, 20
        )
    elif ui.open:
        if ui.hover_on.isdigit():
            draw.image(
                ui.icons["hand"],
                ui.pointer.x, ui.pointer.y-20, 
                20, 20
            )

def draw_callback_3d(self, context):
    ''' Draw snapped bbox while dragging and in the future other blenderkit related stuff. '''
    ui = context.window_manager.asset_browser
    if ui.drag and ui.active_asset_index >= 0 :
        asset = ui.library["assets"][ui.active_asset_index]
        if asset.type in ["Model"]:
            draw.draw_bbox(ui.bbox_location, ui.bbox_rotation, ui.bbox_min, ui.bbox_max)
