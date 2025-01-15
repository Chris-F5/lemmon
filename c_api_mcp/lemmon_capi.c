#include "X11/extensions/XI2.h"
#include <X11/Xlib.h>
#include <X11/extensions/XInput2.h>
#include <GL/glx.h>
//#include <GL/gl.h>

#define PY_SSIZE_T_CLEAN
#include <Python.h>

static Display *dpy;
static XVisualInfo *vi;
static Colormap cmap;
static Window w;
static GLXContext glc;

static PyObject *display_callback;
static PyObject *reshape_callback;
static PyObject *motion_callback;

int quit;

static void
list_devices(void)
{
    int count, i, c, b;
    char *type;
    XIDeviceInfo *devices;
    XIButtonClassInfo *bc;
    XIValuatorClassInfo *vc;

    devices = XIQueryDevice(dpy, XIAllDevices, &count);
    for (i = 0; i < count; i++) {
        printf("%d %d %d %s\n",
            devices[i].deviceid,
            devices[i].enabled,
            devices[i].num_classes,
            devices[i].name);
        for (c = 0; c < devices[i].num_classes; c++) {
            switch (devices[i].classes[c]->type) {
            case XIKeyClass:
                type = "Key";
                break;
            case XIButtonClass:
                type = "Button";
                break;
            case XIValuatorClass:
                type = "Valuator";
                break;
            case XITouchClass:
                type = "Touch";
                break;
            case XIScrollClass:
                type = "Scroll";
                break;
            default:
                type = "UNKNOWN";
            }
            printf("  %d %s\n", devices[i].classes[c]->sourceid, type);
            if (devices[i].classes[c]->type == XIButtonClass) {
                bc = (XIButtonClassInfo *)devices[i].classes[c];
                for (b = 0; b < bc->num_buttons; b++) {
                    if (bc->labels[b] == 0)
                        printf("    NONE\n");
                    else
                        printf("    %s %d\n", XGetAtomName(dpy, bc->labels[b]), bc->state.mask[0]);
                }
            }
            if (devices[i].classes[c]->type == XIValuatorClass) {
                vc = (XIValuatorClassInfo *)devices[i].classes[c];
                if (vc->label == 0)
                    printf("    NONE\n");
                else
                    printf("    %s %d %f %f\n", XGetAtomName(dpy, vc->label), vc->number, vc->min, vc->max);
            }
        }
    }
    XIFreeDeviceInfo(devices);
}

static PyObject*
init_window(PyObject *self, PyObject *args)
{
    GLint att[] = { GLX_RGBA, GLX_DEPTH_SIZE, 24, GLX_DOUBLEBUFFER, None };
    XSetWindowAttributes swa;
    char *title;

    if (!PyArg_ParseTuple(args, "s:init", &title))
        return NULL;

    dpy = XOpenDisplay(NULL);
    if (!dpy) {
        PyErr_SetString(PyExc_Exception, "XOpenDisplay failed");
        return NULL;
    }

    vi = glXChooseVisual(dpy, 0, att);
    if (vi == NULL) {
        PyErr_SetString(PyExc_Exception, "glXChooseVisual failed");
        return NULL;
    }

    cmap = XCreateColormap(dpy, DefaultRootWindow(dpy), vi->visual, AllocNone);

    memset(&swa, 0, sizeof(swa));
    swa.colormap = cmap;
    swa.event_mask = ExposureMask | KeyPressMask | KeyReleaseMask;

    w = XCreateWindow(
        dpy, DefaultRootWindow(dpy),
        0, 0, 600, 600,
        0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa
    );
    glc = glXCreateContext(dpy, vi, NULL, GL_TRUE);
    glXMakeCurrent(dpy, w, glc);

    XMapWindow(dpy, w);
    XStoreName(dpy, w, title);

    unsigned char xi_mask[(XI_LASTEVENT + 7) / 8] = { 0 };
    XISetMask(xi_mask, XI_DeviceChanged);
    XISetMask(xi_mask, XI_ButtonPress);
    XISetMask(xi_mask, XI_ButtonRelease);
    XISetMask(xi_mask, XI_Motion);

    XIEventMask input_event_mask;
    input_event_mask.deviceid = XIMasterPointer;
    input_event_mask.mask_len = sizeof(xi_mask);
    input_event_mask.mask = xi_mask;

    XISelectEvents(dpy, w, &input_event_mask, 1);

    XFlush(dpy);

    list_devices();

    Py_RETURN_NONE;
}

