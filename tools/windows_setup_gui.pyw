"""Optional Tkinter setup for Orbit Remote Commander (per-user, local-only)."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from windows_setup import install, status, uninstall, location

root = tk.Tk()
root.title("Orbit Remote Commander — Local Setup")
root.geometry("650x400")
root.minsize(530, 360)

tk.Label(root, text="Orbit Remote Commander", font=("Segoe UI", 18, "bold")).pack(pady=(18, 6))
tk.Label(root, text="Local read-only companion. No internet connection or ChatGPT pairing is created.",
         wraplength=590).pack(pady=(0, 14))
project = tk.StringVar()
tk.Label(root, text="Select one trusted project folder:").pack()
entry = tk.Entry(root, textvariable=project, width=72)
entry.pack(padx=20, pady=(6, 6), fill="x")
tk.Button(root, text="Browse folder", command=lambda: project.set(filedialog.askdirectory() or project.get())).pack()
display = tk.Text(root, height=10, wrap="word")
display.pack(padx=20, pady=14, fill="both", expand=True)
display.insert("1.0", "Choose a project folder, then Preview. Read-only by default.")
display.config(state="disabled")


def show(value):
    display.config(state="normal")
    display.delete("1.0", "end")
    display.insert("1.0", json.dumps(value, indent=2))
    display.config(state="disabled")


def run(action):
    try:
        home = location()
        if action == "preview":
            show(install(home, project.get() or None, apply=False))
        elif action == "install":
            plan = install(home, project.get() or None, apply=False)
            show(plan)
            if messagebox.askyesno("Confirm local setup",
                "Install these files only for your current user?\n"
                "No remote access is enabled. No IDE or startup changes."):
                show(install(home, project.get() or None, apply=True))
        elif action == "status":
            show(status(home))
        elif action == "uninstall":
            show(uninstall(home, apply=False))
            if messagebox.askyesno("Confirm local uninstall",
                "Remove verified Orbit Remote Commander program files?\n"
                "Project configuration is preserved unless separately removed."):
                show(uninstall(home, apply=True))
    except (ValueError, OSError, KeyError) as exc:
        show({"status": "BLOCKED", "reason": str(exc)})


actions = tk.Frame(root)
actions.pack(pady=(0, 14))
for label, action in (("Preview", "preview"), ("Install", "install"),
                      ("Status", "status"), ("Uninstall", "uninstall")):
    tk.Button(actions, text=label, width=12, command=lambda a=action: run(a)).pack(side="left", padx=5)

root.mainloop()
