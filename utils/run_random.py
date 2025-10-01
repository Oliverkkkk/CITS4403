"""
GUI entry point for the Feral Cats ABM.
- Default: python run_random.py            
"""

import os, sys
import matplotlib

# Select backend 
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

#  GUI Mode
def launch_gui():
    # ***Force TkAgg to avoid conflicts before importing pyplot / visual2d***
    select_backend(interactive=True, force_tk=True)

    import tkinter as tk
    from tkinter import ttk, messagebox
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    from src.model import FeralCatModel
    from src.visual2d import animate_grid

    root = tk.Tk()
    root.title("Feral Cats ABM — Interactive GUI")

    # left panel for parameters
    CANVAS_W, CANVAS_H, DPI = 720, 720, 100
    params_frame = ttk.Frame(root, padding=10)
    params_frame.grid(row=0, column=0, sticky="nsw")
    display_frame = ttk.Frame(root, padding=10)
    display_frame.grid(row=0, column=1, sticky="nw")
    display_frame.configure(width=CANVAS_W, height=CANVAS_H)
    display_frame.grid_propagate(False)

    def add_row(r, text, var):
        ttk.Label(params_frame, text=text, width=16, anchor="w").grid(row=r, column=0, pady=3, sticky="w")
        e = ttk.Entry(params_frame, textvariable=var, width=12)
        e.grid(row=r, column=1, pady=3, sticky="w")
        return e

    width_var  = tk.StringVar(value="25")
    height_var = tk.StringVar(value="25")
    steps_var = tk.StringVar(value="100")
    cats_var = tk.StringVar(value="6")
    prey_var = tk.StringVar(value="40")
    pb_var = tk.StringVar(value="0.2")
    pc_var = tk.StringVar(value="0.1")
    pf_var = tk.StringVar(value="0.4")
    seed_var = tk.StringVar(value="")  # optional

    add_row(0, "Grid width",  width_var)
    add_row(1, "Grid height", height_var)
    add_row(2, "Steps",       steps_var)
    add_row(3, "Cats",        cats_var)
    add_row(4, "Prey",        prey_var)
    add_row(5, "predation_base (pb)", pb_var)
    add_row(6, "predation_coef (pc)", pc_var)
    add_row(7, "flee_prob (pf)", pf_var)
    add_row(8, "Seed (optional)",     seed_var)

    # right panel for animation
    display_frame = ttk.Frame(root, padding=10)
    display_frame.grid(row=0, column=1, sticky="nsew")
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    canvas_widget = None # canvas widget holder
    current_fig = None
    current_anim = None
    is_running = False
    is_paused = False

    def set_running_state(running: bool):
        # manage button states
        nonlocal is_running, is_paused
        is_running = running
        if running:
            start_btn.config(state="disabled")
            pause_btn.config(state="normal", text="Pause")
            reset_btn.config(state="normal")
        else:
            start_btn.config(state="normal")
            pause_btn.config(state="disabled", text="Pause")
            reset_btn.config(state="normal")
            is_paused = False

    def stop_current_animation():
        nonlocal current_anim
        if current_anim is not None:
            try:
                current_anim.event_source.stop()
            except Exception:
                pass
            current_anim = None


    def clear_canvas():
        nonlocal canvas_widget
        if canvas_widget is not None:
            canvas_widget.destroy()
            canvas_widget = None

    def show_plots(model):
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
            # restore main window
                set_running_state(False)
                try:
                    root.deiconify()
                    root.lift()
                    root.focus_force()
                except Exception:
                    pass

        for f in figs:
            f.canvas.mpl_connect('close_event', _on_figure_closed)
        
        plt.show(block=False)

    def start_sim():
        nonlocal canvas_widget, current_anim
        if is_running:
            # avoid multiple clicks on Start
            return

        # read & validate params
        try:
            w  = int(width_var.get())
            h  = int(height_var.get())
            st = max(1, int(steps_var.get()))
            nc = int(cats_var.get())
            np_ = int(prey_var.get())
            pb = float(pb_var.get())
            pc = float(pc_var.get())
            pf = float(pf_var.get())
            seed_txt = seed_var.get().strip()
            seed = int(seed_txt) if seed_txt else None
        except Exception:
            messagebox.showerror("Invalid input", "Please check parameter types.")
            return

        # clean previous state
        plt.close('all')
        stop_current_animation()
        clear_canvas()

        # build model
        model = FeralCatModel(width=w, height=h, n_cats=nc, n_prey=np_,
                              predation_base=pb, predation_coef=pc, prey_flee_prob = pf, seed=seed)
        model.datacollector.collect(model)

        def _on_finished():
            root.after(0, lambda: show_plots(model))

        fig, anim = animate_grid(model, steps=st + 1, interval_ms=300,
                                 title=f"Feral Cats vs Prey ({w}x{h})",
                                 on_finished=_on_finished)
        
        canvas = FigureCanvasTkAgg(fig, master=display_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)

        current_fig = fig
        canvas_widget = widget
        current_anim = anim 

        set_running_state(True)

    def pause_resume():
        nonlocal is_paused
        if not is_running or current_anim is None:
            return
        if is_paused:
            current_anim.event_source.start()
            is_paused = False
            pause_btn.config(text="Pause")
        else:
            current_anim.event_source.stop()
            is_paused = True
            pause_btn.config(text="Resume")

    def reset_sim():
        # reset to initial state
        nonlocal is_paused
        plt.close('all')
        stop_current_animation()
        clear_canvas()
        set_running_state(False)

    # control buttons
    start_btn = ttk.Button(params_frame, text="Start", command=start_sim)
    start_btn.grid(row=8, column=0, columnspan=2, pady=(12,2), sticky="ew")

    pause_btn = ttk.Button(params_frame, text="Pause", command=pause_resume, state="disabled")
    pause_btn.grid(row=9, column=0, columnspan=2, pady=2, sticky="ew")

    reset_btn = ttk.Button(params_frame, text="Reset", command=reset_sim, state="normal")
    reset_btn.grid(row=10, column=0, columnspan=2, pady=(2,0), sticky="ew")

    # Graceful exit on window close
    def on_close():
        try:
            plt.close('all')
        except Exception:
            pass
        stop_current_animation()
        root.quit()
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
        launch_gui()