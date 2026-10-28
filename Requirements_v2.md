# Requirements v2 — Orthonormal Transform Explorer

Refines [Requirements_v1.md](Requirements_v1.md) using the Lab 1 handout (Lab 1.pdf, Part I).

## 1. Overview

### 1.1 Purpose
A desktop tool to understand and visualize transforms by an orthonormal matrix. The user builds an N×N orthonormal transform matrix, checks its orthonormality, inspects its basis vectors, and applies the forward or inverse transform to data vectors stored in an Excel spreadsheet.

### 1.2 Users
A single student or analyst running the tool locally. No accounts, no network, no multi-user needs.

### 1.3 Goals
- Make orthonormality visible: numerical check plus basis-vector plots.
- Make transform behaviour visible: graph input and output vectors and report their energy.
- Support the Part I-b experiments (N = 128): sinusoids, phase shifts, random noise, pulses.

### 1.4 Non-goals
- No fast (FFT-style) algorithm; direct matrix multiply is fine for N ≤ a few thousand.
- No web or mobile UI.
- No runtime AI/LLM calls (see Open Question Q2).

## 2. Open questions (resolve before coding)

| # | Question | Working assumption |
|---|----------|--------------------|
| Q1 | **Which matrix?** The handout says "the orthonormal matrix I specified in lecture 2", which is not in the files provided. | **Orthonormal DCT-II**, a real matrix that exists for every power-of-2 size. `C[0,n] = sqrt(1/N)`, `C[k,n] = sqrt(2/N)·cos(π(2n+1)k / 2N)` for k ≥ 1. The matrix is isolated in one function so it can be swapped for the lecture's definition (e.g. Hadamard, Haar, real DFT/Hartley). **Please confirm against the lecture notes.** |
| Q2 | v1 says "an AI service provider model generates a graph". The handout says "Claude generates a graph", which most likely means Claude *writes the code* that graphs. | Graphs are drawn locally with matplotlib. No API key or network. |
| Q3 | Spreadsheet layout: v1 puts N "in the first row of its first column" and data in "rows 1 through N of columns 2, 3, 4". | Cell A1 holds N. Data lives in B1:B{N}, C1:C{N}, … (row 1 is data, not a header). Columns can be given as letters (`B`) or numbers (`2`). |
| Q4 | Must the transform size N be entered in the UI *and* be in the spreadsheet? | Yes, both. The UI size defines the matrix. A1 must match it, otherwise the program reports an error and does nothing. |

## 3. Functional requirements

### FR-1 Transform size
- Integer entry field; must be a power of 2 (2, 4, 8, …). Check: `n >= 2 and (n & (n-1)) == 0`.
- Upper bound 4096 to keep the matrix fast and plots readable (configurable constant).
- On violation (non-integer, ≤ 1, not a power of 2): show an error dialog naming the bad value and a list of nearby valid sizes. Do not build a matrix. Log the event.
- On success, build the matrix, log "Built N×N matrix", and enable the other controls.

### FR-2 Matrix generation
- Build the orthonormal matrix `T` (N×N, float64) per Q1.
- Forward transform: `y = T·x`. Inverse transform: `x = Tᵀ·y`.

### FR-3 Verify button
- Computes `P = T·Tᵀ` and compares it to `I` with `np.allclose(P, I, atol=1e-10)`.
- Log shows: size, PASS/FAIL, max |P − I|, and, for N ≤ 8, the full product matrix. For larger N show the diagonal range and max off-diagonal magnitude.
- **Written answer (include in the log text and the lab report):** Does this prove the rows are orthonormal? Yes. Entry (i, j) of `T·Tᵀ` is the dot product of row i with row j. Identity means each row has unit norm (diagonal = 1) and distinct rows are orthogonal (off-diagonal = 0). The only caveat is floating-point: the check holds within a tolerance, not exactly. Because `T` is square, `TᵀT = I` follows too, so the columns are also orthonormal and `Tᵀ = T⁻¹`. That is why the inverse is simply the transpose.

