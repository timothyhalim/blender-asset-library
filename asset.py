import os
import json
from datetime import datetime
from .image import IMG

DATETIMEFORM = "%Y/%m/%d %H:%M:%S"

MATERIAL_TEMPLATE = os.path.normpath(os.path.join(__file__, "..", "template", "Material.blend"))

ASSET_TYPES = {
    "MDL": {
            "label" : "Model",
            "desc" : "Model Asset",
            "icon" : "MONKEY",
            "supported" : False
        },
    "MTL": {
            "label" : "Material",
            "desc" : "Material Asset",
            "icon" : "MATERIAL",
            "supported" : True
        },
    "LGT": {
            "label" : "Light",
            "desc" : "Light and HDRI Asset",
            "icon" : "LIGHT_DATA",
            "supported" : False
        },
    "PTC": {
            "label" : "Particle",
            "desc" : "Particle and FX Asset",
            "icon" : "PARTICLES",
            "supported" : False
        },
}

ASSET_SORT_BY = (
        ("id", "Id", ""),
        ("name", "Name", ""),
        ("author", "Author", ""),
        ("created", "Date Created", ""),
        ("updated", "Date Modified", ""),
    )

class Asset():
    def __init__(
                    self, id="", name="", author="", 
                    created=datetime.now(), updated=datetime.now(), 
                    image_file="", type="", tags=[], 
                    objects=[], collections=[], materials=[],
                    bbox_max=[0,0,0], bbox_min=[0,0,0],
                    json_file=""
                ):
        if json_file:
            self.from_json(json_file)
        else:
            self.id = id
            self.name = name
            self.author = author
            self.created = created if isinstance(created, datetime) else datetime.strptime(created, DATETIMEFORM)
            self.updated = updated if isinstance(updated, datetime) else datetime.strptime(updated, DATETIMEFORM)
            self.image_file = image_file
            self.type = type
            self.tags = tags
            self.objects = [o.name for o in objects]
            self.collections = collections
            self.materials = materials
            self.bbox_min = bbox_max
            self.bbox_max = bbox_min
    
    def jsonfiy(self):
        data = {
            "id" : self.id,
            "name" : self.name,
            "author" : self.author,
            "created" : self.created.strftime(DATETIMEFORM),
            "updated" : self.updated.strftime(DATETIMEFORM),
            "image_file" : self.image_file,
            "type" : self.type,
            "tags" : self.tags,
            "objects" : [o if isinstance(o, str) else o.name for o in self.objects],
            "collections" : [c if isinstance(c, str) else c.name for c in self.collections],
            "materials" : [m if isinstance(m, str) else m.name for m in self.materials],
            "bbox_min" : self.bbox_min,
            "bbox_max" : self.bbox_max,
        }
        return data

    def from_json(self, json_file):
        with open(json_file, "r") as f:
            data = json.load(f)
        self.id = data.get('id', "")
        self.name = data.get('name', "")
        self.author = data.get('author', "")
        created = data.get('created', datetime.now()) 
        self.created = created if isinstance(created, datetime) else datetime.strptime(created, DATETIMEFORM)
        updated = data.get('updated', datetime.now()) 
        self.updated = updated if isinstance(updated, datetime) else datetime.strptime(updated, DATETIMEFORM)
        self.image_file = data.get('image_file', None)
        self.type = data.get('type', "Unknown")
        self.tags = data.get('tags', ["No Tag"])
        self.objects = data.get('objects', [])
        self.collections = data.get('collections', [])
        self.materials = data.get('materials', [])
        self.bbox_min = data.get('bbox_max', [0,0,0])
        self.bbox_max = data.get('bbox_min', [0,0,0])
        return self

    def to_json(self, json_file):
        folder = os.path.dirname(json_file)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        if os.path.isdir(folder):
            with open(json_file, "w") as f:
                f.write(json.dumps(self.jsonfiy(), indent=4))

    def update_thumbnail(self, image):
        print("Update", self)
        self.thumbnail = image

    @staticmethod
    def get_library():
        import bpy # Imported here so it didn't cause error on multiprocessing
        
        lib = []
        
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        library = addon_prefs.library_path

        for asset_id in sorted(os.listdir(library)):
            asset_data = os.path.join(library, asset_id, f"{asset_id}_data.json")
            if os.path.isfile(asset_data):
                asset = Asset()
                asset.from_json(asset_data)
                thumbnail = os.path.join(library, asset.id, asset.image_file)
                if os.path.isfile(thumbnail):
                    asset.thumbnail = IMG(thumbnail)
                lib.append(asset)
                
        return lib

    #             # Generate Asset Type Property
    #             Asset.add_asset_type(browser, asset.type)

    #             # Generate Asset Tags Property
    #             for tag in asset.tags:
    #                 if not hasattr(WindowManager, f"{asset.type}_{tag}"):
    #                     setattr(WindowManager, f"{asset.type}_{tag}", BoolProperty(default=True))
    #                 browser.asset_data["categories"][asset.type][tag] = getattr(WindowManager, f"{asset.type}_{tag}")

    # @staticmethod
    # def add_asset_type(browser, asset_type):
    #     if not hasattr(WindowManager, asset_type):
    #         setattr(WindowManager, asset_type, BoolProperty(default=True))
    #     if not hasattr(WindowManager, f"{asset_type}_expand"):
    #         setattr(WindowManager, f"{asset_type}_expand", BoolProperty(default=False))  
    #     browser.asset_data["categories"][asset_type] = browser.asset_data["categories"].get(asset_type, {})
