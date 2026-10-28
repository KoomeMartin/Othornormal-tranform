# Orthonormal Transform Explorer

A tkinter program for exploring transforms by an orthonormal matrix (the orthonormal DCT-II). It builds the N×N matrix for a power-of-2 size, verifies it, graphs its basis vectors, and applies the forward or inverse transform to columns of an Excel spreadsheet.

Project documents: [Requirements_v1.md](Requirements_v1.md), [Requirements_v2.md](Requirements_v2.md), [Design.md](Design.md).

## Setup

Python 3.10+ (tkinter ships with it).

```
pip install -r requirements.txt
```

## Run

```
python src/main.py
```

## Using it

1. **Transform size:** enter a power of 2 (2, 4, 8, … up to 4096) and press *Build matrix*. Anything else is rejected with a message.
2. **Verify:** multiplies the matrix by its transpose, compares it to the identity, and logs the result and the explanation of why this proves the rows are orthonormal.
3. **Basis vector:** enter a row number (0-based) and press *Plot row*. The log shows the row's maximum, minimum and number of sign changes.
4. **Spreadsheet transform:** choose an `.xlsx` file, choose Forward or Inverse, give the input and output columns (letter or number) and press *Go*. The result is written to the output column, graphed, and the input and output energies are logged.
5. **Graph a column:** pick a column and press *Graph column* to plot it and log its energy (the sum of squares).

### Spreadsheet layout

- Cell **A1** holds N, and it must equal the size you built.
- Data columns are **B** onward. Each holds N values in rows **1 to N** (row 1 is data, not a header).
- Column A can't be used as an input or output column.
- If you generate data with Excel formulas, save the file in Excel before using it, so the computed values are stored. Only the output column is written, so your formulas are preserved.
- Close the file in Excel before pressing *Go*.

## Tests

```
python -m pytest
```

## Part I-b experiments

```
python tools/part1b.py [output_dir]
```

Creates an N=128 workbook of the lab's test vectors, runs them through the program's controller (forward then inverse), writes PNG graphs, and prints a summary table of energies, round-trip errors and dominant bins.

## Layout

```
src/        main.py, app.py (UI), controller.py, transform.py, sheet_io.py, plots.py, errors.py
tests/      pytest suites for the transform, spreadsheet I/O and controller
tools/      part1b.py experiment runner
```
