"""tkinter UI. Widgets and callbacks only; all logic lives in controller.py."""
import time
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, scrolledtext, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from controller import Controller
from errors import UserError


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Orthonormal Transform Explorer")
        self.ctl = Controller(self.log, self.show_figure, confirm=self.confirm)

        self.n_var = tk.StringVar(value="128")
        self.row_var = tk.StringVar(value="0")
        self.file_var = tk.StringVar()
        self.dir_var = tk.StringVar(value="forward")
        self.in_var = tk.StringVar(value="B")
        self.out_var = tk.StringVar(value="C")
        self.graph_var = tk.StringVar(value="B")

        self._build_widgets()
        self._update_states()

    # --- layout ------------------------------------------------------------
    def _section(self, title):
        f = ttk.LabelFrame(self.root, text=title, padding=6)
        f.pack(fill="x", padx=8, pady=3)
        return f

    def _build_widgets(self):
        f = self._section("1. Transform size")
        ttk.Label(f, text="N (power of 2):").pack(side="left")
        ttk.Entry(f, textvariable=self.n_var, width=8).pack(side="left", padx=4)
        ttk.Button(f, text="Build matrix", command=self._guard(self.on_build)).pack(side="left")

        f = self._section("2. Verify")
        self.verify_btn = ttk.Button(f, text="Verify orthonormality",
                                     command=self._guard(self.ctl.verify))
        self.verify_btn.pack(side="left")

        f = self._section("3. Basis vector")
        ttk.Label(f, text="Row k (0-based):").pack(side="left")
        ttk.Entry(f, textvariable=self.row_var, width=8).pack(side="left", padx=4)
        self.row_btn = ttk.Button(f, text="Plot row", command=self._guard(self.on_plot_row))
        self.row_btn.pack(side="left")

        f = self._section("4. Spreadsheet transform")
        r1 = ttk.Frame(f)
        r1.pack(fill="x")
        ttk.Label(r1, text="File:").pack(side="left")
        ttk.Entry(r1, textvariable=self.file_var, width=48, state="readonly").pack(side="left", padx=4)
        ttk.Button(r1, text="Browse...", command=self._guard(self.on_browse)).pack(side="left")
        r2 = ttk.Frame(f)
        r2.pack(fill="x", pady=3)
        ttk.Radiobutton(r2, text="Forward", variable=self.dir_var, value="forward").pack(side="left")
        ttk.Radiobutton(r2, text="Inverse", variable=self.dir_var, value="inverse").pack(side="left", padx=6)
        ttk.Label(r2, text="Input col:").pack(side="left", padx=(12, 0))
        ttk.Entry(r2, textvariable=self.in_var, width=5).pack(side="left", padx=4)
        ttk.Label(r2, text="Output col:").pack(side="left")
        ttk.Entry(r2, textvariable=self.out_var, width=5).pack(side="left", padx=4)
        self.go_btn = ttk.Button(r2, text="Go", command=self._guard(self.on_go))
        self.go_btn.pack(side="left", padx=8)

        f = self._section("5. Graph a column")
        ttk.Label(f, text="Column:").pack(side="left")
        ttk.Entry(f, textvariable=self.graph_var, width=5).pack(side="left", padx=4)
        self.graph_btn = ttk.Button(f, text="Graph column",
                                    command=self._guard(self.on_graph_column))
        self.graph_btn.pack(side="left")

        f = ttk.LabelFrame(self.root, text="Log", padding=6)
        f.pack(fill="both", expand=True, padx=8, pady=3)
        self.log_box = scrolledtext.ScrolledText(f, height=14, width=100, state="disabled",
                                                 font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True)
        b = ttk.Frame(self.root)
        b.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(b, text="Clear log", command=self.clear_log).pack(side="left")
        ttk.Button(b, text="Save log...", command=self._guard(self.save_log)).pack(side="left", padx=6)

    def _update_states(self):
        built = self.ctl.matrix is not None
        have_file = bool(self.ctl.sheet_path)
        self.verify_btn.config(state="normal" if built else "disabled")
        self.row_btn.config(state="normal" if built else "disabled")
        for b in (self.go_btn, self.graph_btn):
            b.config(state="normal" if built and have_file else "disabled")

    # --- plumbing ----------------------------------------------------------
    def _guard(self, fn):
        """Wrap a callback: UserError -> dialog; anything else -> log traceback + generic dialog."""
        def run(*a):
            try:
                fn(*a)
            except UserError as e:
                self.log(f"Error: {e}")
                messagebox.showerror("Problem", str(e))
            except Exception:
                self.log("Unexpected error:\n" + traceback.format_exc())
                messagebox.showerror("Unexpected error", "Something went wrong. See the log for details.")
            self._update_states()
        return run

    def log(self, msg: str):
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"{time.strftime('%H:%M:%S')}  {msg}\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def save_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.log_box.get("1.0", "end"))

    def confirm(self, msg: str) -> bool:
        return messagebox.askyesno("Confirm", msg)

    def show_figure(self, fig):
        win = tk.Toplevel(self.root)
        win.title(fig.axes[0].get_title() if fig.axes else "Graph")
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        NavigationToolbar2Tk(canvas, win)
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- callbacks ---------------------------------------------------------
    def on_build(self):
        self.ctl.build(self.n_var.get())

    def on_browse(self):
        path = filedialog.askopenfilename(filetypes=[("Excel workbook", "*.xlsx")])
        if path:
            self.ctl.set_sheet(path)
            self.file_var.set(path)

    def on_go(self):
        self.ctl.go(self.dir_var.get(), self.in_var.get(), self.out_var.get())

    def on_graph_column(self):
        self.ctl.graph_column(self.graph_var.get())

    def on_plot_row(self):
        self.ctl.plot_row(self.row_var.get())
