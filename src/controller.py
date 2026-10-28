"""One method per button. No tkinter here: I/O goes through injected callbacks."""
from pathlib import Path

import numpy as np

import plots
import sheet_io
import transform as tf
from errors import UserError

VERIFY_EXPLANATION = (
    "Does T*T^T = I prove the rows are orthonormal? Yes. Entry (i,j) of T*T^T is the dot "
    "product of row i with row j. Diagonal = 1 means every row has unit length; off-diagonal "
    "= 0 means distinct rows are orthogonal. (Checked to a floating-point tolerance, not "
    "exactly.) T is square, so T^T*T = I as well: the columns are orthonormal too, and "
    "T^T is the inverse of T."
)


class Controller:
    def __init__(self, log, show_figure, confirm=lambda msg: True):
        self.log = log
        self.show_figure = show_figure
        self.confirm = confirm
        self.n = None
        self.matrix = None
        self.sheet_path = None

    # --- [1] build ---------------------------------------------------------
    def build(self, n_text: str) -> int:
        s = str(n_text).strip()
        try:
            n = int(s)
        except ValueError:
            raise UserError(f"'{n_text}' is not an integer. Enter a power of 2 such as 2, 4, 8, 128.")
        if not tf.is_power_of_two(n):
            lo = 1 << max(1, n.bit_length() - 1) if n > 2 else 2
            hi = lo * 2
            raise UserError(f"{n} is not a power of 2 (nearest valid sizes: {lo} and {hi}).")
        if n > tf.MAX_N:
            raise UserError(f"{n} is too large. The maximum size is {tf.MAX_N}.")
        self.matrix = tf.build_matrix(n)
        self.n = n
        self.log(f"Built {n}x{n} orthonormal DCT-II matrix.")
        return n

    def _need_matrix(self):
        if self.matrix is None:
            raise UserError("Build a matrix first (enter a size and press Build matrix).")

    # --- [2] verify --------------------------------------------------------
    def verify(self):
        self._need_matrix()
        r = tf.verify_orthonormal(self.matrix)
        self.log(f"Verify N={self.n}: T*T^T vs identity -> {'PASS' if r.ok else 'FAIL'}; "
                 f"max |T*T^T - I| = {r.max_abs_error:.3e}")
        if self.n <= 8:
            with np.printoptions(precision=6, suppress=True, linewidth=120):
                self.log("T*T^T =\n" + str(r.product))
        else:
            self.log(f"Diagonal range [{r.min_diag:.12f}, {r.max_diag:.12f}]; "
                     f"largest off-diagonal magnitude {r.max_offdiag:.3e}")
        self.log(VERIFY_EXPLANATION)

    # --- [3] basis vector --------------------------------------------------
    def plot_row(self, k_text: str):
        self._need_matrix()
        try:
            k = int(str(k_text).strip())
        except ValueError:
            raise UserError(f"'{k_text}' is not an integer row number.")
        if not 0 <= k < self.n:
            raise UserError(f"Row {k} is out of range. Valid rows are 0 to {self.n - 1}.")
        row = self.matrix[k]
        d = tf.describe_row(row, k)
        self.log(f"Row {k}: max {d.max_value:.6g} at n={d.max_index}, min {d.min_value:.6g} "
                 f"at n={d.min_index}, {d.sign_changes} sign change(s) "
                 f"(about {d.sign_changes / 2:g} cycles).")
        self.show_figure(plots.plot_basis_row(row, k))

    # --- [4] spreadsheet ---------------------------------------------------
    def set_sheet(self, path):
        self.sheet_path = str(path) if path else None
        if self.sheet_path:
            self.log(f"Spreadsheet: {Path(self.sheet_path).name}")

    def go(self, direction: str, in_text: str, out_text: str):
        self._need_matrix()
        if direction not in ("forward", "inverse"):
            raise UserError("Choose forward or inverse.")
        sheet_n = sheet_io.read_n(self.sheet_path)
        if sheet_n != self.n:
            raise UserError(f"The sheet says N={sheet_n} but the matrix is {self.n}x{self.n}. "
                            "Rebuild the matrix with the same size, or fix cell A1.")
        in_col = sheet_io.parse_column(in_text)
        out_col = sheet_io.parse_column(out_text)
        x = sheet_io.read_column(self.sheet_path, in_col, self.n)
        if sheet_io.column_has_data(self.sheet_path, out_col, self.n):
            if not self.confirm(f"Column {out_text.strip().upper()} already has data. Overwrite it?"):
                self.log("Go cancelled; nothing was written.")
                return
        y = tf.forward(self.matrix, x) if direction == "forward" else tf.inverse(self.matrix, x)
        sheet_io.write_column(self.sheet_path, out_col, y)
        ex, ey = tf.energy(x), tf.energy(y)
        self.log(f"{direction.capitalize()} transform: column {in_text.strip().upper()} -> "
                 f"column {out_text.strip().upper()} ({Path(self.sheet_path).name}).")
        self.log(f"Energy in = {ex:.10g}, energy out = {ey:.10g}, ratio = "
                 f"{(ey / ex) if ex else float('nan'):.10g}")
        self.show_figure(plots.plot_vector(
            y, f"{direction.capitalize()} transform result (column {out_text.strip().upper()}), "
               f"energy = {ey:.6g}"))

    # --- [5] graph a column ------------------------------------------------
    def graph_column(self, col_text: str):
        self._need_matrix()
        sheet_n = sheet_io.read_n(self.sheet_path)
        if sheet_n != self.n:
            raise UserError(f"The sheet says N={sheet_n} but the matrix is {self.n}x{self.n}.")
        col = sheet_io.parse_column(col_text)
        v = sheet_io.read_column(self.sheet_path, col, self.n)
        e = tf.energy(v)
        self.log(f"Column {col_text.strip().upper()}: energy = {e:.10g}")
        self.show_figure(plots.plot_vector(
            v, f"Column {col_text.strip().upper()}, energy = {e:.6g}"))
