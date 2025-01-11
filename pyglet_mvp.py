import numpy as np
import ctypes
import pyglet
#import pyglet.gl as GL

import OpenGL
OpenGL.ERROR_ON_COPY = True
from OpenGL import GL, GLUT
import OpenGL.GL.shaders

import fitz
import PIL.Image


class PDFPane:
    vao = None
    shader_program = None

    def __init__(self):
        if PDFPane.vao == None:
            PDFPane.gen_vao()
        if PDFPane.shader_program == None:
            PDFPane.gen_shader_program()
        self.gen_pdf_texture('example.pdf', 0, 2)
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
        with open('pdf.vert') as f:
            vert_src = f.read()
        with open('pdf.frag') as f:
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


class MainWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pdf = PDFPane()
        assert len(pyglet.input.get_tablets()) == 1
        tablet = pyglet.input.get_tablets()[0].open(self)
        tablet.push_handlers(
            on_enter=self.on_tablet_enter,
            on_leave=self.on_tablet_leave,
            on_motion=self.on_tablet_motion,
        )
        print(tablet)

    def on_tablet_enter(self, cursor):
        print(cursor, "ENTER")

    def on_tablet_leave(self, cursor):
        print(cursor, "LEAVE")

    def on_tablet_motion(self, cursor, x, y, pressure, *_):
        print(x, y, pressure)

    def on_draw(self):
        GL.glClearColor(0.0, 0.0, 0.2, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        proj = np.identity(4, dtype=np.float32)
        proj[0][0] = proj[1][1] = 3e-3
        self.pdf.display(proj)

    def on_resize(self, width, height):
        GL.glViewport(0, 0, width, height)

if __name__ == '__main__':
    window = MainWindow(500, 500, "test_window", resizable=True)
    pyglet.app.run()
