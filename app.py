import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
import os
import csv

# Get absolute path for VS Code reliability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- CTI VALUES ----------------
CTI_Q1_Q4 = 0.150
CTI_Q1_Q5 = 0.300
CTI_Q4_Q5 = 0.150

# ---------------- VALIDATION ----------------
def validate_numeric(P):
    if P == "":
        return True
    try:
        float(P)
        return True
    except ValueError:
        if P == ".":
            return True
        return False

# ---------------- IEC CURVE ----------------
def iec_curve(I, Ip, TMS, curve):
    if I <= Ip:
        return np.nan
    curves = {
        "Standard Inverse": (0.14, 0.02),
        "Very Inverse": (13.5, 1),
        "Extremely Inverse": (80, 2),
    }
    k, alpha = curves[curve]
    M = I / Ip
    return TMS * (k / ((M ** alpha) - 1))

# ---------------- TRANSFORMER CALC ----------------
def transformer_calculations():
    try:
        MVA = float(entry_mva.get())
        LV = float(entry_lv.get())
        HV = float(entry_hv.get())
        Z = float(entry_z.get())
        FLC_LV = (MVA * 1000) / (np.sqrt(3) * LV)
        Isc_LV = FLC_LV / (Z / 100)
        HV_factor = HV / LV
        label_flc.config(text=f"FLC (LV) = {FLC_LV:.3f} A")
        label_isc.config(text=f"Isc (LV) = {Isc_LV:.3f} A")
        return FLC_LV, Isc_LV, HV_factor
    except:
        label_flc.config(text="FLC (LV) = -")
        label_isc.config(text="Isc (LV) = -")
        return None, None, 1

# ---------------- PLOT FUNCTION ----------------
def plot_curves():
    ax.clear()
    ax.set_title("Time-Current Characteristics", fontsize=14, fontweight="bold")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Current (A)", fontsize=12)
    ax.set_ylabel("Time (s)", fontsize=12)
    ax.grid(True, which="both", linestyle="--", alpha=0.7)

    currents = np.logspace(1, 5, 800)
    FLC_LV, Isc_LV, HV_factor = transformer_calculations()

    # NOTE: Transformer Damage Curve and Inrush Point logic removed from here

    try:
        fault_current = float(entry_fault.get())
    except:
        fault_current = None

    if Isc_LV and fault_current and fault_current > Isc_LV:
        messagebox.showwarning("Warning", "Fault current exceeds LV short circuit current.")
        fault_current = Isc_LV

    trip_times = {}
    colors = ["blue", "green", "red", "purple", "orange"]

    for i in range(5):
        try:
            Ip = float(pickups[i].get())
            TMS = float(tms_values[i].get())
            curve = curve_boxes[i].get()
        except:
            continue

        current_scaling = HV_factor if i == 4 else 1
        merged_curve = []

        for I in currents:
            I_scaled = I / current_scaling
            times = []
            if idmt_vars[i].get() == 1:
                t_idmt = iec_curve(I_scaled, Ip, TMS, curve)
                if not np.isnan(t_idmt): times.append(t_idmt)
            if dt1_vars[i].get() == 1:
                try:
                    if I_scaled >= float(dt1_pickups[i].get()): times.append(float(dt1_times[i].get()))
                except: pass
            if i >= 3 and dt2_vars[i].get() == 1:
                try:
                    if I_scaled >= float(dt2_pickups[i].get()): times.append(float(dt2_times[i].get()))
                except: pass
            merged_curve.append(min(times) if times else np.nan)

        merged_curve = np.array(merged_curve)
        ax.plot(currents, merged_curve, color=colors[i], linewidth=2.5, label=f"Q{i+1}")

        if fault_current:
            I_fault_scaled = fault_current / current_scaling
            intersection_times = []
            if idmt_vars[i].get() == 1:
                t_f = iec_curve(I_fault_scaled, Ip, TMS, curve)
                if not np.isnan(t_f): intersection_times.append(t_f)
            if dt1_vars[i].get() == 1:
                try:
                    if I_fault_scaled >= float(dt1_pickups[i].get()): intersection_times.append(float(dt1_times[i].get()))
                except: pass
            if i >= 3 and dt2_vars[i].get() == 1:
                try:
                    if I_fault_scaled >= float(dt2_pickups[i].get()): intersection_times.append(float(dt2_times[i].get()))
                except: pass
            if intersection_times:
                t_res = min(intersection_times)
                trip_times[f"Q{i+1}"] = round(t_res, 3)
                ax.plot(fault_current, t_res, 'o', color=colors[i])
                ax.text(fault_current, t_res, f"{t_res:.3f}s", fontsize=9)

    if fault_current:
        ax.axvline(fault_current, linestyle="dotted", color="black", linewidth=2, label="Fault Level")
    ax.legend()
    canvas.draw()
    update_report(trip_times, FLC_LV, Isc_LV, fault_current)