### FR-4 Basis-vector plot
- Row-number field (0-based; valid 0 … N−1, with the indexing convention shown in the UI label) plus a "Plot row" button.
- Validates the range; out-of-range shows an error.
- Plots row `k` against sample index n (stem or line-with-markers), titled with k and N.

### FR-5 Spreadsheet transform ("Go")
Controls:
- "Browse…" file picker for `.xlsx`.
- Forward / Inverse toggle (radio buttons).
- "Input column" field and "Output column" field.
- "Go" button.

Behaviour on Go:
1. Validate the file, the columns, and that N in A1 equals the UI size.
2. Read `N` numeric values from rows 1…N of the input column.
3. Apply the forward or inverse transform.
4. Write the result into rows 1…N of the output column.
5. Save the workbook and plot the result vector.
6. Log: file, direction, input and output columns, input energy, output energy.

Rules:
- The input and output columns must be ≥ 2 (column A is reserved for N). Reject A.
- Input and output may be the same column; warn before overwriting existing data.
- Input cells that are blank or non-numeric: error naming the first bad cell. Never silently treat them as 0.
- If the file is open in Excel, saving fails. Catch `PermissionError` and tell the user to close it.

### FR-5b Cell-formula caveat
Part I-b requires generating data in Excel, probably with formulas. openpyxl returns formulas, not values, unless the file is read with `data_only=True`, and that only works if Excel has saved cached values. Saving a workbook loaded with `data_only=True` *replaces formulas with values*. So the program must:
- Read values from a `data_only=True` load.
- Write results through a normal load (formulas preserved) and save that, so only the output column changes.
- If a cached value is missing (`None`), tell the user to open and save the file in Excel first.

### FR-6 Graph-a-column and energy
- Column field plus a "Graph column" button.
- Plots the selected column (rows 1…N) and logs its **energy** `E = Σ xᵢ²`.
- Both graph buttons also show the energy in the plot title or a status label, so the Parseval comparison (input vs. output energy) is easy to read.

### FR-7 Log window
- Scrolling, read-only text pane in the main window; timestamped lines.
- Receives all verification results, errors, and operation summaries.
- "Clear log" and "Save log…" buttons (nice to have).

## 4. Inputs

| Input | Source | Type / constraint |
|-------|--------|-------------------|
| Transform size N | Entry field | Integer, power of 2, 2 ≤ N ≤ 4096 |
| Row number k | Entry field | Integer, 0 ≤ k < N |
| Spreadsheet | File dialog | `.xlsx`; A1 = N; data in column B onward, rows 1…N |
| Direction | Radio toggle | Forward / Inverse |
| Input column | Entry field | Letter or number, ≥ 2 (B) |
| Output column | Entry field | Letter or number, ≥ 2 (B) |
| Column to graph | Entry field | Letter or number, ≥ 2 (B) |

## 5. Outputs

| Output | Destination | Content |
|--------|-------------|---------|
| Log messages | Log window | Verify result, errors, energies, operation summaries |
| Error dialogs | Message box | Constraint violations and file problems |
| Basis-vector plot | Matplotlib window or embedded canvas | Row k of T vs. n |
| Result plot | Same | Transformed (or inverse transformed) column |
| Column plot | Same | Selected column plus energy |
| Updated spreadsheet | Same `.xlsx` | Output column filled with results |

## 6. Mathematical background (for the report)

- Orthonormal: `T·Tᵀ = TᵀT = I`.
- Energy: `E(x) = Σ xᵢ² = ‖x‖²`.
- Orthonormal transforms preserve energy (Parseval): `‖Tx‖² = xᵀTᵀTx = ‖x‖²`. Use FR-6 to confirm this for each Part I-b experiment, to within floating-point error.
- Inverse = transpose, so forward-then-inverse should return the original column to ~1e-12.

## 7. Part I-b experiment support (N = 128)

The program does not generate data. The user builds these in Excel, but the program must handle them. Suggested formulas (with n = 0…127 and cell A1 = 128):

