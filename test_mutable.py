"""

"""


__author__ = 'Yngve Mardal Moe'
__email__ = 'yngve.m.moe@gmail.com'


import pytest
from mutable import mutable


@pytest.fixture
def one_trap():
    def f(x, a=[]):
        a.append(x)
        return a
    return f


@pytest.fixture
def one_kwonly_trap():
    def f(x, *, a=[]):
        a.append(x)
        return a
    return f

@pytest.fixture
def two_traps():
    def f(x, a=[], b=[]):
        a.append(x)
        b.append(x)
        return a, b
    return f


@pytest.fixture
def one_mutable(one_trap):
    return mutable(one_trap)


@pytest.fixture
def one_mutable_kwonly_arg(one_kwonly_trap):
    return mutable(one_kwonly_trap)
    

@pytest.fixture
def one_mutable_one_trap(two_traps):
    return mutable('a')(two_traps)


@pytest.fixture
def two_mutables(two_traps):
    return mutable()(two_traps)


def test_different_ids_returned(one_mutable):
    a = one_mutable(1)
    b = one_mutable(2)
    assert a is not b


def test_different_values_returned(one_mutable):
    a = one_mutable(1)
    b = one_mutable(2)
    assert a != b


def test_kwonly_different_ids_returned(one_mutable_kwonly_arg):
    a = one_mutable_kwonly_arg(1)
    b = one_mutable_kwonly_arg(2)
    assert a is not b
    

def test_kwonly_different_values_returned(one_mutable_kwonly_arg):
    a = one_mutable_kwonly_arg(1)
    b = one_mutable_kwonly_arg(2)
    assert a != b


def test_one_mutable_one_trap_changes_ids_correctly(one_mutable_one_trap):
    a1, b1 = one_mutable_one_trap(1)
    a2, b2 = one_mutable_one_trap(2)
    assert a1 is not a2
    assert b1 is b2


def test_one_mutable_one_trap_changes_vals_correctly(one_mutable_one_trap):
    a1, b1 = one_mutable_one_trap(1)
    a2, b2 = one_mutable_one_trap(2)
    assert a1 != a2
    assert b1 == b2


def test_two_mutables_changes_ids_correctly(two_mutables):
    a1, b1 = two_mutables(1)
    a2, b2 = two_mutables(2)
    assert a1 is not a2
    assert b1 is not b2


def test_two_mutables_changes_vals_correctly(two_mutables):
    a1, b1 = two_mutables(1)
    a2, b2 = two_mutables(2)
    assert a1 != a2
    assert b1 != b2