# ---------------- REPORT ----------------
def update_report(trip_times, FLC_LV, Isc_LV, fault_current):
    report_text.delete("1.0", tk.END)
    report_text.insert(tk.END, "Coordination Report\n" + "="*20 + "\n")
    if FLC_LV:
        report_text.insert(tk.END, f"LV FLC: {FLC_LV:.3f} A | LV Isc: {Isc_LV:.3f} A\n")
    if fault_current:
        report_text.insert(tk.END, f"Fault Current: {fault_current:.3f} A\n\n")
    for q in sorted(trip_times.keys()):
        report_text.insert(tk.END, f"{q} Trip: {trip_times[q]:.3f} s\n")
    report_text.insert(tk.END, "\nCoordination Results:\n")
    checks = [("Q1", "Q4", CTI_Q1_Q4), ("Q2", "Q4", CTI_Q1_Q4), ("Q3", "Q4", CTI_Q1_Q4),
              ("Q1", "Q5", CTI_Q1_Q5), ("Q2", "Q5", CTI_Q1_Q5), ("Q3", "Q5", CTI_Q1_Q5),
              ("Q4", "Q5", CTI_Q4_Q5)]
    for d, u, c in checks:
        if d in trip_times and u in trip_times:
            m = trip_times[u] - trip_times[d]
            tag = "green" if m >= c else "red"
            report_text.insert(tk.END, f"{d}->{u}: {m:.3f}s {'OK' if m >= c else 'NOT OK'}\n", tag)
    report_text.tag_config("green", foreground="green")
    report_text.tag_config("red", foreground="red")

# ---------------- ACTIONS ----------------
def new_project():
    entry_mva.delete(0, tk.END); entry_hv.delete(0, tk.END)
    entry_lv.delete(0, tk.END); entry_z.delete(0, tk.END)
    entry_fault.delete(0, tk.END)
    for i in range(5):
        pickups[i].delete(0, tk.END); tms_values[i].delete(0, tk.END)
        dt1_pickups[i].delete(0, tk.END); dt1_times[i].delete(0, tk.END)
        dt2_pickups[i].delete(0, tk.END); dt2_times[i].delete(0, tk.END)
        idmt_vars[i].set(0); dt1_vars[i].set(0); dt2_vars[i].set(0)
    ax.clear(); canvas.draw(); report_text.delete("1.0", tk.END)
    label_flc.config(text="FLC = -"); label_isc.config(text="Isc = -")

def prefill_data():
    entry_mva.delete(0, tk.END); entry_mva.insert(0, "16.6")
    entry_hv.delete(0, tk.END); entry_hv.insert(0, "33")
    entry_lv.delete(0, tk.END); entry_lv.insert(0, "11")
    entry_z.delete(0, tk.END); entry_z.insert(0, "10")
    entry_fault.delete(0, tk.END); entry_fault.insert(0, "7900")
    defaults = [[220, 0.025, 600, 0.0, 0, 0.0], [275, 0.025, 750, 0.0, 0, 0.0], 
                [330, 0.025, 900, 0.0, 0, 0.0], [825, 0.07, 2250, 0.15, 8000, 0.0],
                [275, 0.12, 750, 0.3, 2666.67, 0.0]]
    for i, v in enumerate(defaults):
        pickups[i].delete(0, tk.END); pickups[i].insert(0, v[0])
        tms_values[i].delete(0, tk.END); tms_values[i].insert(0, v[1])
        dt1_pickups[i].delete(0, tk.END); dt1_pickups[i].insert(0, v[2])
        dt1_times[i].delete(0, tk.END); dt1_times[i].insert(0, v[3])
        dt2_pickups[i].delete(0, tk.END); dt2_pickups[i].insert(0, v[4])
        dt2_times[i].delete(0, tk.END); dt2_times[i].insert(0, v[5])
        idmt_vars[i].set(1); dt1_vars[i].set(1); dt2_vars[i].set(1)
    transformer_calculations()

