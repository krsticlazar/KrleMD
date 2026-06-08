import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.converter import convert_file, get_markitdown_error
from app.utils import get_output_path, open_file_in_explorer

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None


SUPPORTED_EXTENSIONS = (
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".xls",
    ".html",
    ".htm",
    ".csv",
    ".json",
    ".xml",
    ".zip",
    ".epub",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
)


if TkinterDnD is not None:

    class BaseWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._require(self)
                self.dnd_available = True
            except tk.TclError:
                self.dnd_available = False

else:

    class BaseWindow(ctk.CTk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.dnd_available = False


class KrleMDApp(BaseWindow):
    def __init__(self):
        super().__init__()

        self.title("KrleMD")
        self.geometry("620x480")
        self.minsize(600, 460)

        try:
            self.iconbitmap("assets/icon.ico")
        except tk.TclError:
            pass

        self.default_font = ctk.CTkFont(family="Segoe UI", size=13)
        self.title_font = ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
        self.subtitle_font = ctk.CTkFont(family="Segoe UI", size=13)
        self.small_font = ctk.CTkFont(family="Segoe UI", size=12)

        self.selected_file: str | None = None
        self.output_dir: str | None = None
        self.last_output_path: str | None = None
        self.is_converting = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()
        self._build_status()
        self._set_idle_state()

        import_error = get_markitdown_error()
        if import_error:
            self._set_status(import_error, "error")

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 10))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header, text="KrleMD", font=self.title_font, anchor="w")
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Convert anything to Markdown",
            font=self.subtitle_font,
            text_color=("gray35", "gray70"),
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=28, pady=(4, 8))
        content.grid_columnconfigure(0, weight=1)

        self.drop_frame = ctk.CTkFrame(
            content,
            height=130,
            border_width=2,
            border_color=("gray72", "gray35"),
            fg_color=("gray96", "gray14"),
            corner_radius=8,
        )
        self.drop_frame.grid(row=0, column=0, sticky="ew", pady=(8, 18))
        self.drop_frame.grid_propagate(False)
        self.drop_frame.grid_columnconfigure(0, weight=1)
        self.drop_frame.grid_rowconfigure(0, weight=1)
        self.drop_frame.grid_rowconfigure(1, weight=1)

        drop_title = "Drop file here or click Browse" if self.dnd_available else "Click Browse to select a file"
        self.drop_label = ctk.CTkLabel(self.drop_frame, text=drop_title, font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))
        self.drop_label.grid(row=0, column=0, sticky="s", pady=(18, 2))

        drop_hint = "Supported: PDF, DOCX, PPTX, XLSX, images, HTML, CSV, EPUB, ZIP"
        self.drop_hint_label = ctk.CTkLabel(self.drop_frame, text=drop_hint, font=self.small_font, text_color=("gray40", "gray66"))
        self.drop_hint_label.grid(row=1, column=0, sticky="n", pady=(2, 18))

        self.drop_frame.bind("<Button-1>", lambda _event: self.browse_file())
        self.drop_label.bind("<Button-1>", lambda _event: self.browse_file())
        self.drop_hint_label.bind("<Button-1>", lambda _event: self.browse_file())

        if self.dnd_available:
            self._enable_drop_target(self.drop_frame)
            self._enable_drop_target(self.drop_label)
            self._enable_drop_target(self.drop_hint_label)

        selected_row = ctk.CTkFrame(content, fg_color="transparent")
        selected_row.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        selected_row.grid_columnconfigure(1, weight=1)

        selected_label = ctk.CTkLabel(selected_row, text="Selected:", width=90, anchor="w", font=self.default_font)
        selected_label.grid(row=0, column=0, sticky="w")

        self.selected_var = tk.StringVar(value="No file selected")
        self.selected_entry = ctk.CTkEntry(selected_row, textvariable=self.selected_var, state="disabled", font=self.default_font)
        self.selected_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        browse_button = ctk.CTkButton(selected_row, text="Browse", width=92, command=self.browse_file, font=self.default_font)
        browse_button.grid(row=0, column=2)

        output_row = ctk.CTkFrame(content, fg_color="transparent")
        output_row.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        output_row.grid_columnconfigure(1, weight=1)

        output_label = ctk.CTkLabel(output_row, text="Output folder:", width=90, anchor="w", font=self.default_font)
        output_label.grid(row=0, column=0, sticky="w")

        self.output_var = tk.StringVar(value="Same as input folder")
        self.output_entry = ctk.CTkEntry(output_row, textvariable=self.output_var, state="disabled", font=self.default_font)
        self.output_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        output_browse_button = ctk.CTkButton(output_row, text="Browse", width=92, command=self.browse_output_folder, font=self.default_font)
        output_browse_button.grid(row=0, column=2)

        self.same_folder_button = ctk.CTkButton(
            output_row,
            text="Same",
            width=72,
            fg_color=("gray78", "gray30"),
            hover_color=("gray70", "gray38"),
            text_color=("gray10", "gray95"),
            command=self.use_input_folder,
            font=self.default_font,
        )
        self.same_folder_button.grid(row=0, column=3, padx=(8, 0))

        self.convert_button = ctk.CTkButton(
            content,
            text="Convert to Markdown",
            height=44,
            command=self.start_conversion,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        )
        self.convert_button.grid(row=3, column=0, sticky="ew", pady=(4, 14))

        self.progress = ctk.CTkProgressBar(content, mode="indeterminate", height=6)
        self.progress.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        self.progress.grid_remove()

        separator = ctk.CTkFrame(content, height=1, fg_color=("gray80", "gray28"))
        separator.grid(row=5, column=0, sticky="ew", pady=(4, 12))

    def _build_status(self) -> None:
        status = ctk.CTkFrame(self, fg_color="transparent")
        status.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 22))
        status.grid_columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(status, textvariable=self.status_var, anchor="w", font=self.default_font)
        self.status_label.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.open_button = ctk.CTkButton(status, text="Open", width=84, command=self.open_last_output, font=self.default_font)
        self.open_button.grid(row=0, column=1)

    def _enable_drop_target(self, widget) -> None:
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", self.handle_drop)

    def browse_file(self) -> None:
        filetypes = [
            ("Supported files", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select a file", filetypes=filetypes)
        if path:
            self.set_selected_file(path)

    def browse_output_folder(self) -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_dir = path
            self.output_var.set(path)

    def use_input_folder(self) -> None:
        self.output_dir = None
        self.output_var.set("Same as input folder")

    def handle_drop(self, event) -> str:
        paths = self.tk.splitlist(event.data)
        if not paths:
            return event.action

        self.set_selected_file(paths[0])
        return event.action

    def set_selected_file(self, path: str) -> None:
        file_path = Path(path)

        if not file_path.is_file():
            self._set_status("Please select a file.", "error")
            return

        self.selected_file = str(file_path)
        self.selected_var.set(str(file_path))
        self.last_output_path = None
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            self._set_status("Ready", "neutral")
        else:
            self._set_status("File selected. Conversion support depends on MarkItDown.", "neutral")
        self._set_idle_state()

    def start_conversion(self) -> None:
        if not self.selected_file or self.is_converting:
            return

        import_error = get_markitdown_error()
        if import_error:
            self._set_status(import_error, "error")
            messagebox.showerror("MarkItDown setup required", import_error)
            return

        output_path = get_output_path(self.selected_file, self.output_dir)
        self.is_converting = True
        self.last_output_path = None
        self._set_status("Converting...", "neutral")
        self._set_converting_state()

        worker = threading.Thread(target=self._convert_in_background, args=(self.selected_file, output_path), daemon=True)
        worker.start()

    def _convert_in_background(self, input_path: str, output_path: str) -> None:
        success, message = convert_file(input_path, output_path)
        self.after(0, self._finish_conversion, success, message, output_path)

    def _finish_conversion(self, success: bool, message: str, output_path: str) -> None:
        self.is_converting = False

        if success:
            self.last_output_path = output_path
            self._set_status(f"Done! Saved to: {self._shorten_path(output_path)}", "success")
        else:
            self.last_output_path = None
            self._set_status(message or "Conversion failed.", "error")

        self._set_idle_state()

    def open_last_output(self) -> None:
        if self.last_output_path:
            open_file_in_explorer(self.last_output_path)

    def _set_converting_state(self) -> None:
        self.convert_button.configure(text="Converting...", state="disabled")
        self.open_button.configure(state="disabled")
        self.progress.grid()
        self.progress.start()

    def _set_idle_state(self) -> None:
        self.progress.stop()
        self.progress.grid_remove()
        self.convert_button.configure(
            text="Convert to Markdown",
            state="normal" if self.selected_file and not self.is_converting else "disabled",
        )
        self.open_button.configure(state="normal" if self.last_output_path else "disabled")

    def _set_status(self, message: str, level: str) -> None:
        colors = {
            "success": ("#0f7b3a", "#35d07f"),
            "error": ("#b42318", "#ff7a70"),
            "neutral": ("gray35", "gray72"),
        }
        self.status_var.set(message)
        self.status_label.configure(text_color=colors.get(level, colors["neutral"]))

    def _shorten_path(self, path: str, max_length: int = 72) -> str:
        if len(path) <= max_length:
            return path

        output_path = Path(path)
        compact = f"...\\{output_path.parent.name}\\{output_path.name}"
        if len(compact) <= max_length:
            return compact

        return f"...\\{output_path.name}"
