"""Desktop form for creating a general name tag 3MF.

Run with a Python installation that has CadQuery installed:

    python nametag_app.py

This app uses nametag_builder.py and is independent of the Lifeguard tag tools.
"""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, font as tkfont, messagebox, ttk

from nametag_builder import (
    NameTagParameters,
    build_name_tag_parts,
    export_name_tag_3mf,
)


PROJECT_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIRECTORY = PROJECT_DIRECTORY / "output"
TEXT_STYLES = {
    "Embossed (raised)": "raised",
    "Embedded (inlaid)": "inlaid",
    "Engraved (recessed)": "engraved",
}


def safe_filename_part(name: str) -> str:
    """Convert a displayed name to a filesystem-safe filename stem."""
    normalized = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return normalized.strip("_") or "name_tag"


def create_name_tag_file(
    name: str,
    length: float,
    width: float,
    font_size: float,
    font_name: str,
    text_style: str,
    letter_colors: list[str],
    base_color: str,
    output_directory: Path,
) -> Path:
    """Build a color-aware name tag and save its 3MF in *output_directory*."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Enter a name before creating the tag.")

    clean_font = font_name.strip()
    if not clean_font:
        raise ValueError("Enter a font name.")

    style_key = TEXT_STYLES.get(text_style)
    if style_key is None:
        raise ValueError("Choose Embossed, Embedded, or Engraved text.")

    params = NameTagParameters(
        name=clean_name,
        width=length,
        height=width,
        text_height=font_size,
        font=clean_font,
    )
    base, letter_parts = build_name_tag_parts(params, text_style=style_key)
    destination = output_directory.expanduser() / f"{safe_filename_part(clean_name)}_name_tag.3mf"
    return export_name_tag_3mf(
        base,
        letter_parts,
        letter_colors,
        destination,
        base_color=base_color,
    )


class NameTagApp(ttk.Frame):
    """Simple form for the general name tag model."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=20)
        self.master = master
        self.name = tk.StringVar()
        self.length = tk.StringVar(value="75")
        self.width = tk.StringVar(value="28")
        self.font_size = tk.StringVar(value="14")
        self.font_name = tk.StringVar(value="Arial")
        self.text_style = tk.StringVar(value="Embossed (raised)")
        self.letter_colors: list[str] = []
        self.base_color = tk.StringVar(value="#D9D9D9FF")
        self.output_directory = tk.StringVar(value=str(DEFAULT_OUTPUT_DIRECTORY))
        self.status = tk.StringVar(
            value="Enter a name, dimensions, font, and save folder for the color 3MF."
        )
        self._build()
        self.name.trace_add("write", self._name_changed)
        self.text_style.trace_add("write", self._text_style_changed)
        self._name_changed()

    def _build(self) -> None:
        self.master.title("Name Tag Maker")
        self.master.resizable(False, False)
        self.grid(sticky="nsew")
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Name Tag Maker", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            self,
            text="Create a 3D-printable name tag as a color 3MF file.",
        ).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2, 18)
        )

        ttk.Label(self, text="Name").grid(row=2, column=0, sticky="w", pady=4)
        name_entry = ttk.Entry(self, textvariable=self.name, width=36)
        name_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)
        name_entry.focus()

        ttk.Label(self, text="Length (mm)").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self.length, width=12).grid(
            row=3, column=1, sticky="w", pady=4
        )

        ttk.Label(self, text="Width (mm)").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self.width, width=12).grid(
            row=4, column=1, sticky="w", pady=4
        )

        ttk.Label(self, text="Font size (mm)").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self.font_size, width=12).grid(
            row=5, column=1, sticky="w", pady=4
        )

        ttk.Label(self, text="Font name").grid(row=6, column=0, sticky="w", pady=4)
        installed_fonts = sorted(
            family for family in tkfont.families(self.master) if not family.startswith("@")
        )
        ttk.Combobox(
            self,
            textvariable=self.font_name,
            values=installed_fonts,
            state="normal",
            width=32,
        ).grid(row=6, column=1, columnspan=2, sticky="ew", pady=4)

        ttk.Label(self, text="Text style").grid(row=7, column=0, sticky="w", pady=4)
        ttk.Combobox(
            self,
            textvariable=self.text_style,
            values=tuple(TEXT_STYLES),
            state="readonly",
            width=24,
        ).grid(row=7, column=1, sticky="w", pady=4)

        ttk.Label(self, text="Letter colors").grid(
            row=8, column=0, sticky="nw", pady=(8, 4)
        )
        color_controls = ttk.Frame(self)
        color_controls.grid(row=8, column=1, columnspan=2, sticky="ew", pady=(8, 4))
        self.letter_color_canvas = tk.Canvas(
            color_controls, height=120, width=390, highlightthickness=1
        )
        self.letter_color_scrollbar = ttk.Scrollbar(
            color_controls, orient="vertical", command=self.letter_color_canvas.yview
        )
        self.letter_color_canvas.configure(
            yscrollcommand=self.letter_color_scrollbar.set
        )
        self.letter_color_canvas.pack(side="left", fill="x", expand=True)
        self.letter_color_scrollbar.pack(side="right", fill="y")
        self.letter_color_rows = ttk.Frame(self.letter_color_canvas)
        self._letter_color_window = self.letter_color_canvas.create_window(
            (0, 0), window=self.letter_color_rows, anchor="nw"
        )
        self.letter_color_rows.bind("<Configure>", self._update_color_scrollregion)
        self.letter_color_canvas.bind("<Configure>", self._resize_color_rows)

        ttk.Label(self, text="Base color").grid(row=9, column=0, sticky="w", pady=4)
        base_color = self.base_color.get()
        self.base_color_button = tk.Button(
            self,
            text=base_color[:7],
            width=14,
            background=base_color[:7],
            activebackground=base_color[:7],
            foreground=self._contrast_for_color(base_color),
            command=self.choose_base_color,
        )
        self.base_color_button.grid(row=9, column=1, sticky="w", pady=4)

        ttk.Label(self, text="Save location").grid(
            row=10, column=0, sticky="w", pady=(10, 4)
        )
        ttk.Entry(self, textvariable=self.output_directory, width=36).grid(
            row=10, column=1, sticky="ew", pady=(10, 4)
        )
        ttk.Button(self, text="Choose…", command=self.choose_output_directory).grid(
            row=10, column=2, sticky="e", padx=(8, 0), pady=(10, 4)
        )

        ttk.Separator(self).grid(row=11, column=0, columnspan=3, sticky="ew", pady=18)
        buttons = ttk.Frame(self)
        buttons.grid(row=12, column=0, columnspan=3, sticky="e")
        ttk.Button(buttons, text="Create color 3MF", command=self.create_tag).grid(
            row=0, column=0
        )
        ttk.Button(buttons, text="Close", command=self.master.destroy).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Label(self, textvariable=self.status, wraplength=440).grid(
            row=13, column=0, columnspan=3, sticky="w", pady=(16, 0)
        )

    def _name_changed(self, *_args) -> None:
        letters = [character for character in self.name.get().strip() if not character.isspace()]
        while len(self.letter_colors) < len(letters):
            self.letter_colors.append("#FFFFFFFF")
        del self.letter_colors[len(letters) :]
        self._refresh_letter_color_rows(letters)

    def _text_style_changed(self, *_args) -> None:
        letters = [
            character
            for character in self.name.get().strip()
            if not character.isspace()
        ]
        self._refresh_letter_color_rows(letters)

    def _refresh_letter_color_rows(self, letters: list[str]) -> None:
        for child in self.letter_color_rows.winfo_children():
            child.destroy()

        if not letters:
            ttk.Label(
                self.letter_color_rows,
                text="Type a name to choose a color for each letter.",
            ).grid(row=0, column=0, sticky="w", padx=6, pady=6)
            return

        engraved = TEXT_STYLES.get(self.text_style.get()) == "engraved"
        row_offset = 0
        if engraved:
            ttk.Label(
                self.letter_color_rows,
                text="Engraved colors fill the bottom of each pocket.",
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=4)
            row_offset = 1

        for index, character in enumerate(letters):
            color = self.letter_colors[index]
            foreground = self._contrast_for_color(color)
            ttk.Label(
                self.letter_color_rows,
                text=f"Letter {index + 1}: {character}",
                width=20,
            ).grid(row=index + row_offset, column=0, sticky="w", padx=6, pady=2)
            tk.Button(
                self.letter_color_rows,
                text=color[:7],
                width=12,
                background=color[:7],
                activebackground=color[:7],
                foreground=foreground,
                command=lambda letter_index=index: self.choose_letter_color(letter_index),
            ).grid(row=index + row_offset, column=1, sticky="w", padx=6, pady=2)

        self.letter_color_canvas.configure(scrollregion=self.letter_color_canvas.bbox("all"))

    @staticmethod
    def _contrast_for_color(color: str) -> str:
        red, green, blue = (int(color[offset : offset + 2], 16) for offset in (1, 3, 5))
        brightness = (red * 299 + green * 587 + blue * 114) / 1000
        return "#000000" if brightness > 140 else "#FFFFFF"

    def _update_color_scrollregion(self, _event=None) -> None:
        self.letter_color_canvas.configure(scrollregion=self.letter_color_canvas.bbox("all"))

    def _resize_color_rows(self, event) -> None:
        self.letter_color_canvas.itemconfigure(self._letter_color_window, width=event.width)

    def choose_letter_color(self, index: int) -> None:
        _rgb, selected_color = colorchooser.askcolor(
            color=self.letter_colors[index][:7],
            title=f"Choose color for letter {index + 1}",
            parent=self.master,
        )
        if selected_color:
            self.letter_colors[index] = f"{selected_color.upper()}FF"
            letters = [
                character
                for character in self.name.get().strip()
                if not character.isspace()
            ]
            self._refresh_letter_color_rows(letters)

    def choose_base_color(self) -> None:
        _rgb, selected_color = colorchooser.askcolor(
            color=self.base_color.get()[:7],
            title="Choose a color for the tag body",
            parent=self.master,
        )
        if selected_color:
            color = f"{selected_color.upper()}FF"
            self.base_color.set(color)
            self.base_color_button.configure(
                text=color[:7],
                background=color[:7],
                activebackground=color[:7],
                foreground=self._contrast_for_color(color),
            )

    def choose_output_directory(self) -> None:
        initial_directory = Path(self.output_directory.get()).expanduser()
        if not initial_directory.is_dir():
            initial_directory = PROJECT_DIRECTORY
        selected = filedialog.askdirectory(
            title="Choose where to save the name tag 3MF",
            initialdir=str(initial_directory),
        )
        if selected:
            self.output_directory.set(selected)

    def create_tag(self) -> None:
        try:
            length = float(self.length.get())
            width = float(self.width.get())
            font_size = float(self.font_size.get())
            path = create_name_tag_file(
                self.name.get(),
                length,
                width,
                font_size,
                self.font_name.get(),
                self.text_style.get(),
                self.letter_colors.copy(),
                self.base_color.get(),
                Path(self.output_directory.get()),
            )
        except ValueError as error:
            messagebox.showerror(
                "Check the name and dimensions",
                "Enter a name, positive numeric dimensions and font size, and a font name.\n\n"
                f"Details: {error}",
                parent=self.master,
            )
            return
        except OSError as error:
            messagebox.showerror("Could not create name tag", str(error), parent=self.master)
            return

        self.status.set(f"Created:\n{path}")
        if TEXT_STYLES.get(self.text_style.get()) == "engraved":
            parts_note = "The lettering is cut into the body, with colored parts at the pocket floors."
        else:
            parts_note = "The tag body and each letter are separate parts."
        messagebox.showinfo(
            "Color name tag created",
            "The color-aware 3MF was saved to:\n"
            f"{path}\n\n{parts_note} Open it in your slicer to review the result.",
            parent=self.master,
        )


def main() -> None:
    root = tk.Tk()
    ttk.Style(root).configure("Title.TLabel", font=("Helvetica", 18, "bold"))
    NameTagApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
