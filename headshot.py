import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import os
import threading

class HeadshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Staff Headshot Processor")
        self.root.geometry("820x680")
        self.root.resizable(True, True)
        self.root.configure(bg="#f5f5f5")

        self.files = []
        self.previews = []
        self.output_folder = tk.StringVar(value="")
        self.size_var = tk.IntVar(value=200)
        self.face_pos_var = tk.IntVar(value=22)
        self.zoom_var = tk.IntVar(value=100)
        self.status_var = tk.StringVar(value="No images loaded")

        self._build_ui()

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg="#1a1a1a", pady=12)
        top.pack(fill="x")
        tk.Label(top, text="Staff Headshot Processor", font=("Segoe UI", 14, "bold"),
                 fg="white", bg="#1a1a1a").pack(side="left", padx=16)

        # Main layout
        main = tk.Frame(self.root, bg="#f5f5f5")
        main.pack(fill="both", expand=True, padx=14, pady=10)

        # Left panel - controls
        left = tk.Frame(main, bg="#ffffff", relief="flat", bd=0,
                        highlightthickness=1, highlightbackground="#e0e0e0", width=220)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self._section(left, "Input")
        btn_add = tk.Button(left, text="+ Add Images", command=self._add_files,
                            bg="#1a1a1a", fg="white", font=("Segoe UI", 10),
                            relief="flat", padx=10, pady=6, cursor="hand2")
        btn_add.pack(fill="x", padx=12, pady=(0, 4))

        btn_folder = tk.Button(left, text="+ Add Folder", command=self._add_folder,
                               bg="#444", fg="white", font=("Segoe UI", 10),
                               relief="flat", padx=10, pady=6, cursor="hand2")
        btn_folder.pack(fill="x", padx=12, pady=(0, 8))

        btn_clear = tk.Button(left, text="Clear All", command=self._clear,
                              bg="#f0f0f0", fg="#555", font=("Segoe UI", 9),
                              relief="flat", padx=10, pady=4, cursor="hand2")
        btn_clear.pack(fill="x", padx=12, pady=(0, 12))

        self._section(left, "Output Size (px)")
        size_frame = tk.Frame(left, bg="#ffffff")
        size_frame.pack(fill="x", padx=12, pady=(0, 12))
        for s in [100, 150, 200, 300, 400]:
            rb = tk.Radiobutton(size_frame, text=str(s), variable=self.size_var,
                                value=s, bg="#ffffff", font=("Segoe UI", 9),
                                command=self._refresh_previews)
            rb.pack(side="left")
        tk.Entry(size_frame, textvariable=self.size_var, width=5,
                 font=("Segoe UI", 9)).pack(side="left", padx=(6, 0))

        self._section(left, "Crop Adjustment")
        self._slider(left, "Face position (from top)", self.face_pos_var, 5, 55, "%")
        self._slider(left, "Zoom", self.zoom_var, 50, 200, "×", scale=100)

        self._section(left, "Output Folder")
        out_frame = tk.Frame(left, bg="#ffffff")
        out_frame.pack(fill="x", padx=12, pady=(0, 4))
        tk.Entry(out_frame, textvariable=self.output_folder, font=("Segoe UI", 8),
                 width=18).pack(side="left", fill="x", expand=True)
        tk.Button(out_frame, text="…", command=self._pick_output,
                  bg="#e8e8e8", relief="flat", padx=4, cursor="hand2").pack(side="left", padx=(4, 0))

        tk.Label(left, text="(leave blank = same as source)", font=("Segoe UI", 8),
                 fg="#888", bg="#ffffff").pack(padx=12, anchor="w", pady=(0, 12))

        btn_process = tk.Button(left, text="Process & Save All", command=self._process,
                                bg="#2563eb", fg="white", font=("Segoe UI", 11, "bold"),
                                relief="flat", padx=10, pady=10, cursor="hand2")
        btn_process.pack(fill="x", padx=12, pady=(4, 12))

        self.progress = ttk.Progressbar(left, mode="determinate")
        self.progress.pack(fill="x", padx=12, pady=(0, 8))

        # Right panel - preview grid
        right = tk.Frame(main, bg="#f5f5f5")
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Preview", font=("Segoe UI", 10, "bold"),
                 bg="#f5f5f5", fg="#333").pack(anchor="w", pady=(0, 6))

        self.canvas = tk.Canvas(right, bg="#f5f5f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(right, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg="#f5f5f5")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self.canvas_window, width=e.width))

        # Status bar
        status_bar = tk.Frame(self.root, bg="#e8e8e8", pady=4)
        status_bar.pack(fill="x", side="bottom")
        tk.Label(status_bar, textvariable=self.status_var, font=("Segoe UI", 9),
                 bg="#e8e8e8", fg="#555").pack(side="left", padx=12)

    def _section(self, parent, text):
        tk.Label(parent, text=text.upper(), font=("Segoe UI", 8, "bold"),
                 fg="#888", bg="#ffffff").pack(anchor="w", padx=12, pady=(14, 4))

    def _slider(self, parent, label, var, mn, mx, unit, scale=None):
        frame = tk.Frame(parent, bg="#ffffff")
        frame.pack(fill="x", padx=12, pady=(0, 8))
        val_label = tk.Label(frame, font=("Segoe UI", 9), bg="#ffffff", fg="#333", width=6)
        val_label.pack(side="right")

        def update(e=None):
            if scale:
                val_label.config(text=f"{var.get()/scale:.1f}{unit}")
            else:
                val_label.config(text=f"{var.get()}{unit}")
            self._refresh_previews()

        tk.Label(frame, text=label, font=("Segoe UI", 9), bg="#ffffff", fg="#555").pack(anchor="w")
        sl = tk.Scale(frame, variable=var, from_=mn, to=mx, orient="horizontal",
                      showvalue=False, bg="#ffffff", highlightthickness=0,
                      troughcolor="#e0e0e0", command=update)
        sl.pack(fill="x")
        update()

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"), ("All", "*.*")])
        for p in paths:
            if p not in self.files:
                self.files.append(p)
        self._refresh_previews()

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if not folder:
            return
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() in exts:
                p = os.path.join(folder, f)
                if p not in self.files:
                    self.files.append(p)
        self._refresh_previews()

    def _clear(self):
        self.files = []
        self.previews = []
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.status_var.set("No images loaded")

    def _pick_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

    def _make_circle(self, path, size, face_pct, zoom):
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        z = zoom / 100.0
        src_size = int(min(w, h) / z)
        src_x = (w - src_size) // 2
        src_y = int(h * face_pct / 100) - int(src_size * 0.2)
        src_y = max(0, min(src_y, h - src_size))
        cropped = img.crop((src_x, src_y, src_x + src_size, src_y + src_size))
        cropped = cropped.resize((size, size), Image.LANCZOS)

        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size - 1, size - 1), fill=255)

        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(cropped, (0, 0), mask)
        return result

    def _refresh_previews(self):
        self.previews = []
        for w in self.grid_frame.winfo_children():
            w.destroy()
        if not self.files:
            self.status_var.set("No images loaded")
            return

        THUMB = 100
        cols = 4
        face_pct = self.face_pos_var.get()
        zoom = self.zoom_var.get()

        for i, path in enumerate(self.files):
            try:
                img = self._make_circle(path, THUMB, face_pct, zoom)
                tk_img = ImageTk.PhotoImage(img)
                self.previews.append(tk_img)

                card = tk.Frame(self.grid_frame, bg="#ffffff",
                                highlightthickness=1, highlightbackground="#e0e0e0")
                card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nw")

                lbl = tk.Label(card, image=tk_img, bg="#ffffff")
                lbl.pack(padx=8, pady=(8, 4))

                name = os.path.basename(path)
                name = name[:16] + "…" if len(name) > 16 else name
                tk.Label(card, text=name, font=("Segoe UI", 8), fg="#666",
                         bg="#ffffff", wraplength=100).pack(padx=4, pady=(0, 8))
            except Exception:
                pass

        self.status_var.set(f"{len(self.files)} image(s) loaded — preview at 100px")

    def _process(self):
        if not self.files:
            messagebox.showwarning("No Images", "Please add some images first.")
            return
        threading.Thread(target=self._do_process, daemon=True).start()

    def _do_process(self):
        size = self.size_var.get()
        face_pct = self.face_pos_var.get()
        zoom = self.zoom_var.get()
        out_base = self.output_folder.get()
        total = len(self.files)
        done = 0
        errors = 0

        self.progress["maximum"] = total

        for path in self.files:
            try:
                result = self._make_circle(path, size, face_pct, zoom)
                folder = out_base if out_base else os.path.dirname(path)
                base = os.path.splitext(os.path.basename(path))[0]
                out_path = os.path.join(folder, f"{base}_headshot.png")
                result.save(out_path, "PNG")
                done += 1
            except Exception:
                errors += 1
            self.progress["value"] = done + errors
            self.status_var.set(f"Processing... {done + errors}/{total}")

        msg = f"Done! {done} saved"
        if errors:
            msg += f", {errors} failed"
        self.status_var.set(msg)
        self.progress["value"] = 0
        messagebox.showinfo("Complete", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = HeadshotApp(root)
    root.mainloop()
