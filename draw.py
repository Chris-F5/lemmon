import numpy as np
import ctypes

import OpenGL
OpenGL.ERROR_ON_COPY = True
from OpenGL import GL, GLUT
import OpenGL.GL.shaders


def window_reshape_callback(w, h):
    global width, height
    width = w
    height = h
    GL.glViewport(0, 0, width, height)


def mouse_motion_callback(x, y):
    global points
    points = np.concatenate((points, [2*x/width-1, -2*y/height+1, 0.0]), dtype=np.float32)


def display_callback():
    global program, points

    vert_buffer = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vert_buffer)
    assert points.dtype == np.float32
    GL.glBufferData(GL.GL_ARRAY_BUFFER, points, GL.GL_STREAM_DRAW)
    GL.glEnableVertexAttribArray(0)
    GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, 0, ctypes.c_void_p(0))

    GL.glClearColor(0.0, 0.0, 0.2, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    GL.glUseProgram(program)
    GL.glDrawArrays(GL.GL_POINTS, 0, len(points)//3)
    GLUT.glutSwapBuffers()


width = 500
height = 500

points = np.array([], dtype=np.float32)

GLUT.glutInit()
GLUT.glutInitDisplayMode(GLUT.GLUT_RGBA)
GLUT.glutInitWindowSize(width, height)
win = GLUT.glutCreateWindow("draw.py")
GL.glViewport(0, 0, width, height)

with open('basic.vert') as f:
    vert_src = f.read()
with open('basic.frag') as f:
    frag_src = f.read()
program = GL.shaders.compileProgram(
    GL.shaders.compileShader(vert_src, GL.GL_VERTEX_SHADER),
    GL.shaders.compileShader(frag_src, GL.GL_FRAGMENT_SHADER),
)

vertex_array = GL.glGenVertexArrays(1)
GL.glBindVertexArray(vertex_array)

GLUT.glutReshapeFunc(window_reshape_callback)
GLUT.glutMotionFunc(mouse_motion_callback)
GLUT.glutDisplayFunc(display_callback)
GLUT.glutIdleFunc(display_callback)
GLUT.glutMainLoop()
print("DONE")
