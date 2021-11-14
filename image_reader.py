import zlib
import struct
import os
import time
import threading
import bgl

# PNG Data Reader
# Taken from https://pyokagan.name/blog/2019-10-14-png/

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'

class PNG:
    width = 0
    height = 0
    bit_depth = 8
    bytes_per_pixel = 4 # RGBA
    gamma = 2.2

    def __init__(self, file_path):
        self.raw_data = None
        self.file_path = file_path

    def generate_buffer(self):
        if self.raw_data is None:
            self.read_data()
            self.flip_vertical()
        self.id = bgl.Buffer(bgl.GL_INT, [1])

        bgl.glGenTextures(1, self.id)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.id.to_list()[0])

        image_size = self.width * self.height * self.bytes_per_pixel
        self.buffer = bgl.Buffer(bgl.GL_FLOAT, [image_size], self.as_float())
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA, self.width, self.height, 0, bgl.GL_RGBA, bgl.GL_FLOAT, self.buffer)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)

    def read_data(self):
        if os.path.isfile(self.file_path):
            self.load()        
        else:
            raise(self.file_path, "is not a file")
    
    def flip_vertical(self):
        array = self.build_array()
        flipped = []
        for row in array:
            flipped.insert(0, row)
        data = []
        for row in flipped:
            for col in row:
                r,g,b,a = col
                data.extend([r,g,b,a])
        self.raw_data = data

    def as_byte(self):
        return self.raw_data
        # return self.build_array(self.raw_data, self.width, self.height, self.bytes_per_pixel)

    def as_float(self):
        floats = [(d/255)**(self.gamma) for d in self.raw_data]
        return floats
        # return self.build_array(floats, self.width, self.height, self.bytes_per_pixel)

    def load(self):
        with open(self.file_path, 'rb') as f:
            start = time.time()
            if f.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
                raise Exception('Invalid PNG Signature')

            chunks = []
            while True:
                chunk_type, chunk_data = self.read_chunk(f)
                chunks.append((chunk_type, chunk_data))
                if chunk_type == b'IEND':
                    break
            
            _, IHDR_data = chunks[0] # IHDR is always first chunk
            self.width, self.height, self.bit_depth, colort, compm, filterm, interlacem = struct.unpack('>IIBBBBB', IHDR_data)
            
            self.raw_data = [0] * self.width * self.height * self.bytes_per_pixel
            # PNG Format Check
            if compm != 0:
                raise Exception('invalid compression method')
            if filterm != 0:
                raise Exception('invalid filter method')
            if colort != 6:
                raise Exception('we only support truecolor with alpha')
            if self.bit_depth != 8:
                raise Exception('we only support a bit depth of 8')
            if interlacem != 0:
                raise Exception('we only support no interlacing')

            IDAT_data = b''.join(chunk_data for chunk_type, chunk_data in chunks if chunk_type == b'IDAT')
            IDAT_data = zlib.decompress(IDAT_data)

            raw_data = []
            stride = self.width * self.bytes_per_pixel
            
            def raw_data_a(r, c):
                return raw_data[r * stride + c - self.bytes_per_pixel] if c >= self.bytes_per_pixel else 0

            def raw_data_b(r, c):
                return raw_data[(r-1) * stride + c] if r > 0 else 0

            def raw_data_c(r, c):
                return raw_data[(r-1) * stride + c - self.bytes_per_pixel] if r > 0 and c >= self.bytes_per_pixel else 0

            i = 0
            for r in range(self.height): # for each row
                filter_type = IDAT_data[i] # first byte of row is filter type
                i += 1
                for c in range(stride): # for each byte in row
                    Filt_x = IDAT_data[i]
                    i += 1
                    if filter_type == 0: # None
                        raw_data_x = Filt_x
                    elif filter_type == 1: # Sub
                        raw_data_x = Filt_x + raw_data_a(r, c)
                    elif filter_type == 2: # Up
                        raw_data_x = Filt_x + raw_data_b(r, c)
                    elif filter_type == 3: # Average
                        raw_data_x = Filt_x + (raw_data_a(r, c) + raw_data_b(r, c)) // 2
                    elif filter_type == 4: # Paeth
                        raw_data_x = Filt_x + self.PaethPredictor(raw_data_a(r, c), raw_data_b(r, c), raw_data_c(r, c))
                    else:
                        raise Exception('unknown filter type: ' + str(filter_type))
                    raw_data.append(raw_data_x & 0xff) # truncation to byte

            print(f"Reading {os.path.basename(self.file_path)} takes {time.time()-start:.02f} seconds")
            self.raw_data = raw_data
            self.generate_buffer()

    def read_chunk(self, f):
        chunk_length, chunk_type = struct.unpack('>I4s', f.read(8))
        chunk_data = f.read(chunk_length)
        chunk_expected_crc, = struct.unpack('>I', f.read(4))
        chunk_actual_crc = zlib.crc32(chunk_data, zlib.crc32(struct.pack('>4s', chunk_type)))
        if chunk_expected_crc != chunk_actual_crc:
            raise Exception('chunk checksum failed')
        return chunk_type, chunk_data

    def PaethPredictor(self, a, b, c):
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            Pr = a
        elif pb <= pc:
            Pr = b
        else:
            Pr = c
        return Pr

    def build_array(self):
        pixels = []
        pixel = []
        for d in self.raw_data:
            pixel.append(d)
            if len(pixel) == self.bytes_per_pixel:
                pixels.append(pixel)
                pixel = []

        rows = []
        row = []
        for pixel in pixels:
            row.append(pixel)
            if len(row) == self.width:
                rows.append(row)
                row = []
        
        return rows
