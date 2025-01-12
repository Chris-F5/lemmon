#include <X11/Xlib.h>
#include <GL/glx.h>
//#include <GL/gl.h>

#define PY_SSIZE_T_CLEAN
#include <Python.h>

static Display *dpy;

static PyObject *display_callback;

static PyObject*
init(PyObject *self, PyObject *args)
{
    /*
    int n;
    if (!PyArg_ParseTuple(args, "i", &n))
        return NULL;
    */
    dpy = XOpenDisplay(NULL);
    if (!dpy) {
        PyErr_SetString(PyExc_Exception, "XOpenDisplay failed");
        return NULL;
    }
    int black_color = BlackPixel(dpy, DefaultScreen(dpy));
    int white_color = WhitePixel(dpy, DefaultScreen(dpy));

    GLint att[] = { GLX_RGBA, GLX_DEPTH_SIZE, 24, GLX_DOUBLEBUFFER, None };
    XVisualInfo *vi = glXChooseVisual(dpy, 0, att);
    if (vi == NULL) {
        PyErr_SetString(PyExc_Exception, "glXChooseVisual failed");
        return NULL;
    }
    Colormap cmap = XCreateColormap(dpy, DefaultRootWindow(dpy), vi->visual, AllocNone);

    XSetWindowAttributes swa;
    memset(&swa, 0, sizeof(swa));
    swa.colormap = cmap;
    swa.event_mask = ExposureMask | KeyPressMask;

    Window w = XCreateWindow(
        dpy, DefaultRootWindow(dpy),
        0, 0, 600, 600,
        0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa
    );
    GLXContext glc = glXCreateContext(dpy, vi, NULL, GL_TRUE);
    glXMakeCurrent(dpy, w, glc);
    /*
    Window w = XCreateSimpleWindow(
        dpy, DefaultRootWindow(dpy),
        0, 0, 200, 100,
        0, black_color, black_color
    );
    */

    XMapWindow(dpy, w);

    GC gc = XCreateGC(dpy, w, 0, NULL);
    XSetForeground(dpy, gc, white_color);

    for (;;) {
        XEvent e;
        XNextEvent(dpy, &e);
        if(e.type == Expose) {
            XWindowAttributes gwa;
            XGetWindowAttributes(dpy, w, &gwa);
            //glViewport(0, 0, gwa.width, gwa.height);
            //DrawAQuad();
            printf("1\n");
            if (display_callback != NULL) {
                printf("2\n");
                PyObject *arglist = Py_BuildValue("(ii)", gwa.width, gwa.height);
                PyObject_CallObject(display_callback, arglist);
                Py_DECREF(arglist);
            }
            glXSwapBuffers(dpy, w);
        } else if(e.type == KeyPress) {
            glXMakeCurrent(dpy, None, NULL);
            glXDestroyContext(dpy, glc);
            XDestroyWindow(dpy, w);
            XCloseDisplay(dpy);
            break;
        }
    }

    //XDrawLine(dpy, w, gc, 10, 60, 180, 20);
    //XFlush(dpy);

    Py_RETURN_NONE;
}

static PyObject*
set_display_callback(PyObject *self, PyObject *args)
{
    PyObject *new_callback;
    if (!PyArg_ParseTuple(args, "O:set_display_callback", &new_callback)) {
        return NULL;
    }
    if (!PyCallable_Check(new_callback)) {
        PyErr_SetString(PyExc_TypeError, "");
        return NULL;
    }
    printf("set\n");
    Py_XDECREF(display_callback);
    Py_XINCREF(new_callback);
    display_callback = new_callback;

    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"init", init, METH_VARARGS, "inits everything" },
    {"set_display_callback", set_display_callback, METH_VARARGS, "sets display callback" },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "lemmon_capi",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC
PyInit_lemmon_capi(void)
{
    return PyModule_Create(&module);
}

