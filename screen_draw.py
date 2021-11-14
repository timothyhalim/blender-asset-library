import bpy
import bgl
import blf
import mathutils
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
import math

def draw_rect(x, y, width, height, color):
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

def draw_line2d(x1, y1, x2, y2, width, color):
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

def draw_lines(vertices, indices, color):
    bgl.glEnable(bgl.GL_BLEND)

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def draw_rect_3d(coords, color):
    indices = [(0, 1, 2), (2, 3, 0)]
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)
    shader.uniform_float("color", color)
    batch.draw(shader)

def draw_bbox(location, rotation, bbox_min, bbox_max, progress=None, color=(0, 1, 0, 1)):
    rotation = mathutils.Euler(rotation)

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
    draw_lines(vertices, lines, color)
    
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
            draw_rect_3d(r, color)

def draw_image(image, x=0, y=0, width=100, height=100, crop=(0, 0, 1, 1)):
    if not hasattr(image, "id"):
        image.generate_buffer()
        
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

# def draw_image(x, y, width, height, image, crop=(0, 0, 1, 1)):
#     coords = [
#         (x, y), (x + width, y),
#         (x, y + height), (x + width, y + height)]

#     uvs = [(crop[0], crop[1]),
#            (crop[2], crop[1]),
#            (crop[0], crop[3]),
#            (crop[2], crop[3]),
#            ]

#     indices = [(0, 1, 2), (2, 1, 3)]

#     shader = gpu.shader.from_builtin('2D_IMAGE')
#     batch = batch_for_shader(shader, 'TRIS',
#                              {"pos": coords,
#                               "texCoord": uvs},
#                              indices=indices)

#     # send image to gpu if it isn't there already
#     if image.gl_load():
#         raise Exception()

#     # texture identifier on gpu
#     texture_id = image.bindcode

#     # in case someone disabled it before
#     bgl.glEnable(bgl.GL_BLEND)

#     # bind texture to image unit 0
#     bgl.glActiveTexture(bgl.GL_TEXTURE0)
#     bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture_id)

#     shader.bind()
#     # tell shader to use the image that is bound to image unit 0
#     shader.uniform_int("image", 0)
#     batch.draw(shader)

#     bgl.glDisable(bgl.GL_TEXTURE_2D)
#     return image

def draw_text(text, x, y, size, rotation=0, color=(1, 1, 1, 1), ralign = False):
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

def object_in_particle_collection(o):
    '''checks if an object is in a particle system as instance, to not snap to it and not to try to attach material.'''
    for p in bpy.data.particles:
        if p.render_type == 'COLLECTION':
            if p.instance_collection:
                for o1 in p.instance_collection.objects:
                    if o1 == o:
                        return True
        if p.render_type == 'COLLECTION':
            if p.instance_object == o:
                return True
    return False

def deep_ray_cast(depsgraph, ray_origin, vec):
    # this allows to ignore some objects, like objects with bounding box draw style or particle objects
    object = None
    # while object is None or object.draw
    has_hit, snapped_location, snapped_normal, face_index, object, matrix = bpy.context.scene.ray_cast(
        depsgraph, ray_origin, vec)
    empty_set = False, Vector((0, 0, 0)), Vector((0, 0, 1)), None, None, None
    if not object:
        return empty_set

    try_object = object

    while try_object and (try_object.display_type == 'BOUNDS' or object_in_particle_collection(try_object)):
        ray_origin = snapped_location + vec.normalized() * 0.0003
        try_has_hit, try_snapped_location, try_snapped_normal, try_face_index, try_object, try_matrix = bpy.context.scene.ray_cast(
            depsgraph, ray_origin, vec)
        if try_has_hit:
            # this way only good hits are returned, otherwise
            has_hit, snapped_location, snapped_normal, face_index, object, matrix = try_has_hit, try_snapped_location, try_snapped_normal, try_face_index, try_object, try_matrix
    if not (object.display_type == 'BOUNDS' or object_in_particle_collection(
            try_object)):  # or not object.visible_get()):
        return has_hit, snapped_location, snapped_normal, face_index, object, matrix
    return empty_set

def mouse_raycast(context, mx, my):
    r = context.region
    rv3d = context.region_data
    coord = mx, my

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(r, rv3d, coord)
    if rv3d.view_perspective == 'CAMERA' and rv3d.is_perspective == False:
        #  ortographic cameras don'w work with region_2d_to_origin_3d
        view_position = rv3d.view_matrix.inverted().translation
        ray_origin = view3d_utils.region_2d_to_location_3d(r, rv3d, coord, depth_location=view_position)
    else:
        ray_origin = view3d_utils.region_2d_to_origin_3d(r, rv3d, coord, clamp=1.0)

    ray_target = ray_origin + (view_vector * 1000000000)

    vec = ray_target - ray_origin
    has_hit, snapped_location, snapped_normal, face_index, object, matrix = deep_ray_cast(
        bpy.context.view_layer.depsgraph, ray_origin, vec)

    if has_hit:
        # backface snapping inversion
        if view_vector.angle(snapped_normal) < math.pi / 2:
            snapped_normal = -snapped_normal

        snapped_rotation = snapped_normal.to_track_quat('Z', 'Y').to_euler()
        # snapped_rotation.rotate_axis('Z', )

    else:
        plane_normal = (0, 0, 1)
        if math.isclose(view_vector.x, 0, abs_tol=1e-4) and math.isclose(view_vector.z, 0, abs_tol=1e-4):
            plane_normal = (0, 1, 0)
        elif math.isclose(view_vector.z, 0, abs_tol=1e-4):
            plane_normal = (1, 0, 0)

        snapped_location = mathutils.geometry.intersect_line_plane(ray_origin, ray_target, (0, 0, 0), plane_normal,
                                                                False)
        if snapped_location != None:
            has_hit = True
            snapped_normal = Vector((0, 0, 1))
            face_index = None
            object = None
            matrix = None
            snapped_rotation = snapped_normal.to_track_quat('Z', 'Y').to_euler()
            snapped_rotation.rotate_axis('Z', -math.pi/2)

    return has_hit, snapped_location, snapped_normal, snapped_rotation, face_index, object, matrix