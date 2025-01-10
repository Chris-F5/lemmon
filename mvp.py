import numpy as np
import ctypes

import OpenGL
OpenGL.ERROR_ON_COPY = True
from OpenGL import GL, GLUT
import OpenGL.GL.shaders

import fitz
import PIL.Image


def window_reshape_callback(w, h):
    global width, height
    width = w
    height = h
    GL.glViewport(0, 0, width, height)


def display_callback():
    global pdf

    GL.glClearColor(0.0, 0.0, 0.2, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    pdf.display()

    GLUT.glutSwapBuffers()


class PDFPane:
    vao = None
    shader_program = None

    def __init__(self):
        if PDFPane.vao == None:
            PDFPane.gen_vao()
        if PDFPane.shader_program == None:
            PDFPane.gen_shader_program()
        self.texture = self.gen_pdf_texture('example.pdf', 0)

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
        PDFPane.shader_program = GL.shaders.compileProgram(
            GL.shaders.compileShader(vert_src, GL.GL_VERTEX_SHADER),
            GL.shaders.compileShader(frag_src, GL.GL_FRAGMENT_SHADER),
        )

    def gen_pdf_texture(self, pdf_fname, page_no):
        doc = fitz.open(pdf_fname)
        page = doc.load_page(page_no)
        pixmap = page.get_pixmap()
        assert pixmap.n == 3
        img = PIL.Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        img = img.transpose(PIL.Image.Transpose.FLIP_TOP_BOTTOM)
        img_array = np.array(img, dtype=np.uint8)

        texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, pixmap.width, pixmap.height, 0,
            GL.GL_RGB, GL.GL_UNSIGNED_BYTE, img_array
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        doc.close()
        return texture

    def display(self):
        GL.glUseProgram(PDFPane.shader_program)
        #GL.glActivateTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glBindVertexArray(PDFPane.vao)
        GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 4)


width = 500
height = 500

GLUT.glutInit()
GLUT.glutInitDisplayMode(GLUT.GLUT_RGBA)
GLUT.glutInitWindowSize(width, height)
win = GLUT.glutCreateWindow("draw.py")
GL.glViewport(0, 0, width, height)

pdf = PDFPane()

GLUT.glutReshapeFunc(window_reshape_callback)
GLUT.glutDisplayFunc(display_callback)
GLUT.glutIdleFunc(display_callback)
GLUT.glutMainLoop()
print("DONE")
