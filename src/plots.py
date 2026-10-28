"""Matplotlib figures. Figures are returned, never shown here."""
import numpy as np
from matplotlib.figure import Figure


def _fig():
    fig = Figure(figsize=(8, 4), tight_layout=True)
    return fig, fig.add_subplot(111)


def _draw(ax, values, style):
    x = np.arange(len(values))
    if style == "stem":
        ax.stem(x, values)
    else:
        ax.plot(x, values, marker="o", markersize=3)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.grid(alpha=0.3)


def plot_vector(values, title: str, style: str = "line") -> Figure:
    fig, ax = _fig()
    _draw(ax, np.asarray(values, dtype=float), style)
    ax.set_title(title)
    ax.set_xlabel("index n")
    ax.set_ylabel("value")
    return fig


def plot_basis_row(row, k: int) -> Figure:
    """Graph row k of the transform matrix, marking its maximum and minimum."""
    row = np.asarray(row, dtype=float)
    n = len(row)
    fig, ax = _fig()
    _draw(ax, row, "stem" if n <= 32 else "line")
    ax.set_title(f"Basis vector: row {k} of the {n}x{n} orthonormal transform")
    ax.set_xlabel("column index n")
    ax.set_ylabel("matrix entry")
    for idx, name in ((int(row.argmax()), "max"), (int(row.argmin()), "min")):
        ax.annotate(f"{name} {row[idx]:.3g}", (idx, row[idx]), textcoords="offset points",
                    xytext=(0, 10 if name == "max" else -14), ha="center", fontsize=8)
    return fig