static PyObject*
main_loop(PyObject *self, PyObject *args)
{
    XEvent e;
    XWindowAttributes gwa;
    for (;;) {
        while (XPending(dpy)) {
            XNextEvent(dpy, &e);
            if(e.type == Expose) { /* should use resize not expose */
                XGetWindowAttributes(dpy, w, &gwa);
                if (reshape_callback != NULL) {
                    PyObject *arglist = Py_BuildValue("(ii)", gwa.width, gwa.height);
                    PyObject_CallObject(reshape_callback, arglist);
                    Py_DECREF(arglist);
                }
            } else if(e.type == KeyPress) {
                printf("press %d %d %d\n", e.xkey.keycode, e.xkey.state, e.xkey.send_event);
            } else if(e.type == KeyRelease) {
                printf("release %d %d\n", e.xkey.keycode, e.xkey.state);
            } else if (e.type == GenericEvent && e.xcookie.evtype == XI_Motion) {
                XGetEventData(dpy, &e.xcookie);
                XIDeviceEvent *dev_event = e.xcookie.data;
                int left_click, right_click;
                left_click = (dev_event->buttons.mask_len > 0 && XIMaskIsSet(dev_event->buttons.mask, Button1));
                right_click = (dev_event->buttons.mask_len > 0 && XIMaskIsSet(dev_event->buttons.mask, Button3));

                double pressure = 0.0;
                //printf("%f %f\n");
                if(XIMaskIsSet(dev_event->valuators.mask, 2)) {
                    pressure = dev_event->valuators.values[2];
                //    printf("+ %f\n", dev_event->valuators.values[2]);
                }
                if (motion_callback != NULL) {
                    PyObject *arglist;
                    arglist = Py_BuildValue("(ddd)", dev_event->event_x, dev_event->event_y, pressure);
                    PyObject_CallObject(motion_callback, arglist);
                    Py_DECREF(arglist);
                }
            } else if (e.type == GenericEvent && e.xcookie.evtype == XI_ButtonPress) {
                XGetEventData(dpy, &e.xcookie);
                XIDeviceEvent *dev_event = e.xcookie.data;
                printf("%d\n", dev_event->detail);
            } else if (e.type == GenericEvent && e.xcookie.evtype == XI_DeviceChanged) {
                XGetEventData(dpy, &e.xcookie);
                XIDeviceChangedEvent *change_event = e.xcookie.data;
                printf("change\n");
            }
        }
        if (quit) {
            break;
        }
        if (display_callback != NULL) {
            PyObject_CallObject(display_callback, NULL);
            glXSwapBuffers(dpy, w);
        }
    }
    glXMakeCurrent(dpy, None, NULL);
    glXDestroyContext(dpy, glc);
    XDestroyWindow(dpy, w);
    XCloseDisplay(dpy);
    Py_RETURN_NONE;
}


static PyObject*
quit_window(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ":quit")) {
        return NULL;
    }
    quit = 1;
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
    Py_XDECREF(display_callback);
    Py_XINCREF(new_callback);
    display_callback = new_callback;

    Py_RETURN_NONE;
}

static PyObject*
set_reshape_callback(PyObject *self, PyObject *args)
{
    PyObject *new_callback;
    if (!PyArg_ParseTuple(args, "O:set_reshape_callback", &new_callback)) {
        return NULL;
    }
    if (!PyCallable_Check(new_callback)) {
        PyErr_SetString(PyExc_TypeError, "");
        return NULL;
    }
    Py_XDECREF(reshape_callback);
    Py_XINCREF(new_callback);
    reshape_callback = new_callback;

    Py_RETURN_NONE;
}

static PyObject*
set_motion_callback(PyObject *self, PyObject *args)
{
    PyObject *new_callback;
    if (!PyArg_ParseTuple(args, "O:set_motion_callback", &new_callback)) {
        return NULL;
    }
    if (!PyCallable_Check(new_callback)) {
        PyErr_SetString(PyExc_TypeError, "");
        return NULL;
    }
    Py_XDECREF(motion_callback);
    Py_XINCREF(new_callback);
    motion_callback = new_callback;

    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"init_window", init_window, METH_VARARGS, "creates window and opengl context" },
    {"main_loop", main_loop, METH_VARARGS, "starts main loop" },
    {"quit_window", quit_window, METH_VARARGS, "ends main loop" },
    {"set_display_callback", set_display_callback, METH_VARARGS, "sets display callback" },
    {"set_reshape_callback", set_reshape_callback, METH_VARARGS, "sets reshape callback" },
    {"set_motion_callback", set_motion_callback, METH_VARARGS, "sets motion callback" },
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

