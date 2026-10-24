"""Create the round YMCA Lifeguard tag as a CadQuery model.

The default is the proven Lucy-tag geometry: a 45 mm diameter, 2 mm thick
round PLA tag with a small external keyring tab. The tab holds a 5 mm hole with
a 2.5 mm radial wall. Lettering is always a first-layer inlay for a
smooth face-down finish.
Open this file in CQ-editor and run it to preview the two print bodies.

Examples:

    python lifeguard_tag.py --name Lucy --output output/lucy_lifeguard.stl
    python lifeguard_tag.py --name Emma --output output/emma.stl

For two-colour printing, use the automatically generated *_tag.stl and
*_letters.stl files as separate bodies in the slicer.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import cadquery as cq
from cadquery import exporters


# OCP CAD Viewer is optional. CQ-editor does not need this import because it
# supplies show_object itself when executing the script.
try:
    from ocp_vscode import show_object as _ocp_show_object
except ImportError:
    _ocp_show_object = None


class LifeguardTagParameters:
    """Dimensions in millimetres; defaults reproduce Don's Lucy tag."""

    # A conventional class is deliberate: CQ-editor runs files in a temporary
    # namespace, where Python 3.12's @dataclass annotation lookup can fail.
    def __init__(
        self,
        name="Lucy",
        diameter=45.0,
        thickness=2.0,
        edge_wall=0.8,
        include_keyring_hole=True,
        hole_diameter=5.0,
        hole_wall=2.5,
        tab_blend_radius=2.0,
        lifeguard_font="Arial Narrow",
        name_font="Arial",
        text_size=5.5,
        text_raise=0.55,
        inlay_depth=0.55,
        style="inlaid",
        # With 5.5 mm lettering, these radii leave roughly 3–4 mm from the
        # outside of the glyphs to the 45 mm disk perimeter.
        lifeguard_arc_radius=16.5,
        lifeguard_arc_degrees=150.0,
        name_arc_radius=16.0,
        name_character_spacing_degrees=27.0,
        name_max_arc_degrees=140.0,
        cross_size=20.0,
        cross_arm_width=8.0,
    ):
        self.name = name
        self.diameter = diameter
        self.thickness = thickness
        self.edge_wall = edge_wall
        self.include_keyring_hole = include_keyring_hole
        self.hole_diameter = hole_diameter
        self.hole_wall = hole_wall
        self.tab_blend_radius = tab_blend_radius
        self.lifeguard_font = lifeguard_font
        self.name_font = name_font
        self.text_size = text_size
        self.text_raise = text_raise
        self.inlay_depth = inlay_depth
        self.style = style
        self.lifeguard_arc_radius = lifeguard_arc_radius
        self.lifeguard_arc_degrees = lifeguard_arc_degrees
        self.name_arc_radius = name_arc_radius
        self.name_character_spacing_degrees = name_character_spacing_degrees
        self.name_max_arc_degrees = name_max_arc_degrees
        self.cross_size = cross_size
        self.cross_arm_width = cross_arm_width

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("name must contain at least one non-space character")
        if self.diameter <= 0 or self.thickness <= 0:
            raise ValueError("diameter and thickness must be positive")
        if self.text_size <= 0 or self.text_raise <= 0 or self.inlay_depth <= 0:
            raise ValueError("text dimensions must be positive")
        if self.style != "inlaid":
            raise ValueError("Lifeguard tags use first-layer inlaid lettering")
        if self.include_keyring_hole:
            if self.hole_diameter <= 0 or self.hole_wall < 0:
                raise ValueError("hole dimensions are invalid")
            if self.hole_diameter + 2 * self.hole_wall > self.diameter:
                raise ValueError("keyring hole and its surrounding wall do not fit")
            if self.tab_blend_radius <= 0:
                raise ValueError("tab_blend_radius must be positive")


class LifeguardTagModel:
    """Separate solids for the tag and contrasting lettering/icon."""

    def __init__(self, tag: cq.Workplane, letters: cq.Workplane):
        self.tag = tag
        self.letters = letters

    def combined(self) -> cq.Workplane:
        return self.tag.union(self.letters)


def _arc_text(
    text: str,
    radius: float,
    span_degrees: float,
    font: str,
    size: float,
    height: float,
    start_degrees: float,
    rotation_offset: float,
) -> cq.Workplane:
    """Create individually positioned glyphs with proportional arc spacing."""
    characters = [character for character in text if not character.isspace()]
    if not characters:
        raise ValueError("arc text must contain visible characters")

    # CadQuery has no text-on-path operation. Measure each bold glyph and use
    # its actual width as arc length, producing a close visual approximation of
    # proportional text rather than giving every character equal angular space.
    glyphs = [
        cq.Workplane("XY").text(
            character,
            size,
            height,
            font=font,
            kind="bold",
            halign="center",
            valign="center",
        )
        for character in characters
    ]
    widths = [glyph.val().BoundingBox().xlen for glyph in glyphs]
    direction = 1.0 if span_degrees >= 0 else -1.0
    available_arc_length = radius * math.radians(abs(span_degrees))
    tracking = (
        0.0
        if len(glyphs) == 1
        else max(0.0, (available_arc_length - sum(widths)) / (len(glyphs) - 1))
    )
    angle = start_degrees + direction * math.degrees(widths[0] / (2 * radius))

    result: cq.Workplane | None = None
    for index, glyph in enumerate(glyphs):
        glyph = (
            glyph.rotate((0, 0, 0), (0, 0, 1), angle + rotation_offset)
            .translate(
                (
                    radius * math.cos(math.radians(angle)),
                    radius * math.sin(math.radians(angle)),
                    0,
                )
            )
        )
        result = glyph if result is None else result.union(glyph)
        if index < len(glyphs) - 1:
            center_distance = widths[index] / 2 + tracking + widths[index + 1] / 2
            angle += direction * math.degrees(center_distance / radius)

    assert result is not None
    return result


