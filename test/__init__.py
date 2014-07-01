import numpy as np
from numpy.testing import assert_array_equal

from xray import utils, DataArray
from xray.variable import as_variable
from xray.pycompat import PY3, unittest

try:
    import scipy
    has_scipy = True
except ImportError:
    has_scipy = False

try:
    import pydap.client
    has_pydap = True
except ImportError:
    has_pydap = False

try:
    import netCDF4
    has_netCDF4 = True
except ImportError:
    has_netCDF4 = False


def requires_scipy(test):
    return test if has_scipy else unittest.skip('requires scipy')(test)


def requires_pydap(test):
    return test if has_pydap else unittest.skip('requires pydap.client')(test)


def requires_netCDF4(test):
    return test if has_netCDF4 else unittest.skip('requires netCDF4')(test)


def decode_string_data(data):
    if data.dtype.kind == 'S':
        return np.core.defchararray.decode(data, 'utf-8', 'replace')
    return data


def data_allclose_or_equiv(arr1, arr2, rtol=1e-05, atol=1e-08):
    if any(arr.dtype.kind == 'S' for arr in [arr1, arr2]):
        arr1 = decode_string_data(arr1)
        arr2 = decode_string_data(arr2)
    exact_dtypes = ['M', 'm', 'O', 'U']
    if any(arr.dtype.kind in exact_dtypes for arr in [arr1, arr2]):
        return utils.array_equiv(arr1, arr2)
    else:
        return utils.allclose_or_equiv(arr1, arr2, rtol=rtol, atol=atol)


class TestCase(unittest.TestCase):
    if PY3:
        # Python 3 assertCountEqual is roughly equivalent to Python 2
        # assertItemsEqual
        def assertItemsEqual(self, first, second, msg=None):
            return self.assertCountEqual(first, second, msg)

    def assertVariableEqual(self, v1, v2):
        assert as_variable(v1).equals(v2), (v1, v2)

    def assertVariableIdentical(self, v1, v2):
        assert as_variable(v1).identical(v2), (v1, v2)

    def assertVariableAllClose(self, v1, v2, rtol=1e-05, atol=1e-08):
        self.assertEqual(v1.dimensions, v2.dimensions)
        allclose = data_allclose_or_equiv(
            v1.values, v2.values, rtol=rtol, atol=atol)
        assert allclose, (v1.values, v2.values)

    def assertVariableNotEqual(self, v1, v2):
        self.assertFalse(as_variable(v1).equals(v2))

    def assertArrayEqual(self, a1, a2):
        assert_array_equal(a1, a2)

    def assertDatasetEqual(self, d1, d2):
        # this method is functionally equivalent to `assert d1 == d2`, but it
        # checks each aspect of equality separately for easier debugging
        self.assertEqual(sorted(d1.variables, key=str),
                         sorted(d2.variables, key=str))
        for k in d1:
            v1 = d1.variables[k]
            v2 = d2.variables[k]
            self.assertVariableEqual(v1, v2)

    def assertDatasetIdentical(self, d1, d2):
        # this method is functionally equivalent to `assert d1.identical(d2)`,
        # but it checks each aspect of equality separately for easier debugging
        assert utils.dict_equiv(d1.attrs, d2.attrs), (d1.attrs, d2.attrs)
        self.assertEqual(sorted(d1.variables, key=str),
                         sorted(d2.variables, key=str))
        for k in d1:
            v1 = d1.variables[k]
            v2 = d2.variables[k]
            assert v1.identical(v2), (v1, v2)

    def assertDatasetAllClose(self, d1, d2, rtol=1e-05, atol=1e-08):
        self.assertEqual(sorted(d1.variables, key=str),
                         sorted(d2.variables, key=str))
        for k in d1:
            v1 = d1.variables[k]
            v2 = d2.variables[k]
            self.assertVariableAllClose(v1, v2, rtol=rtol, atol=atol)

    def assertIndexesEqual(self, d1, d2):
        self.assertEqual(sorted(d1.indexes), sorted(d2.indexes))
        for k in d1.indexes:
            v1 = d1.indexes[k]
            v2 = d2.indexes[k]
            self.assertVariableEqual(v1, v2)

    def assertDataArrayEqual(self, ar1, ar2):
        self.assertVariableEqual(ar1, ar2)
        self.assertIndexesEqual(ar1, ar2)

    def assertDataArrayIdentical(self, ar1, ar2):
        self.assertEqual(ar1.name, ar2.name)
        self.assertDatasetIdentical(ar1.dataset, ar2.dataset)

    def assertDataArrayAllClose(self, ar1, ar2, rtol=1e-05, atol=1e-08):
        self.assertVariableAllClose(ar1, ar2, rtol=rtol, atol=atol)
        self.assertIndexesEqual(ar1, ar2)


class ReturnItem(object):
    def __getitem__(self, key):
        return key


def source_ndarray(array):
    """Given an ndarray, return the base object which holds its memory, or the
    object itself.
    """
    base = array.base
    if base is None:
        base = array
    return base
