"""A simple Tkinter panel for creating personalized Lifeguard tag print files.

Run from Thonny or any Python installation that has CadQuery available:

    python lifeguard_tag_app.py

The panel deliberately exposes only the choices needed for normal use. The
proven Lifeguard geometry remains in lifeguard_tag.py.
"""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from lifeguard_tag import LifeguardTagParameters, build_lifeguard_tag, export_bodies


PROJECT_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIRECTORY = PROJECT_DIRECTORY / "output"


def safe_filename_part(name: str) -> str:
    """Turn a displayed name into a predictable, filesystem-safe file stem."""
    normalized = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return normalized.strip("_") or "lifeguard_tag"


def create_print_files(
    name: str, include_keyring_hole: bool, center_mark: str, output_directory: Path
) -> tuple[Path, Path]:
    """Create the aligned tag and lettering STL files for one person."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Enter a name before creating print files.")

    model = build_lifeguard_tag(
        LifeguardTagParameters(
            name=clean_name,
            include_keyring_hole=include_keyring_hole,
            center_mark=center_mark,
        )
    )
    destination = output_directory / f"{safe_filename_part(clean_name)}_lifeguard.stl"
    return export_bodies(model, destination)


class LifeguardTagApp(ttk.Frame):
    """The small, non-CAD-facing form used for routine tag creation."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=20)
        self.master = master
        self.name = tk.StringVar()
        self.include_keyring_hole = tk.BooleanVar(value=True)
        self.center_mark = tk.StringVar(value="cross")
        self.output_directory = tk.StringVar(value=str(DEFAULT_OUTPUT_DIRECTORY))
        self.status = tk.StringVar(value="Enter a name to create a Lifeguard tag.")
        self._build()

    def _build(self) -> None:
        self.master.title("Lifeguard Tag Maker")
        self.master.resizable(False, False)
        self.grid(sticky="nsew")
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Lifeguard Tag Maker", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            self,
            text="Creates matching tag and lettering STL parts for two-colour printing.",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 18))

        ttk.Label(self, text="Name").grid(row=2, column=0, sticky="w", pady=4)
        name_entry = ttk.Entry(self, textvariable=self.name, width=32)
        name_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)
        name_entry.focus()

        ttk.Checkbutton(
            self,
            text="Include keyring hole",
            variable=self.include_keyring_hole,
        ).grid(row=3, column=1, columnspan=2, sticky="w", pady=(8, 14))

        ttk.Label(self, text="Center mark").grid(row=4, column=0, sticky="nw", pady=4)
        mark_frame = ttk.Frame(self)
        mark_frame.grid(row=4, column=1, columnspan=2, sticky="w", pady=4)
        ttk.Radiobutton(
            mark_frame,
            text="Cross with LIFEGUARD",
            variable=self.center_mark,
            value="cross",
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            mark_frame,
            text="YMCA logo",
            variable=self.center_mark,
            value="ymca",
        ).grid(row=1, column=0, sticky="w")
        ttk.Label(
            mark_frame,
            text="The YMCA layout omits the upper LIFEGUARD lettering.",
        ).grid(row=2, column=0, sticky="w", pady=(2, 0))

        ttk.Label(self, text="Output folder").grid(row=5, column=0, sticky="nw", pady=(14, 4))
        ttk.Entry(self, textvariable=self.output_directory, width=32).grid(
            row=5, column=1, sticky="ew", pady=(14, 4)
        )
        ttk.Button(self, text="Choose…", command=self.choose_output_directory).grid(
            row=5, column=2, sticky="e", padx=(8, 0), pady=(14, 4)
        )

        ttk.Separator(self).grid(row=6, column=0, columnspan=3, sticky="ew", pady=18)
        ttk.Button(self, text="Create STL Parts", command=self.create).grid(
            row=7, column=1, sticky="e"
        )
        ttk.Button(self, text="Close", command=self.master.destroy).grid(
            row=7, column=2, sticky="e", padx=(8, 0)
        )
        ttk.Label(self, textvariable=self.status, wraplength=410).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(16, 0)
        )

    def choose_output_directory(self) -> None:
        selected = filedialog.askdirectory(
            title="Choose where to save the Lifeguard tag files",
            initialdir=self.output_directory.get(),
        )
        if selected:
            self.output_directory.set(selected)

    def create(self) -> None:
        try:
            tag_path, letters_path = create_print_files(
                self.name.get(),
                self.include_keyring_hole.get(),
                self.center_mark.get(),
                Path(self.output_directory.get()).expanduser(),
            )
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not create Lifeguard tag", str(error), parent=self.master)
            return

        self.status.set(f"Created:\n{tag_path.name}\n{letters_path.name}")
        messagebox.showinfo(
            "Lifeguard tag created",
            "Load the two STL files together in Bambu Studio as one object with multiple parts.",
            parent=self.master,
        )


def main() -> None:
    root = tk.Tk()
    ttk.Style(root).configure("Title.TLabel", font=("Helvetica", 18, "bold"))
    LifeguardTagApp(root)
    # Make the small utility visible even when the editor is full-screen.
    root.update_idletasks()
    root.deiconify()
    root.lift()
    root.focus_force()
    root.attributes("-topmost", True)
    root.after(250, lambda: root.attributes("-topmost", False))
    root.mainloop()


if __name__ == "__main__":
    main()
