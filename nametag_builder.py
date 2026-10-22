"""Generate a parameter-driven, 3D-printable name tag with CadQuery.

Run this module with the CadQuery-enabled environment:

    python nametag_builder.py --name "Alex" --output alex_name_tag.stl
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
from cadquery import exporters


@dataclass(frozen=True)
class NameTagParameters:
    """All dimensions are millimetres."""

    name: str = "Your Name"
    width: float = 75.0
    height: float = 28.0
    thickness: float = 3.0
    corner_radius: float = 3.0
    text_height: float = 14.0
    text_raise: float = 0.8
    font: str = "Arial"
    hole_diameter: float = 4.5
    hole_margin: float = 7.0

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("name must contain at least one non-space character")
        if self.width <= 0 or self.height <= 0 or self.thickness <= 0:
            raise ValueError("width, height, and thickness must be positive")
        if not 0 < self.corner_radius <= min(self.width, self.height) / 2:
            raise ValueError("corner_radius must fit within the tag")
        if self.text_height <= 0 or self.text_raise <= 0:
            raise ValueError("text_height and text_raise must be positive")
        if self.hole_diameter <= 0 or self.hole_margin <= self.hole_diameter / 2:
            raise ValueError("hole_margin must exceed the hole radius")
        if self.hole_margin + self.hole_diameter / 2 > self.width / 2:
            raise ValueError("hole does not fit within the tag width")


def build_name_tag(params: NameTagParameters) -> cq.Workplane:
    """Return a solid name tag with raised lettering and a keyring hole."""
    params.validate()

    base = (
        cq.Workplane("XY")
        .rect(params.width, params.height)
        .extrude(params.thickness)
        .edges("|Z")
        .fillet(params.corner_radius)
    )

    # Start the lettering just inside the base so it fuses reliably when printed.
    lettering = (
        cq.Workplane("XY")
        .text(
            params.name.strip(),
            params.text_height,
            params.text_raise + 0.05,
            font=params.font,
            halign="center",
            valign="center",
        )
        .translate((0, 0, params.thickness - 0.05))
    )

    hole_x = params.width / 2 - params.hole_margin
    keyring_hole = (
        cq.Workplane("XY")
        .center(hole_x, 0)
        .circle(params.hole_diameter / 2)
        .extrude(params.thickness + params.text_raise + 1)
    )

    return base.union(lettering).cut(keyring_hole)


def export_stl(model: cq.Workplane, destination: Path) -> None:
    """Export *model* to an STL file, creating the output directory if needed."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(model, str(destination), exportType="STL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a 3D-printable name tag STL.")
    parser.add_argument("--name", default="Your Name", help="Text shown on the tag")
    parser.add_argument("--output", type=Path, default=Path("name_tag.stl"))
    parser.add_argument("--width", type=float, default=75.0)
    parser.add_argument("--height", type=float, default=28.0)
    parser.add_argument("--thickness", type=float, default=3.0)
    parser.add_argument("--text-height", type=float, default=14.0)
    parser.add_argument("--font", default="Arial")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    params = NameTagParameters(
        name=args.name,
        width=args.width,
        height=args.height,
        thickness=args.thickness,
        text_height=args.text_height,
        font=args.font,
    )
    model = build_name_tag(params)
    export_stl(model, args.output)
    print(f"Wrote {args.output.resolve()}")


# CQ-editor supplies show_object when it executes this file.  Keeping this outside
# main lets an editor preview work without generating an STL or parsing its args.
if "show_object" in globals():
    show_object(build_name_tag(NameTagParameters()), name="Name tag")


if __name__ == "__main__":
    main()
