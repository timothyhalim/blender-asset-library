import os
import time
try:
    import numpy as np
    import bgl
    from .PIL import Image
except:
    import sys
    mod = os.path.join(os.path.dirname(__file__), "PIL")
    if not mod in sys.path:
        sys.path.append(mod)
    from PIL import Image

class IMG():
    gamma = 2.2
    def __init__(self, image_file):
        self.file_path = image_file
        self.image = Image.open(image_file)
        self.width, self.height = self.image.size
        self.channels = len(self.image.getbands())
        self.depth = self.image.mode
        self.loaded = False
        self.is_loading = False
        
    # def __repr__(self):
    #     return os.path.basename(self.file_path)
        
    def load(self):
        return list(self.image.getdata())
        
    def generate_buffer(self):
        if hasattr(self, "pixels"):
            if hasattr(self.pixels, "value"):
                print(type(self.pixels))
                self.raw_data = self.pixels.value
            elif isinstance(self.pixels, list):
                self.raw_data = self.pixels
                
            if self.raw_data:
                self.is_loading = True
                
                # Pixel processing
                dt = np.dtype('uint8,uint8,uint8,uint8')
                self.pixels = np.array(self.raw_data, dtype=dt) # [(r,g,b,a), .. width*height]
                self.pixels = self.pixels.reshape(self.height, self.width) # Reshape to [(r,g,b,a), .. width],[(r,g,b,a), .. width], .. height]
                self.pixels = self.pixels.view(np.uint8) # Convert it to unstructured so can be calculated [[r,g,b,a]..]
                self.pixels = np.flip(self.pixels, 0) # Flip vertical
                
                # Creating OpenGL Buffer
                self.id = bgl.Buffer(bgl.GL_INT, [1])
                bgl.glGenTextures(1, self.id)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.id.to_list()[0])

                image_size = self.width * self.height * self.channels
                self.buffer = bgl.Buffer(bgl.GL_FLOAT, [image_size], self.as_float())
                bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA, self.width, self.height, 0, bgl.GL_RGBA, bgl.GL_FLOAT, self.buffer)
                bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
                bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)
                
                self.loaded = True
                self.is_loading = False
            
    def as_float(self):
        floats = self.pixels.flatten().astype(np.float32)/255
        floats = floats**self.gamma
        return floats