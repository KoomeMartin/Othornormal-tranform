"""Orthonormal DCT-II transform matrix and related maths (no GUI, no I/O)."""
from dataclasses import dataclass

import numpy as np

MIN_N = 2
MAX_N = 4096


def is_power_of_two(n: int) -> bool:
    return n >= MIN_N and (n & (n - 1)) == 0


def build_matrix(n: int) -> np.ndarray:
    """Orthonormal DCT-II: row 0 = sqrt(1/N); row k>=1 = sqrt(2/N)*cos(pi(2j+1)k/2N)."""
    k = np.arange(n).reshape(-1, 1)
    j = np.arange(n).reshape(1, -1)
    t = np.sqrt(2.0 / n) * np.cos(np.pi * (2 * j + 1) * k / (2 * n))
    t[0, :] = np.sqrt(1.0 / n)
    return t


def forward(t: np.ndarray, x: np.ndarray) -> np.ndarray:
    return t @ x


def inverse(t: np.ndarray, y: np.ndarray) -> np.ndarray:
    return t.T @ y


def energy(v) -> float:
    v = np.asarray(v, dtype=float)
    return float(np.sum(v * v))


@dataclass
class VerifyResult:
    ok: bool
    max_abs_error: float
    product: np.ndarray
    min_diag: float
    max_diag: float
    max_offdiag: float


def verify_orthonormal(t: np.ndarray, atol: float = 1e-10) -> VerifyResult:
    p = t @ t.T
    n = p.shape[0]
    err = np.abs(p - np.eye(n))
    diag = np.diag(p)
    off = p - np.diag(diag)
    return VerifyResult(
        ok=bool(np.allclose(p, np.eye(n), atol=atol, rtol=0.0)),
        max_abs_error=float(err.max()),
        product=p,
        min_diag=float(diag.min()),
        max_diag=float(diag.max()),
        max_offdiag=float(np.abs(off).max()),
    )


@dataclass
class RowSummary:
    k: int
    n: int
    max_value: float
    max_index: int
    min_value: float
    min_index: int
    sign_changes: int


def describe_row(row, k: int) -> RowSummary:
    row = np.asarray(row, dtype=float)
    signs = np.sign(row[np.abs(row) > 1e-12])
    return RowSummary(
        k=k, n=len(row),
        max_value=float(row.max()), max_index=int(row.argmax()),
        min_value=float(row.min()), min_index=int(row.argmin()),
        sign_changes=int(np.sum(np.diff(signs) != 0)),
    )
