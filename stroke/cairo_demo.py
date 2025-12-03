import lemmon_capi
import cairo
import PIL.Image
import numpy as np
import fitz
import ctypes

import OpenGL
OpenGL.ERROR_ON_COPY = True
from OpenGL import GL, GLUT
import OpenGL.GL.shaders

class PDFPane:
    vao = None
    shader_program = None
    transform_uniform_location = None

    def __init__(self):
        if PDFPane.vao == None:
            PDFPane.gen_vao()
        if PDFPane.shader_program == None:
            PDFPane.gen_shader_program()
        self.gen_pdf_texture('./example.pdf', 0, 2)
        self.model = np.array([
            [self.page_width, 0.0,              0.0, 0.0],
            [0.0,             self.page_height, 0.0, 0.0],
            [0.0,             0.0,              1.0, 0.0],
            [0.0,             0.0,              0.0, 1.0],
        ], dtype=np.float32)
        self.view = np.identity(4, dtype=np.float32)
        self.view[0, 3] = -self.page_width//2
        self.view[1, 3] = -(self.page_height*2)//3

    @staticmethod
    def gen_vao():
        vertices = np.array([
            0.0, 0.0,
            1.0, 0.0,
            1.0, 1.0,
            0.0, 1.0
        ], dtype=np.float32)

        PDFPane.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(PDFPane.vao)

        vertex_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices, GL.GL_STATIC_DRAW)

        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, False, 0, ctypes.c_void_p(0))
        GL.glEnableVertexAttribArray(0)

        GL.glBindVertexArray(0)

    @staticmethod
    def gen_shader_program():
        with open('./pdf.vert') as f:

            vert_src = f.read()
        with open('./pdf.frag') as f:
            frag_src = f.read()
        vert_shader = GL.shaders.compileShader(vert_src, GL.GL_VERTEX_SHADER)
        frag_shader = GL.shaders.compileShader(frag_src, GL.GL_FRAGMENT_SHADER)
        PDFPane.shader_program = GL.shaders.compileProgram(vert_shader, frag_shader)
        PDFPane.transform_uniform_location = GL.glGetUniformLocation(
            PDFPane.shader_program, "transform"
        )

    def gen_pdf_texture(self, pdf_fname, page_no, resolution=1.0):
        doc = fitz.open(pdf_fname)
        page = doc.load_page(page_no)
        matrix = fitz.Matrix(resolution, resolution)
        pixmap = page.get_pixmap(matrix=matrix)
        assert pixmap.n == 3
        img = PIL.Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        img = img.transpose(PIL.Image.Transpose.FLIP_TOP_BOTTOM)
        img_array = np.array(img.convert("RGBA"), dtype=np.uint8)
        self.raw_width = img.width
        self.raw_height = img.height
        self.page_width = page.bound().width
        self.page_height = page.bound().height

        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, img.width, img.height, 0,
            GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, img_array
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        doc.close()

    def display(self, projection):
        GL.glUseProgram(PDFPane.shader_program)
        # GL.glActivateTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        transform = projection @ self.view @ self.model
        assert transform.dtype==np.float32
        GL.glUniformMatrix4fv(PDFPane.transform_uniform_location, 1, True, transform)
        GL.glBindVertexArray(PDFPane.vao)
        GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 4)


lemmon_capi.init_window("cairo demo")

WIDTH = 100
HEIGHT = 100
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
ctx = cairo.Context(surface)

ctx.set_source_rgba(0.5, 0, 0.5, 0.5)
ctx.paint()

ctx.set_source_rgba(0, 1, 0, 1)
ctx.arc(50, 50, 50, 0, 2*3.14159)
ctx.fill()
surface.write_to_png("example.png")

buf = surface.get_data()
img_np = np.ndarray(shape=(HEIGHT, WIDTH, 4),
                    dtype=np.uint8,
                    buffer=buf)
print(img_np)
# img = PIL.Image.frombuffer("RGBA", (WIDTH, HEIGHT), buf, "raw", "BGRA", 0, 1)
# img = img.transpose(PIL.Image.FLIP_TOP_BOTTOM)
# img_np = np.array(img, dtype=np.uint8)
texture = GL.glGenTextures(1)
GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, WIDTH, HEIGHT, 0,
                GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, img_np)
GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

def load_texture(path):
    img = PIL.Image.open(path).transpose(PIL.Image.FLIP_TOP_BOTTOM).convert('RGBA')
    img_data = np.array(img, dtype=np.uint8)

    texture_id = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)

    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, img.width, img.height, 0,
                 GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, img_data)

    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

    return texture_id

texture = load_texture("example.png")

pdf = PDFPane()

def get_proj():
    transform = np.identity(4, dtype=np.float32)
    transform[0][3] = -0
    transform[1][3] = -0
    scale = np.identity(4, dtype=np.float32)
    scale[0][0] = 3.0 / WIDTH
    scale[1][1] = 3.0 / HEIGHT
    return scale @ transform

def display_callback():
    GL.glEnable(GL.GL_BLEND)
    GL.glClearColor(0.0, 0.0, 0.2, 0.5)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT, GL.GL_DEPTH_BUFFER_BIT)

    GL.glBindTexture(GL.GL_TEXTURE_2D, texture)

    proj = get_proj()
    pdf.draw(proj)


def button_down_callback(btn):
    lemmon_capi.quit_window()


lemmon_capi.set_display_callback(display_callback)
lemmon_capi.set_button_down_callback(button_down_callback)
lemmon_capi.main_loop()
print("DONE")
