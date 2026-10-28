import numpy as np
import pytest

import transform as tf


@pytest.mark.parametrize("n", [2, 4, 8, 128, 4096])
def test_power_of_two_true(n):
    assert tf.is_power_of_two(n)


@pytest.mark.parametrize("n", [-4, 0, 1, 3, 6, 100])
def test_power_of_two_false(n):
    assert not tf.is_power_of_two(n)


@pytest.mark.parametrize("n", [2, 4, 8, 16, 64, 128, 256])
def test_orthonormal(n):
    t = tf.build_matrix(n)
    assert np.allclose(t @ t.T, np.eye(n), atol=1e-12)
    assert np.allclose(t.T @ t, np.eye(n), atol=1e-12)
    assert tf.verify_orthonormal(t).ok


def test_round_trip_and_parseval():
    n = 128
    t = tf.build_matrix(n)
    x = np.random.default_rng(0).uniform(-1, 1, n)
    y = tf.forward(t, x)
    assert np.allclose(tf.inverse(t, y), x, atol=1e-12)
    assert tf.energy(y) == pytest.approx(tf.energy(x), rel=1e-12)


def test_row0_constant_and_row_cycles():
    t = tf.build_matrix(128)
    assert np.allclose(t[0], t[0, 0])
    # row 5 = 2.5 cycles of cosine -> 5 sign changes
    assert int(np.sum(np.diff(np.sign(t[5])) != 0)) == 5


def test_matches_scipy():
    scipy_fft = pytest.importorskip("scipy.fft")
    x = np.random.default_rng(1).normal(size=64)
    y = tf.forward(tf.build_matrix(64), x)
    assert np.allclose(y, scipy_fft.dct(x, type=2, norm="ortho"), atol=1e-12)


def test_verify_detects_non_orthonormal():
    assert not tf.verify_orthonormal(np.ones((4, 4))).ok
