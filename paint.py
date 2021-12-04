import bgl
import blf
from mathutils import Euler
import gpu
from gpu_extras.batch import batch_for_shader

def rect_2d(x, y, width, height, color):
    xmax = x + width
    ymax = y + height
    points = [[x, y],  # [x, y]
              [x, ymax],  # [x, y]
              [xmax, ymax],  # [x, y]
              [xmax, y],  # [x, y]
              ]
    indices = ((0, 1, 2), (2, 3, 0))

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": points}, indices=indices)

    shader.bind()
    shader.uniform_float("color", color)
    bgl.glEnable(bgl.GL_BLEND)
    batch.draw(shader)

def line_2d(x1, y1, x2, y2, width, color):
    coords = (
        (x1, y1), (x2, y2))

    indices = (
        (0, 1),)
    bgl.glEnable(bgl.GL_BLEND)

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def line_3d(vertices, indices, color):
    bgl.glEnable(bgl.GL_BLEND)

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def rect_3d(coords, color):
    indices = [(0, 1, 2), (2, 3, 0)]
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)
    shader.uniform_float("color", color)
    batch.draw(shader)

def bbox(location, rotation, bbox_min, bbox_max, progress=None, color=(0, 1, 0, 1)):
    rotation = Euler(rotation)

    smin = Vector(bbox_min)
    smax = Vector(bbox_max)
    v0 = Vector(smin)
    v1 = Vector((smax.x, smin.y, smin.z))
    v2 = Vector((smax.x, smax.y, smin.z))
    v3 = Vector((smin.x, smax.y, smin.z))
    v4 = Vector((smin.x, smin.y, smax.z))
    v5 = Vector((smax.x, smin.y, smax.z))
    v6 = Vector((smax.x, smax.y, smax.z))
    v7 = Vector((smin.x, smax.y, smax.z))

    arrowx = smin.x + (smax.x - smin.x) / 2
    arrowy = smin.y - (smax.x - smin.x) / 2
    v8 = Vector((arrowx, arrowy, smin.z))

    vertices = [v0, v1, v2, v3, v4, v5, v6, v7, v8]
    for v in vertices:
        v.rotate(rotation)
        v += Vector(location)

    lines = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5],
             [2, 6], [3, 7], [0, 8], [1, 8]]
    line_3d(vertices, lines, color)
    
    if progress != None:
        color = (color[0], color[1], color[2], .2)
        progress = progress * .01
        vz0 = (v4 - v0) * progress + v0
        vz1 = (v5 - v1) * progress + v1
        vz2 = (v6 - v2) * progress + v2
        vz3 = (v7 - v3) * progress + v3
        rects = (
            (v0, v1, vz1, vz0),
            (v1, v2, vz2, vz1),
            (v2, v3, vz3, vz2),
            (v3, v0, vz0, vz3))
        for r in rects:
            rect_3d(r, color)

def image(image, x=0, y=0, width=100, height=100, crop=(0, 0, 1, 1)):
    if not hasattr(image, "pixels"): return
    if not hasattr(image, "id"): image.generate_buffer()
    if hasattr(image, "id"): 
        coords = [
            (x, y), (x + width, y),
            (x, y + height), (x + width, y + height)]

        uvs = [(crop[0], crop[1]),
            (crop[2], crop[1]),
            (crop[0], crop[3]),
            (crop[2], crop[3]),
            ]

        indices = [(0, 1, 2), (2, 1, 3)]

        shader = gpu.shader.from_builtin('2D_IMAGE')
        batch = batch_for_shader(shader, 'TRIS',
                                {"pos": coords,
                                "texCoord": uvs},
                                indices=indices)

        # in case someone disabled it before
        bgl.glEnable(bgl.GL_BLEND)

        # bind texture to image unit 0
        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.id.to_list()[0])

        shader.bind()
        # tell shader to use the image that is bound to image unit 0
        shader.uniform_int("image", 0)
        batch.draw(shader)

        bgl.glDisable(bgl.GL_TEXTURE_2D)

def text(text, x, y, size, rotation=0, color=(1, 1, 1, 1), ralign = False):
    font_id = 1
    rotation = (rotation/360) * (2 * 22.0/7) 

    blf.color(font_id, color[0], color[1], color[2], color[3])
    blf.size(font_id, size, 72)
    if ralign:
        width, height = blf.dimensions(font_id, text)
        x-=width

    blf.position(font_id, x, y, 0)
    blf.enable(font_id, blf.ROTATION)
    blf.rotation(font_id, rotation)
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 5, 0, 0, 0, 1)
    for i in range(-1, 1):
        for j in range(-1, 1):
            blf.shadow_offset(font_id, i, j)
    blf.draw(font_id, text)

    # Restore
    blf.rotation(font_id, 0)
    blf.disable(font_id, blf.ROTATION)
    blf.disable(font_id, blf.SHADOW)
