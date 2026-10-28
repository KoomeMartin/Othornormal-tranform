# Design — Orthonormal Transform Explorer

Companion to [Requirements_v2.md](Requirements_v2.md). This document turns the requirements and the decisions made since v2 into one design: stack, architecture, data flow, module interfaces and test plan.

## 1. Decisions locked in

| # | Topic | Decision |
|---|-------|----------|
| D1 | Matrix | The canonical **orthonormal DCT-II** matrix. Row 0 is `sqrt(1/N)`. Row `k ≥ 1` is `sqrt(2/N)·cos(π(2n+1)k / 2N)`. Built in one function (`build_matrix`), so it can be swapped later. |
| D2 | Claude's role | **Claude writes the code** (this project is built with Claude). There is **no runtime AI call**: the basis-vector graph is drawn locally. See section 6. |
| D3 | Spreadsheet layout | Fixed, as set out in section 5. Cell A1 holds N. Data is in columns B onward, rows 1…N, with no header row. |
| D4 | Language and GUI | Python 3.10+, tkinter (required by the handout). |
| D5 | Versioning | Requirement files are versioned (`Requirements_v1`, `v2`, …). This design does not edit earlier versions. |

## 2. Technology stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Language | Python 3.10+ | |
| GUI | tkinter + ttk | Standard library. Desktop only. |
| Numerics | NumPy | Matrix build, `T @ T.T`, `allclose`, energy |
| Excel I/O | openpyxl | Reads cached values and writes one column without destroying formulas (section 5.3) |
| Plotting | matplotlib, `TkAgg` backend, `FigureCanvasTkAgg` | Embedded in the Tk window |
| Tests | pytest | Math, file I/O and the controller run headless. |
| Dependencies | `requirements.txt` | `numpy`, `openpyxl`, `matplotlib`, `pytest` |

## 3. Architecture

### 3.1 Layers

```
┌──────────────────────────────────────────────┐
│ app.py (tkinter)  — widgets, callbacks, log   │  UI layer: no math, no file parsing
├──────────────────────────────────────────────┤
│ controller.py — one method per button         │  Orchestration: validates inputs, calls services,
│                                                │  reports to the log, raises user-facing errors
├───────────────┬───────────────┬───────────────┤
│ transform.py  │ sheet_io.py   │ plots.py      │  Pure services
│ (NumPy)       │ (openpyxl)    │ (matplotlib)  │
├───────────────┴───────────────┴───────────────┤
└──────────────────────────────────────────────┘
```

Rules:
- Services never import tkinter. They return values or raise `UserError` (a small exception class carrying a message that is safe to show).
- Only `app.py` touches widgets. The controller receives plain values (strings from the entry fields) and returns plain results.
- Nothing talks to the network.

### 3.2 File layout

```
Lab 1/
  Requirements_v1.md
  Requirements_v2.md
  Design.md
  requirements.txt
  src/
    main.py          # entry point: builds Tk root and App
    app.py           # tkinter widgets and callbacks
    controller.py    # one method per button
    errors.py        # UserError
    transform.py
    sheet_io.py
    plots.py
  tests/
    test_transform.py
    test_sheet_io.py
    test_controller.py
```

### 3.3 Window layout

```
┌ Orthonormal Transform Explorer ─────────────────────────────┐
│ [1] Transform size   N: [____]  [Build matrix]              │
│ [2] Verify           [Verify orthonormality]                │
│ [3] Basis vector     Row k: [____]  [Plot row]              │
│ [4] Spreadsheet      File: [______________] [Browse…]       │
│                      (•) Forward  ( ) Inverse               │
│                      Input col: [__]  Output col: [__]      │
│                      [Go]                                   │
│ [5] Graph a column   Column: [__]  [Graph column]           │
│ ┌ Log ────────────────────────────────────────────────────┐ │
│ │ 14:02:11  Built 128×128 DCT-II matrix                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Clear log] [Save log…]                                     │
└─────────────────────────────────────────────────────────────┘
```

Plots open in separate matplotlib windows through `plt.show(block=False)`, so several can be compared side by side. Embedding the plot is an alternative if separate windows prove awkward.

Control state: everything below [1] is disabled until a valid N is built. The Go and Graph buttons also need a chosen file. Controls are re-enabled when a build succeeds. A failed rebuild keeps the previous matrix.

