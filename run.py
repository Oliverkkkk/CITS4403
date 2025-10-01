"""
GUI entry point for the Feral Cats ABM (custom map support, class-based, no unresolved refs).
Run: python run.py
"""

import os, sys, json
import numpy as np
import matplotlib

# ---- backend selection ----
def select_backend(interactive=True, force_tk=False):
    if os.environ.get("MPLBACKEND"):
        return
    if force_tk:
        matplotlib.use("TkAgg", force=True)
        return
    if not interactive or os.environ.get("CI") or not sys.stdout.isatty():
        matplotlib.use("Agg", force=True)
        return
    candidates = (["MacOSX", "QtAgg", "TkAgg", "Agg"] if sys.platform == "darwin"
                  else ["QtAgg", "TkAgg", "Agg"])
    for name in candidates:
        try:
            matplotlib.use(name, force=True)
            return
        except Exception:
            continue

# ---- loaders ----
def load_vegetation_from_csv(path, max_val=4):
    arr = np.genfromtxt(path, delimiter=",", dtype=float)
    arr = np.nan_to_num(arr, nan=0.0)
    v = np.rint(arr).astype(np.int16)
    np.clip(v, 0, max_val, out=v)
    return v

def load_vegetation_from_json(path, max_val=4):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    v = np.array(data, dtype=np.int16)
    np.clip(v, 0, max_val, out=v)
    return v

def load_mask_from_png(path, threshold=128):
    from PIL import Image  # pip install pillow
    img = Image.open(path).convert("L")
    a = np.array(img, dtype=np.uint8)
    return (a >= threshold)

def load_vegetation_from_png(path, scale=4):
    from PIL import Image
    img = Image.open(path).convert("L")
    a = np.array(img, dtype=np.float32) / 255.0
    v = np.rint(a * scale).astype(np.int16)
    np.clip(v, 0, scale, out=v)
    return v

