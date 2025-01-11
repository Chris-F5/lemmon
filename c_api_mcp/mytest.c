#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject*
hello_world(PyObject *self, PyObject *args)
{
    int n;
    if (!PyArg_ParseTuple(args, "i", &n))
        return NULL;
    printf("%d\n", n*2);
    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"hello_world", hello_world, METH_VARARGS, "hello world" },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "mytest",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC
PyInit_mytest(void)
{
    return PyModule_Create(&module);
}