def save_pdf():
    file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
    if not file_path: return
    with PdfPages(file_path) as pdf:
        pdf.savefig(fig)
        fig_rep, ax_rep = plt.subplots(figsize=(11, 8.5)); ax_rep.axis('off')
        ax_rep.text(0.5, 0.95, "Relay Settings & Coordination Report", fontsize=16, weight='bold', ha='center')
        headers = ["Relay", "IDMT", "Pick", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2"]
        rows = []
        for i in range(5):
            rows.append([f"Q{i+1}", "ON" if idmt_vars[i].get() else "OFF", 
                         f"{float(pickups[i].get()):.3f}", f"{float(tms_values[i].get()):.3f}",
                         "ON" if dt1_vars[i].get() else "OFF", f"{float(dt1_pickups[i].get()):.3f}", f"{float(dt1_times[i].get()):.3f}",
                         "ON" if dt2_vars[i].get() else "OFF", f"{float(dt2_pickups[i].get()):.3f}", f"{float(dt2_times[i].get()):.3f}"])
        table = ax_rep.table(cellText=rows, colLabels=headers, loc='center', cellLoc='center', bbox=[0.05, 0.5, 0.9, 0.35])
        table.auto_set_font_size(False); table.set_fontsize(10)
        summary = report_text.get("1.0", tk.END)
        ax_rep.text(0.05, 0.45, "Results Summary:", fontsize=12, weight='bold')
        ax_rep.text(0.05, 0.43, summary, fontsize=10, family='monospace', va='top')
        pdf.savefig(fig_rep); plt.close(fig_rep)
    messagebox.showinfo("Saved", f"File saved:\n{file_path}")

def export_to_excel():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV (Excel)","*.csv")])
    if not file_path: return
    try:
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["NEA PROTECTION TOOL REPORT"])
            writer.writerow([])
            writer.writerow(["--- Transformer Data ---"])
            writer.writerow(["Rating (MVA)", entry_mva.get()])
            writer.writerow(["HV Voltage (kV)", entry_hv.get()])
            writer.writerow(["LV Voltage (kV)", entry_lv.get()])
            writer.writerow(["Impedance (%)", entry_z.get()])
            writer.writerow(["FLC (LV)", label_flc.cget("text")])
            writer.writerow(["Isc (LV)", label_isc.cget("text")])
            writer.writerow([])
            writer.writerow(["--- Relay Settings ---"])
            writer.writerow(["Relay", "IDMT", "Pickup", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2", "Curve"])
            for i in range(5):
                writer.writerow([f"Q{i+1}", idmt_vars[i].get(), pickups[i].get(), tms_values[i].get(), 
                                 dt1_vars[i].get(), dt1_pickups[i].get(), dt1_times[i].get(), 
                                 dt2_vars[i].get(), dt2_pickups[i].get(), dt2_times[i].get(), curve_boxes[i].get()])
        messagebox.showinfo("Success", f"Data exported successfully to:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export: {e}")

# ---------------- GUI INIT ----------------
root = tk.Tk()
root.title("NEA Protection Coordination Tool")
root.geometry("1800x950")
root.configure(bg="#e6e6e6")

vcmd = (root.register(validate_numeric), '%P')

menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="New Project (Reset All)", command=new_project)
file_menu.add_command(label="Prefill Defaults", command=prefill_data)
file_menu.add_command(label="Save Report (PDF)", command=save_pdf)
file_menu.add_command(label="Export to Excel (CSV)", command=export_to_excel)
menubar.add_cascade(label="File", menu=file_menu); root.config(menu=menubar)

left = tk.Frame(root, bg="#e6e6e6"); left.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=10)
right = tk.Frame(root, bg="#ffffff"); right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

top_info_frame = tk.Frame(left, bg="#e6e6e6"); top_info_frame.pack(fill="x", pady=5)
tf = tk.LabelFrame(top_info_frame, text="Transformer Data", font=("Arial", 11, "bold"), padx=5, pady=5)
tf.pack(side=tk.LEFT, fill="both", expand=True)

try:
    logo_path = os.path.join(BASE_DIR, "logo.jpg")
    l_img = Image.open(logo_path).resize((100, 100), Image.LANCZOS)
    l_photo = ImageTk.PhotoImage(l_img)
    logo_label = tk.Label(top_info_frame, image=l_photo, bg="#e6e6e6"); logo_label.image = l_photo
    logo_label.pack(side=tk.RIGHT, padx=10)
except: pass

entry_mva = tk.Entry(tf, width=10, validate='key', validatecommand=vcmd)
entry_hv = tk.Entry(tf, width=10, validate='key', validatecommand=vcmd)
entry_lv = tk.Entry(tf, width=10, validate='key', validatecommand=vcmd)
entry_z = tk.Entry(tf, width=10, validate='key', validatecommand=vcmd)