# ---- main GUI app ----
def launch_gui():
    select_backend(interactive=True, force_tk=True)

    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from src.model import FeralCatModel
    from src.visual2d import animate_grid

    class App:
        def __init__(self, root):
            self.root = root
            root.title("Feral Cats ABM — Custom Map")

            # left params panel
            self.params = ttk.Frame(root, padding=10); self.params.grid(row=0, column=0, sticky="nsw")
            # right display panel
            self.display = ttk.Frame(root, padding=10); self.display.grid(row=0, column=1, sticky="nsew")
            root.columnconfigure(1, weight=1); root.rowconfigure(0, weight=1)

            # vars
            self.width_var  = tk.StringVar(value="25")
            self.height_var = tk.StringVar(value="25")
            self.steps_var  = tk.StringVar(value="100")
            self.cats_var   = tk.StringVar(value="6")
            self.prey_var   = tk.StringVar(value="40")
            self.pb_var     = tk.StringVar(value="0.2")
            self.pc_var     = tk.StringVar(value="0.1")
            self.pf_var     = tk.StringVar(value="0.4")
            self.seed_var   = tk.StringVar(value="")

            # inputs
            self._add_row(0, "Grid width",  self.width_var)
            self._add_row(1, "Grid height", self.height_var)
            self._add_row(2, "Steps",       self.steps_var)
            self._add_row(3, "Cats",        self.cats_var)
            self._add_row(4, "Prey",        self.prey_var)
            self._add_row(5, "predation_base (pb)", self.pb_var)
            self._add_row(6, "predation_coef (pc)", self.pc_var)
            self._add_row(7, "flee_prob (pf)",      self.pf_var)
            self._add_row(8, "Seed (optional)",     self.seed_var)

            # custom map
            r = 9
            ttk.Separator(self.params, orient="horizontal").grid(row=r, column=0, columnspan=2, sticky="ew", pady=(8,6)); r += 1
            ttk.Label(self.params, text="Custom Map (optional)", font=("TkDefaultFont", 10, "bold")).grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

            self.veg_label_var = tk.StringVar(value="Vegetation: (none)")
            self.river_label_var = tk.StringVar(value="River mask: (none)")
            ttk.Label(self.params, textvariable=self.veg_label_var, wraplength=220, justify="left").grid(row=r, column=0, columnspan=2, sticky="w"); r += 1
            ttk.Label(self.params, textvariable=self.river_label_var, wraplength=220, justify="left").grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

            ttk.Button(self.params, text="Load vegetation...", command=self.load_vegetation).grid(row=r, column=0, pady=(4,2), sticky="ew")
            ttk.Button(self.params, text="Load river mask...", command=self.load_river).grid(row=r, column=1, pady=(4,2), sticky="ew"); r += 1
            ttk.Button(self.params, text="Clear maps", command=self.clear_maps).grid(row=r, column=0, columnspan=2, pady=(2,8), sticky="ew"); r += 1

            # control buttons
            self.start_btn = ttk.Button(self.params, text="Start", command=self.start_sim)
            self.start_btn.grid(row=r, column=0, columnspan=2, pady=(12,2), sticky="ew"); r += 1
            self.pause_btn = ttk.Button(self.params, text="Pause", command=self.pause_resume, state="disabled")
            self.pause_btn.grid(row=r, column=0, columnspan=2, pady=2, sticky="ew"); r += 1
            self.reset_btn = ttk.Button(self.params, text="Reset", command=self.reset_sim, state="normal")
            self.reset_btn.grid(row=r, column=0, columnspan=2, pady=(2,0), sticky="ew"); r += 1

            self.scent_var = tk.BooleanVar(value=False)  # scent display toggle
            ttk.Checkbutton(self.params, text="Show cat scent range", variable=self.scent_var).grid(row=r, column=0, columnspan=2, sticky="w", pady=(6, 0)); r += 1

            # state
            self.canvas_widget = None
            self.current_fig = None
            self.current_anim = None
            self.is_running = False
            self.is_paused = False
            self.V = None
            self.R = None

            # close hook
            root.protocol("WM_DELETE_WINDOW", self.on_close)

        def _add_row(self, r, text, var):
            ttk.Label(self.params, text=text, width=18, anchor="w").grid(row=r, column=0, pady=3, sticky="w")
            e = ttk.Entry(self.params, textvariable=var, width=12); e.grid(row=r, column=1, pady=3, sticky="w")
            return e

        # ----- loaders -----
        def load_vegetation(self):
            from tkinter import filedialog, messagebox
            path = filedialog.askopenfilename(
                title="Select vegetation (CSV/JSON/PNG)",
                filetypes=[("CSV","*.csv"),("JSON","*.json"),("PNG","*.png"),("All","*.*")]
            )
            if not path: return
            try:
                if path.lower().endswith(".csv"):
                    v = load_vegetation_from_csv(path, max_val=4)
                elif path.lower().endswith(".json"):
                    v = load_vegetation_from_json(path, max_val=4)
                elif path.lower().endswith(".png"):
                    v = load_vegetation_from_png(path, scale=4)
                else:
                    messagebox.showerror("Unsupported", "CSV / JSON / PNG only"); return
                self.V = v
                h, w = v.shape
                self.width_var.set(str(w)); self.height_var.set(str(h))
                self.veg_label_var.set(f"Vegetation: {os.path.basename(path)} shape={v.shape} range=[{v.min()},{v.max()}]")
            except Exception as e:
                messagebox.showerror("Load error", f"Failed to load nutrition：\n{e}")

        def load_river(self):
            from tkinter import filedialog, messagebox
            path = filedialog.askopenfilename(
                title="Select river mask (PNG/CSV)",
                filetypes=[("PNG","*.png"),("CSV","*.csv"),("All","*.*")]
            )
            if not path: return
            try:
                if path.lower().endswith(".png"):
                    m = load_mask_from_png(path, threshold=128)
                else:
                    arr = np.genfromtxt(path, delimiter=",", dtype=float)
                    arr = np.nan_to_num(arr, nan=0.0); m = (arr > 0.5)
                self.R = m.astype(bool)
                self.river_label_var.set(f"River: {os.path.basename(path)} shape={m.shape} true={m.sum()}")
            except Exception as e:
                messagebox.showerror("Load error", f"Failed to load river：\n{e}")

        def clear_maps(self):
            self.V = None; self.R = None
            self.veg_label_var.set("Vegetation: (none)")
            self.river_label_var.set("River mask: (none)")

        # ----- control helpers -----
        def set_running_state(self, running: bool):
            self.is_running = running
            if running:
                self.start_btn.config(state="disabled")
                self.pause_btn.config(state="normal", text="Pause")
                self.reset_btn.config(state="normal")
            else:
                self.start_btn.config(state="normal")
                self.pause_btn.config(state="disabled", text="Pause")
                self.reset_btn.config(state="normal")
                self.is_paused = False

        def stop_anim(self):
            if self.current_anim is not None:
                try: self.current_anim.event_source.stop()
                except Exception: pass
                self.current_anim = None

        def clear_canvas(self):
            if self.canvas_widget is not None:
                self.canvas_widget.destroy()
                self.canvas_widget = None

        def show_plots(self, model):
            df = model.datacollector.get_model_vars_dataframe().reset_index(drop=True)
            figs = []

            fig1, ax1 = plt.subplots(figsize=(7, 4))
            df[["Prey", "Cats"]].plot(ax=ax1)
            ax1.set_title("Population over time")
            ax1.set_xlabel("Step"); ax1.set_ylabel("Count")
            fig1.tight_layout()
            figs.append(fig1)

            fig2, ax2 = plt.subplots(figsize=(7, 3))
            df["predation_events_this_step"].plot(ax=ax2)
            ax2.set_title("Predation events per step")
            ax2.set_xlabel("Step"); ax2.set_ylabel("Events")
            fig2.tight_layout()
            figs.append(fig2)

            remaining = {"windows": len(figs)} # window close tracking

            def _on_figure_closed(event):
                remaining["windows"] -= 1
                if remaining["windows"] <= 0:
                    self.set_running_state(False) # restore main window
                    try:
                        root.deiconify()
                        root.lift()
                        root.focus_force()
                    except Exception:
                        pass
                    
            for f in figs:
                f.canvas.mpl_connect('close_event', _on_figure_closed)
                try:
                    f.show()  # Matplotlib 3.5+
                except Exception:
                    # compatibility for older versions
                    f.canvas.draw_idle()
                    try:
                        f.canvas.manager.window.deiconify()
                    except Exception:
                        pass

        # ----- actions -----
        def start_sim(self):
            if self.is_running: return

            # read params
            try:
                w  = int(self.width_var.get())
                h  = int(self.height_var.get())
                st = max(1, int(self.steps_var.get()))
                nc = int(self.cats_var.get())
                np_ = int(self.prey_var.get())
                pb = float(self.pb_var.get())
                pc = float(self.pc_var.get())
                pf = float(self.pf_var.get())
                seed = int(self.seed_var.get()) if self.seed_var.get().strip() else None
            except Exception:
                from tkinter import messagebox
                messagebox.showerror("Invalid input", "Please check parameter types.")
                return

            # shape checks
            if self.V is not None:
                hh, ww = self.V.shape
                w, h = ww, hh  # enforce GUI values
                self.width_var.set(str(w)); self.height_var.set(str(h))
            if (self.V is not None) and (self.R is not None) and (self.R.shape != self.V.shape):
                from tkinter import messagebox
                messagebox.showerror("Shape mismatch", f"River {self.R.shape} != Vegetation {self.V.shape}")
                return
            if (self.V is None) and (self.R is not None) and (self.R.shape != (h, w)):
                from tkinter import messagebox
                messagebox.showerror("Shape mismatch", f"River shape {self.R.shape} != Grid ({h},{w})")
                return

            # clean previous
            import matplotlib.pyplot as plt
            plt.close('all'); self.stop_anim(); self.clear_canvas()

            # build model
            model = FeralCatModel(
                width=w, height=h,
                n_cats=nc, n_prey=np_,
                predation_base=pb, predation_coef=pc, prey_flee_prob=pf,
                seed=seed,
                vegetation=self.V, river=self.R
            )
            model.datacollector.collect(model)

            def _on_finished():
                self.show_plots(model)

            fig, anim = animate_grid(model, steps=st+1, interval_ms=300,
                                     title=f"Feral Cats vs Prey ({model.width}x{model.height})",
                                     scent_enabled=lambda: self.scent_var.get(),
                                     on_finished=_on_finished)

            canvas = FigureCanvasTkAgg(fig, master=self.display)
            canvas.draw()
            widget = canvas.get_tk_widget(); widget.pack(fill="both", expand=True)

            # keep refs
            self.current_fig = fig
            self.current_anim = anim
            self.canvas_widget = widget

            self.set_running_state(True)

        def pause_resume(self):
            if not self.is_running or self.current_anim is None: return
            if self.is_paused:
                self.current_anim.event_source.start()
                self.is_paused = False
                self.pause_btn.config(text="Pause")
            else:
                self.current_anim.event_source.stop()
                self.is_paused = True
                self.pause_btn.config(text="Resume")

        def reset_sim(self):
            import matplotlib.pyplot as plt
            plt.close('all'); self.stop_anim(); self.clear_canvas()
            self.set_running_state(False)

        def on_close(self):
            try:
                import matplotlib.pyplot as plt
                plt.close('all')
            except Exception:
                pass
            self.stop_anim()
            self.root.quit(); self.root.destroy(); sys.exit(0)

    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