### 3.4 State

A small `AppState` dataclass lives in the controller.

| Field | Meaning |
|-------|---------|
| `n: int \| None` | Current size |
| `matrix: ndarray \| None` | The N×N matrix |
| `sheet_path: Path \| None` | Chosen workbook |

Changing N invalidates `matrix` and rebuilds it. There is no other global state.

## 4. Module interfaces

### 4.1 `transform.py`
```python
def is_power_of_two(n: int) -> bool
def build_matrix(n: int) -> np.ndarray            # orthonormal DCT-II, float64, shape (n, n)
def forward(T, x) -> np.ndarray                   # T @ x
def inverse(T, y) -> np.ndarray                   # T.T @ y
def energy(v) -> float                            # sum(v**2)
def describe_row(row, k) -> RowSummary             # max/min (value, index), sign changes
def verify_orthonormal(T, atol=1e-10) -> VerifyResult
#   VerifyResult: ok, max_abs_error, product (n×n), min_diag, max_diag, max_offdiag
```

### 4.2 `sheet_io.py`
```python
def parse_column(text: str) -> int                # "B" or "2" → 2 (1-based). Rejects < 2 and non-columns.
def read_n(path) -> int                           # value of A1; must be a positive integer
def read_column(path, col: int, n: int) -> np.ndarray   # rows 1..n; raises UserError naming the first bad cell
def write_column(path, col: int, values) -> None        # rows 1..n; keeps all other cells and formulas
```

### 4.3 `plots.py`
```python
def plot_vector(values, title, *, kind="line") -> Figure
def plot_basis_row(row, k) -> Figure              # row k graph, max/min annotated
```

### 4.4 `controller.py`
One public method per button: `build(n_text)`, `verify()`, `plot_row(k_text)`, `set_sheet(path)`, `go(direction, in_text, out_text)`, `graph_column(col_text)`. Each returns nothing and reports through injected `log(msg)`, `show_figure(fig)` and `confirm(msg)` callbacks, and raises `UserError` for bad input. `app.py` catches `UserError` and shows a dialog. It also catches any other exception, logs the traceback, and shows a generic "unexpected error" dialog, so the UI never dies on a traceback.

## 5. Spreadsheet design

### 5.1 Layout (fixed)

```
      A      B        C        D     …
 1    N      x[0]     x[0]     …
 2           x[1]     …
 …           …
 N           x[N-1]
```
- **A1** = N (positive integer, power of 2, equal to the size built in the UI). Rest of column A is ignored and never written.
- **Data columns** are B (2), C (3), D (4), … Each holds an N-element vector in rows **1…N**. Row 1 is data, not a header.
- Rows below N, and columns not named, are never touched.
- Column fields accept letters (`B`, `aa`) or 1-based numbers (`2`). Column A (1) is rejected as input or output.

### 5.2 Validation order (Go)
1. File chosen and exists.
2. N built, A1 readable, `A1 == N` (otherwise "Sheet says N=…, matrix is …").
3. Input and output column parse, both ≥ 2.
4. Read input rows 1…N. The first blank or non-numeric cell raises an error naming it (for example `C17 is empty`).
5. Transform, then write, then save, then plot.

Nothing is written unless steps 1–4 succeed.

### 5.3 Formulas and cached values
Test vectors will probably be built with Excel formulas. openpyxl cannot compute formulas. It either returns the formula text or, with `data_only=True`, the value Excel last cached.
- **Read:** load with `data_only=True`. A `None` in a data cell that actually holds a formula means Excel never saved cached values. Report: "Open the file in Excel and save it, then retry."
- **Write:** load a *second* workbook without `data_only` (formulas intact), set only the output cells, and save that. This keeps every other formula.
- Writing over an existing formula column asks for confirmation first.
- `PermissionError` on save is reported as "close the file in Excel and retry".
- Results are written as plain numbers (values, not formulas). They do not recalculate if the input changes.
- Caveat: openpyxl drops some Excel features on save (charts, images, some conditional formats). The user is told to work on a copy of important workbooks. The program does not make backups.

## 6. Basis-vector graph (local)

The basis-vector graph is produced locally with no AI service. A runtime model call was considered and removed (see 6.2).