tk.Label(tf, text="Rating (MVA)").grid(row=0, column=0); entry_mva.grid(row=0, column=1)
tk.Label(tf, text="HV (kV)").grid(row=1, column=0); entry_hv.grid(row=1, column=1)
tk.Label(tf, text="LV (kV)").grid(row=2, column=0); entry_lv.grid(row=2, column=1)
tk.Label(tf, text="Impedance (%)").grid(row=3, column=0); entry_z.grid(row=3, column=1)
label_flc = tk.Label(tf, text="FLC = -", fg="blue"); label_flc.grid(row=4, column=0, columnspan=2)
label_isc = tk.Label(tf, text="Isc = -", fg="blue"); label_isc.grid(row=5, column=0, columnspan=2)

ff = tk.LabelFrame(left, text="Fault Data", font=("Arial", 11, "bold")); ff.pack(fill="x", pady=5)
tk.Label(ff, text="Fault (A)").pack(side=tk.LEFT)
entry_fault = tk.Entry(ff, width=10, validate='key', validatecommand=vcmd); entry_fault.pack(side=tk.LEFT, padx=5)

rf = tk.LabelFrame(left, text="Relay Settings", font=("Arial", 11, "bold"), padx=5, pady=5); rf.pack(fill="x", pady=5)
headers = ["Relay", "IDMT", "Pick", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2", "Curve"]
for col, text in enumerate(headers): tk.Label(rf, text=text, font=("Arial", 8, "bold")).grid(row=0, column=col)

pickups, tms_values, dt1_pickups, dt1_times, dt2_pickups, dt2_times, curve_boxes = [], [], [], [], [], [], []
idmt_vars, dt1_vars, dt2_vars = [], [], []

for i in range(5):
    tk.Label(rf, text=f"Q{i+1}").grid(row=i+1, column=0)
    iv, d1v, d2v = tk.IntVar(), tk.IntVar(), tk.IntVar()
    tk.Checkbutton(rf, variable=iv).grid(row=i+1, column=1)
    p = tk.Entry(rf, width=5, vcmd=vcmd, validate='key'); p.grid(row=i+1, column=2); pickups.append(p)
    t = tk.Entry(rf, width=5, vcmd=vcmd, validate='key'); t.grid(row=i+1, column=3); tms_values.append(t)
    tk.Checkbutton(rf, variable=d1v).grid(row=i+1, column=4)
    dp1 = tk.Entry(rf, width=5, vcmd=vcmd, validate='key'); dp1.grid(row=i+1, column=5); dt1_pickups.append(dp1)
    dt1 = tk.Entry(rf, width=5, vcmd=vcmd, validate='key'); dt1.grid(row=i+1, column=6); dt1_times.append(dt1)
    tk.Checkbutton(rf, variable=d2v).grid(row=i+1, column=7)
    dp2 = tk.Entry(rf, width=7, vcmd=vcmd, validate='key'); dp2.grid(row=i+1, column=8); dt2_pickups.append(dp2)
    dt2 = tk.Entry(rf, width=5, vcmd=vcmd, validate='key'); dt2.grid(row=i+1, column=9); dt2_times.append(dt2)
    c = ttk.Combobox(rf, values=["Standard Inverse", "Very Inverse", "Extremely Inverse"], width=15, state="readonly")
    c.current(0); c.grid(row=i+1, column=10); curve_boxes.append(c)
    idmt_vars.append(iv); dt1_vars.append(d1v); dt2_vars.append(d2v)

tk.Button(left, text="Plot Coordination", bg="#007acc", fg="white", font=("Arial", 11, "bold"), command=plot_curves).pack(pady=10, fill="x")

try:
    sld_path = os.path.join(BASE_DIR, "sld.png")
    s_img = Image.open(sld_path).resize((240, 260), Image.LANCZOS)
    s_photo = ImageTk.PhotoImage(s_img)
    lbl_sld = tk.Label(left, image=s_photo, bg="#e6e6e6")
    lbl_sld.image = s_photo
    lbl_sld.pack(pady=5)
except: pass

dev_label = tk.Label(left, text="Protection and Automation Division, GOD", fg="red", bg="#e6e6e6", font=("Arial", 10, "bold"))
dev_label.pack(pady=5)

fig = plt.Figure(figsize=(10, 6)); ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=right); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
report_text = tk.Text(right, height=12, bg="black", fg="white", font=("Arial", 11)); report_text.pack(fill=tk.X)

prefill_data()
root.mainloop()
