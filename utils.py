import bpy
import mathutils
from mathutils import Vector
from bpy_extras import view3d_utils
import math



def get_3d_view_size():
    if hasattr(bpy.context, "screen"):
        screen = bpy.context.screen
        if hasattr(screen, "areas"):
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    for region in area.regions:
                        if region.type == "WINDOW":
                            return (region.width, region.height)
    return (0, 0)

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