### 6.1 Behavior
- `plot_row(k)` validates `0 ≤ k < N`, takes row `k` of the matrix and computes a summary with `describe_row`: maximum and minimum with their indices, and the number of sign changes (so about half that many cycles).
- The summary is logged, for example: "Row 5: max 0.124991 at n=102, min -0.124991 at n=25, 5 sign change(s) (about 2.5 cycles)."
- The figure plots the row against the column index (stem for N ≤ 32, line otherwise), with a zero line, a grid, and the maximum and minimum annotated.

### 6.2 Why there is no runtime Claude call
Everything a model could add here (title, labels, extrema, zero crossings, a short description) is computed exactly and instantly with NumPy. A model call would add a network dependency, an API key, latency and a failure path, with no gain in accuracy. Claude's role in this project is writing the code, which is what the lab handout asks for ("Use Claude to write a program").

If a runtime call is ever wanted, it fits in as an optional step that returns only labels and a text summary. The program would still draw its own data, and the local graph would remain the default.

## 7. Behavior of each feature (data flow)

| Feature | Flow |
|---------|------|
| Build | `n_text` → int → `is_power_of_two` and bounds (2…4096) → `build_matrix` → state → log. On failure: dialog, matrix unchanged. |
| Verify | `T @ T.T` → `verify_orthonormal` → log (PASS/FAIL, max error, full matrix if N ≤ 8) → static explanation of why identity ⇒ orthonormal rows. |
| Plot row | `k_text` → int, range check → `T[k]` → `describe_row` → log summary → `plot_basis_row`. |
| Go | Section 5.2 order → `forward` / `inverse` → `write_column` → `plot_vector` → log both energies. |
| Graph column | Column parse → `read_column` → `plot_vector` → log energy `Σx²`. |

Energy is logged with 10 significant digits. For Go the log also shows the input/output ratio, which should be 1.0 up to floating-point error (Parseval).

## 8. Error handling

| Situation | Behavior |
|-----------|----------|
| N not an integer, < 2, not a power of 2, > 4096 | Dialog stating the bad value and valid neighbours; log entry |
| Row out of range | Dialog stating the valid range |
| No file chosen, file missing or not `.xlsx` | Dialog |
| A1 missing, not an integer, or ≠ N | Dialog with both values |
| Column A, an invalid column, or an unparsable column | Dialog |
| Blank or non-numeric data cell | Dialog naming the cell |
| Formula without cached value | Dialog: open and save in Excel first |
| Save fails (file open elsewhere) | Dialog: close the file and retry |
| Anything unexpected | Traceback to the log, generic dialog |

## 9. Testing

Headless tests (`pytest`, matplotlib `Agg` backend):

| File | Covers |
|------|--------|
| `test_transform.py` | `is_power_of_two` (2, 4, 128 true; 0, 1, 3, 6, −4 false). `T @ T.T ≈ I` for N = 2…256. Forward then inverse recovers random vectors to 1e-12. Parseval: `energy(Tx) ≈ energy(x)`. Row 0 is constant. Matches `scipy.fft.dct(type=2, norm="ortho")` as an oracle if SciPy is installed (test-only dependency, skipped otherwise). |
| `test_sheet_io.py` | Column parsing (`B`, `2`, `aa`, rejects `A`, `0`, `""`). Round trip through a temp workbook. Blank and text cells name the cell. Writing preserves formulas and other columns. Missing cached value error. |
| `test_controller.py` | Each button method with fake `log`, `show_figure` and `confirm` callbacks, covering the error table in section 8. Go enforces `A1 == N`. Plot row validates the range and logs the sign-change summary. |

Manual checks: build N = 128, verify, plot rows 0 and 5 with and without an API key, run the Part I-b vectors, and confirm the formula-preservation behavior with a workbook built by formulas.

## 10. Build plan

1. `transform.py` plus tests.
2. `sheet_io.py` plus tests.
3. `plots.py`.
4. `controller.py` plus tests.
5. `app.py` and `main.py`, then a manual run of Go.
6. Run the Part I-b experiments at N = 128 and record the results for the report.

## 11. Open items

- Confirm the matrix with the lecture 2 definition, if that turns out to differ from the DCT-II. Only `build_matrix` and the row-5 acceptance check (2.5 cycles) would change.
- (Resolved) No runtime AI call.
- Plots open in separate windows. Say so if you would rather embed them in the main window.