| Item | Vector |
|------|--------|
| i, ii | `cos(2π·6·n/128)`, then inverse transform the result |
| iii | `sin(2π·6·n/128)` |
| iv, v | `cos(2π·9·n/128)`, `sin(2π·9·n/128)` |
| vi | Sum of the two previous vectors (a column formula, e.g. `=D1+E1`) |
| vii | `cos(2π·6·n/128 + π/4)` (45° = π/4 rad) |
| viii | `=RANDBETWEEN` is integer-only, so use `=2*RAND()-1`. Paste as values so it stops recalculating. |
| ix–xi | Pulses of width 10, 5, 30: ones in rows 1…w, zeros after |

Note: for the random vector, paste values before running Go. A live `RAND()` column would change between the forward and inverse runs and defeat the verification.

## 8. Non-functional requirements

- **Correctness:** Verify tolerance 1e-10; round-trip tolerance 1e-9.
- **Responsiveness:** Go on N = 128 finishes in well under a second. Heavy work stays off the UI thread only if N is large (not required at N ≤ 4096).
- **Robustness:** Every user-input error is caught and reported in a dialog plus the log. The program never crashes with a traceback in the UI.
- **Usability:** Controls disabled until a valid N is set. Labels state indexing conventions (0-based rows, 1-based spreadsheet columns).
- **Portability:** Windows 11 (primary). Pure-Python dependencies, so it also works on macOS and Linux.
- **Project convention:** Per the handout, keep versioned requirement files (`Requirements_v1.md`, `Requirements_v2.md`, …). Do not edit earlier versions.

## 9. Technology stack

| Concern | Choice | Why |
|---------|--------|-----|
| Language | Python 3.10+ | Required by the handout |
| GUI | tkinter (+ `ttk`) | Required by the handout; ships with Python |
| Numerics | NumPy | Matrix build, `T @ T.T`, `allclose`, energy |
| Excel I/O | openpyxl | Read and write `.xlsx` while preserving formulas (pandas would rewrite the whole sheet) |
| Plotting | matplotlib (`TkAgg` backend, `FigureCanvasTkAgg`) | Native tkinter embedding; stem and line plots |
| Testing | pytest | Unit tests for the math and the file I/O |
| Packaging | `requirements.txt` | `numpy`, `openpyxl`, `matplotlib`, `pytest` |

Rejected alternatives: pandas (unneeded and destroys formulas on write), xlwings (needs Excel installed), PyQt/Streamlit (the handout requires tkinter), SciPy `dct` (fine as a test oracle for Q1's DCT-II assumption, but the lab wants us to build the matrix explicitly).

## 10. Proposed architecture

Separate the math from the GUI so the math is testable without a display.

```
Lab 1/
  Requirements_v1.md
  Requirements_v2.md
  requirements.txt
  src/
    transform.py     # build_matrix(n), is_power_of_two(n), forward/inverse, energy, verify_orthonormal
    sheet_io.py      # read_n, read_column, write_column, column-letter parsing (openpyxl)
    plots.py         # plot_vector(), plot_basis_row() — return Figure objects
    app.py           # tkinter UI: widgets, callbacks, log pane; calls the modules above
  tests/
    test_transform.py
    test_sheet_io.py
```

## 11. Acceptance criteria / test plan

1. N = 6, 0, -4, 1, "abc", 3.5 are each rejected with a dialog. N = 2, 4, 128 are accepted.
2. Verify at N = 128 reports PASS with max error < 1e-10.
3. Plot row 0 and row 5 at N = 128. Row 0 is constant. Row 5 shows 2.5 cycles of cosine (under the DCT-II assumption). Row 128 is rejected.
4. `cos(2π·6·n/128)` → forward → inverse: recovered column matches the original to 1e-9.
5. For every Part I-b vector, input energy ≈ output energy (Parseval) to 1e-9.
6. Output column = A is rejected. A1 ≠ UI size is rejected. A blank or text cell in the data range names the cell. A file open in Excel gives a "close the file" message.
7. A workbook whose data column came from formulas keeps those formulas after Go.
8. Unit tests in `tests/` pass without a display.

## 12. Deliverables

- Working program (`src/`), `requirements.txt`, tests.
- Spreadsheet(s) with the Part I-b vectors and transformed columns.
- Written answers for Part I-b (i–xii) and the FR-3 orthonormality question, with plots and energies, based on the program's output.
