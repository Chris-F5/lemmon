#include <X11/Xlib.h>

#define PY_SSIZE_T_CLEAN
#include <Python.h>

static Display *dsp;

static PyObject*
init(PyObject *self, PyObject *args)
{
    /*
    int n;
    if (!PyArg_ParseTuple(args, "i", &n))
        return NULL;
    */
    dsp = XOpenDisplay(NULL);
    if (!dsp) {
        PyErr_SetString(PyExc_Exception, "XOpenDisplay failed");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"init", init, METH_VARARGS, "inits everything" },
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

