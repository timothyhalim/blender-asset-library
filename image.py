import bgl
from .PIL import Image

class IMG():
    gamma = 2.2
    def __init__(self, image_file):
        self.file_path = image_file
        self.image = Image.open(image_file)
        self.width, self.height = self.image.size
        self.channels = len(self.image.getbands())
        self.depth = self.image.mode
        self.pixels = list(self.image.getdata())
        self.flip_vertical()

    def generate_buffer(self):
        self.id = bgl.Buffer(bgl.GL_INT, [1])

        bgl.glGenTextures(1, self.id)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.id.to_list()[0])

        image_size = self.width * self.height * self.channels
        self.buffer = bgl.Buffer(bgl.GL_FLOAT, [image_size], self.as_float())
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA, self.width, self.height, 0, bgl.GL_RGBA, bgl.GL_FLOAT, self.buffer)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)

    def build_array(self):
        rows = []
        row = []
        for pixel in self.pixels:
            row.append(pixel)
            if len(row) == self.width:
                rows.append(row)
                row = []
        
        return rows

    def flip_vertical(self):
        flipped = list(reversed(self.build_array()))
        data = [d for row in flipped for pixel in row for d in pixel]
        self.raw_data = data

    def as_float(self):
        floats = [(d/255)**self.gamma for d in self.raw_data]
        return floats