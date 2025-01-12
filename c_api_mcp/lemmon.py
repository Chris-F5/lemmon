import lemmon_capi

import OpenGL
OpenGL.ERROR_ON_COPY = True
from OpenGL import GL, GLUT
import OpenGL.GL.shaders


def display(width, height):
    print(width, height)
    GL.glViewport(0, 0, width, height)
    GL.glClearColor(0.0, 0.0, 0.5, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)


lemmon_capi.set_display_callback(display)
lemmon_capi.init(3)
print("DONE")