def _cross(size: float, arm_width: float, height: float) -> cq.Workplane:
    """Return a centered, conventional plus-sign solid."""
    vertical = cq.Workplane("XY").rect(arm_width, size).extrude(height)
    horizontal = cq.Workplane("XY").rect(size, arm_width).extrude(height)
    return vertical.union(horizontal)


def build_lifeguard_tag(params: LifeguardTagParameters) -> LifeguardTagModel:
    """Build the tag body and its separate lettering/cross body."""
    params.validate()

    tag = cq.Workplane("XY").circle(params.diameter / 2).extrude(params.thickness)
    if params.include_keyring_hole:
        # In the Fusion design, the hole's centre is exactly on the perimeter
        # of the 45 mm disk. The outer tab is blended back into the disk with a
        # 2 mm radius, keeping a broad, durable connection. The hole has a
        # 2.5 mm radial wall, matching the Fusion sketch.
        hole_y = params.diameter / 2
        tab_radius = params.hole_diameter / 2 + params.hole_wall
        tab = (
            cq.Workplane("XY")
            .center(0, hole_y)
            .circle(tab_radius)
            .extrude(params.thickness)
        )
        hole = (
            cq.Workplane("XY")
            .center(0, hole_y)
            .circle(params.hole_diameter / 2)
            .extrude(params.thickness + params.text_raise + 1)
        )
        tag = tag.union(tab).edges("|Z").fillet(params.tab_blend_radius).cut(hole)

    # The 0.8 mm fillet from the Fusion design softens both faces of the outer
    # perimeter and the keyring hole. It is applied before the lettering is
    # cut so the first-layer inlay remains sharply defined.
    tag = tag.edges("not |Z").fillet(params.edge_wall)

    lifeguard = _arc_text(
        "LIFEGUARD",
        params.lifeguard_arc_radius,
        # Travel from upper-left to upper-right, beneath the keyring hole.
        -params.lifeguard_arc_degrees,
        params.lifeguard_font,
        params.text_size,
        params.inlay_depth,
        165.0,
        -90.0,
    )
    # Keep every name centered at the bottom.  Four letters such as Lucy need
    # roughly 80 degrees, not the full arc used by the nine-letter heading.
    name_span = min(
        params.name_character_spacing_degrees * (len(params.name.strip()) - 1),
        params.name_max_arc_degrees,
    )
    name_start = 270.0 - name_span / 2
    name = _arc_text(
        params.name.strip(),
        params.name_arc_radius,
        name_span,
        params.name_font,
        params.text_size,
        params.inlay_depth,
        name_start,
        -270.0,
    )
    lettering = lifeguard.union(name).union(
        _cross(
            params.cross_size,
            params.cross_arm_width,
            params.inlay_depth,
        )
    )

    # Recess the matching tool body into the face. Flip the result in the
    # slicer to print the inlaid face against the build plate.
    lettering = lettering.translate((0, 0, params.thickness - params.inlay_depth))
    tag = tag.cut(lettering)

    return LifeguardTagModel(tag=tag, letters=lettering)


def export_bodies(model: LifeguardTagModel, destination: Path) -> tuple[Path, Path]:
    """Write separate STL files, ready for a two-colour slicer workflow."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    tag_path = destination.with_name(f"{destination.stem}_tag.stl")
    letters_path = destination.with_name(f"{destination.stem}_letters.stl")
    exporters.export(model.tag, str(tag_path), exportType="STL")
    exporters.export(model.letters, str(letters_path), exportType="STL")
    return tag_path, letters_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a YMCA Lifeguard tag.")
    parser.add_argument("--name", default="Lucy", help="Name below the cross")
    parser.add_argument("--without-hole", action="store_true", help="Omit the keyring hole")
    parser.add_argument("--output", type=Path, default=Path("lifeguard_tag.stl"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = build_lifeguard_tag(
        LifeguardTagParameters(
            name=args.name,
            include_keyring_hole=not args.without_hole,
        )
    )
    tag_path, letters_path = export_bodies(model, args.output)
    print(f"Wrote {tag_path.resolve()} and {letters_path.resolve()}")


# CQ-editor supplies show_object when it runs this file; OCP CAD Viewer exposes
# the optional _ocp_show_object import above. Showing the bodies separately
# makes the two-colour intent obvious in either preview.
_preview_show_object = globals().get("show_object", _ocp_show_object)
if _preview_show_object is not None:
    preview = build_lifeguard_tag(LifeguardTagParameters(name="Benjamin"))
    _preview_show_object(
        preview.tag,
        name="Lifeguard tag",
        options={"color": (0.90, 0.05, 0.05)},
    )
    _preview_show_object(
        preview.letters,
        name="Lifeguard lettering",
        options={"color": (1.0, 1.0, 1.0)},
    )


# In VS Code, the OCP import above means an ordinary Run is a clean preview.
# Supplying --output retains the command-line STL export workflow.
if __name__ == "__main__" and (_ocp_show_object is None or "--output" in sys.argv):
    main()
