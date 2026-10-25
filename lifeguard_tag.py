"""Create the round YMCA Lifeguard tag as a CadQuery model.

The default is the proven Lucy-tag geometry: a 45 mm diameter, 2 mm thick
round PLA tag with a small external keyring tab. The tab holds a 5 mm hole with
a 2.5 mm radial wall. Lettering is always a first-layer inlay for a
smooth face-down finish.
Open this file in CQ-editor and run it to preview the two print bodies.

Examples:

    python lifeguard_tag.py --name Lucy --output output/lucy_lifeguard.stl
    python lifeguard_tag.py --name Emma --output output/emma.stl
    python lifeguard_tag.py --name Amy --center-mark ymca --format 3mf --output output/amy.3mf

For two-colour printing, use the automatically generated *_tag.stl and
*_letters.stl files as separate bodies in the slicer, or create one color-aware
3MF archive with --format 3mf.
"""

from __future__ import annotations

import argparse
import math
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import cadquery as cq
from cadquery import exporters


PROJECT_DIRECTORY = Path(__file__).resolve().parent
YMCA_LOGO_DXF = PROJECT_DIRECTORY / "assets" / "ymca_logo.dxf"


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
        text_raise=0.195,
        inlay_depth=0.195,
        style="inlaid",
        # With 5.5 mm lettering, these radii leave roughly 3–4 mm from the
        # outside of the glyphs to the 45 mm disk perimeter.
        lifeguard_arc_radius=16.5,
        lifeguard_arc_degrees=150.0,
        name_arc_radius=16.0,
        name_letter_spacing=0.8,
        name_max_arc_degrees=140.0,
        cross_size=20.0,
        cross_arm_width=8.0,
        center_mark="cross",
        ymca_logo_scale=1.2,
        ymca_logo_y_offset=4.0,
        ymca_name_text_size=6.0,
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
        self.name_letter_spacing = name_letter_spacing
        self.name_max_arc_degrees = name_max_arc_degrees
        self.cross_size = cross_size
        self.cross_arm_width = cross_arm_width
        self.center_mark = center_mark
        self.ymca_logo_scale = ymca_logo_scale
        self.ymca_logo_y_offset = ymca_logo_y_offset
        self.ymca_name_text_size = ymca_name_text_size

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("name must contain at least one non-space character")
        if self.diameter <= 0 or self.thickness <= 0:
            raise ValueError("diameter and thickness must be positive")
        if self.text_size <= 0 or self.text_raise <= 0 or self.inlay_depth <= 0:
            raise ValueError("text dimensions must be positive")
        if self.style != "inlaid":
            raise ValueError("Lifeguard tags use first-layer inlaid lettering")
        if self.center_mark not in {"cross", "ymca"}:
            raise ValueError("center_mark must be 'cross' or 'ymca'")
        if self.name_letter_spacing < 0:
            raise ValueError("name_letter_spacing cannot be negative")
        if self.ymca_logo_scale <= 0:
            raise ValueError("ymca_logo_scale must be positive")
        if self.ymca_name_text_size <= 0:
            raise ValueError("ymca_name_text_size must be positive")
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
    tracking: float | None = None,
) -> cq.Workplane:
    """Create individually positioned glyphs with proportional arc spacing."""
    characters = list(text.strip())
    if not any(not character.isspace() for character in characters):
        raise ValueError("arc text must contain visible characters")

    # CadQuery has no text-on-path operation. Measure each bold glyph and use
    # its actual width as arc length, producing a close visual approximation of
    # proportional text rather than giving every character equal angular space.
    # Whitespace deliberately receives a width but no solid so full names keep
    # their word breaks.
    glyphs: list[cq.Workplane | None] = []
    widths: list[float] = []
    for character in characters:
        if character.isspace():
            glyphs.append(None)
            widths.append(size * 0.33)
            continue
        glyph = cq.Workplane("XY").text(
            character,
            size,
            height,
            font=font,
            kind="bold",
            halign="center",
            valign="center",
        )
        glyphs.append(glyph)
        widths.append(glyph.val().BoundingBox().xlen)

    direction = 1.0 if span_degrees >= 0 else -1.0
    tracked_pairs = sum(
        not characters[index].isspace() and not characters[index + 1].isspace()
        for index in range(len(characters) - 1)
    )
    if tracking is None:
        available_arc_length = radius * math.radians(abs(span_degrees))
        tracking = (
            0.0
            if not tracked_pairs
            else max(0.0, (available_arc_length - sum(widths)) / tracked_pairs)
        )
    angle = start_degrees + direction * math.degrees(widths[0] / (2 * radius))

    result: cq.Workplane | None = None
    for index, glyph in enumerate(glyphs):
        if glyph is not None:
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
        if index < len(characters) - 1:
            pair_tracking = (
                tracking
                if not characters[index].isspace() and not characters[index + 1].isspace()
                else 0.0
            )
            center_distance = widths[index] / 2 + pair_tracking + widths[index + 1] / 2
            angle += direction * math.degrees(center_distance / radius)

    assert result is not None
    return result


def _bottom_name(params: LifeguardTagParameters) -> cq.Workplane:
    """Place the lower name with natural glyph spacing, centered at 6 o'clock."""
    characters = list(params.name.strip())
    if not any(not character.isspace() for character in characters):
        raise ValueError("name must contain visible characters")

    # Short names previously filled a fixed 27-degree-per-letter span.  That
    # made a three-letter name look artificially spaced apart.  Measure the
    # actual bold glyphs, use a modest 0.8 mm default gap, and only tighten
    # tracking when a genuinely long name needs the 140-degree limit.
    text_size = (
        params.ymca_name_text_size if params.center_mark == "ymca" else params.text_size
    )
    widths = []
    for character in characters:
        if character.isspace():
            widths.append(text_size * 0.33)
            continue
        width = (
            cq.Workplane("XY")
            .text(
                character,
                text_size,
                params.inlay_depth,
                font=params.name_font,
                kind="bold",
                halign="center",
                valign="center",
            )
            .val()
            .BoundingBox()
            .xlen
        )
        widths.append(width)
    tracked_pairs = sum(
        not characters[index].isspace() and not characters[index + 1].isspace()
        for index in range(len(characters) - 1)
    )
    natural_length = sum(widths) + params.name_letter_spacing * tracked_pairs
    natural_span = math.degrees(natural_length / params.name_arc_radius)
    span = min(natural_span, params.name_max_arc_degrees)
    # Keep ordinary names at the preferred 0.8 mm tracking.  A long full
    # name, however, must let _arc_text reduce that tracking to fit the capped
    # span; otherwise its final characters drift beyond the intended center.
    tracking = (
        params.name_letter_spacing
        if natural_span <= params.name_max_arc_degrees
        else None
    )
    return _arc_text(
        params.name.strip(),
        params.name_arc_radius,
        span,
        params.name_font,
        text_size,
        params.inlay_depth,
        270.0 - span / 2,
        -270.0,
        tracking=tracking,
    )


def _cross(size: float, arm_width: float, height: float) -> cq.Workplane:
    """Return a centered, conventional plus-sign solid."""
    vertical = cq.Workplane("XY").rect(arm_width, size).extrude(height)
    horizontal = cq.Workplane("XY").rect(size, arm_width).extrude(height)
    return vertical.union(horizontal)


def _ymca_logo(height: float, scale: float, y_offset: float) -> cq.Workplane:
    """Return Don's Fusion-drawn YMCA logo, centered on the tag.

    The source sketch is preserved as a DXF rather than traced from an image.
    The sketch includes its own corner radii and fits inside the intended
    20 mm center square.
    """
    if not YMCA_LOGO_DXF.exists():
        raise FileNotFoundError(f"YMCA logo source is missing: {YMCA_LOGO_DXF}")

    source = cq.importers.importDXF(str(YMCA_LOGO_DXF))
    # Calculate the center from the complete source outline.  Scale its 2D
    # wires before extrusion so the enlarged logo remains at the selected
    # inlay depth instead of becoming a raised feature.
    unscaled_logo = source.wires().toPending().extrude(height)
    bounds = unscaled_logo.val().BoundingBox()
    center_offset = (
        -(bounds.xmin + bounds.xmax) / 2,
        -(bounds.ymin + bounds.ymax) / 2,
        0,
    )
    scaled_wires = [
        wire.translate(center_offset).scale(scale) for wire in source.wires().vals()
    ]
    return (
        cq.Workplane("XY")
        .newObject(scaled_wires)
        .toPending()
        .extrude(height)
        .translate((0, y_offset, 0))
    )


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

    # The YMCA layout uses Don's centered logo and deliberately leaves the
    # upper arc blank.  The original cross layout keeps LIFEGUARD at the top.
    lifeguard = None
    if params.center_mark == "cross":
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
    name = _bottom_name(params)
    center_mark = (
        _cross(
            params.cross_size,
            params.cross_arm_width,
            params.inlay_depth,
        )
        if params.center_mark == "cross"
        else _ymca_logo(
            params.inlay_depth,
            params.ymca_logo_scale,
            params.ymca_logo_y_offset,
        )
    )
    lettering = name.union(center_mark)
    if lifeguard is not None:
        lettering = lifeguard.union(lettering)

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


def _three_mf_mesh(shape: cq.Shape) -> str:
    """Return the Core 3MF mesh XML for one CadQuery solid."""
    vertices, triangles = shape.tessellate(0.1)
    # CadQuery tessellates individual BREP faces independently.  Adjacent faces
    # can therefore have duplicate vertices at the same coordinates but with
    # different indexes. STL tolerates that; a 3MF mesh does not, and Bambu
    # reports those seams as thousands of open edges.  Reuse vertices by the
    # exact precision written to the XML before emitting the triangles.
    vertex_indexes: dict[tuple[float, float, float], int] = {}
    unique_vertices: list[tuple[float, float, float]] = []
    index_map: list[int] = []
    for vertex in vertices:
        coordinates = (round(vertex.x, 6), round(vertex.y, 6), round(vertex.z, 6))
        if coordinates not in vertex_indexes:
            vertex_indexes[coordinates] = len(unique_vertices)
            unique_vertices.append(coordinates)
        index_map.append(vertex_indexes[coordinates])

    vertex_xml = "".join(
        f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>'
        for x, y, z in unique_vertices
    )
    triangle_xml = "".join(
        f'<triangle v1="{index_map[triangle[0]]}" v2="{index_map[triangle[1]]}" v3="{index_map[triangle[2]]}"/>'
        for triangle in triangles
    )
    return f"<mesh><vertices>{vertex_xml}</vertices><triangles>{triangle_xml}</triangles></mesh>"


def export_two_color_3mf(
    model: LifeguardTagModel,
    destination: Path,
    *,
    tag_name: str = "Tag body",
    tag_color: str = "#00A651FF",
    inlay_name: str = "Lettering and center mark",
    inlay_color: str = "#FFFFFFFF",
) -> Path:
    """Write one standard 3MF archive with separately colored tag and inlay parts.

    The archive has one build item containing two component objects.  This lets
    slicers import it as one aligned, multi-part object while retaining the
    display colors as Base Material properties.
    """
    destination = destination.with_suffix(".3mf")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tag_mesh = _three_mf_mesh(model.tag.val())
    inlay_mesh = _three_mf_mesh(model.letters.val())
    model_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <metadata name="Title">Lifeguard Tag</metadata>
  <resources>
    <basematerials id="1">
      <base name="{escape(tag_name)}" displaycolor="{escape(tag_color)}"/>
      <base name="{escape(inlay_name)}" displaycolor="{escape(inlay_color)}"/>
    </basematerials>
    <object id="2" type="model" name="{escape(tag_name)}" pid="1" pindex="0">{tag_mesh}</object>
    <object id="3" type="model" name="{escape(inlay_name)}" pid="1" pindex="1">{inlay_mesh}</object>
    <object id="4" type="model" name="Lifeguard Tag"><components><component objectid="2"/><component objectid="3"/></components></object>
  </resources>
  <build><item objectid="4"/></build>
</model>
'''
    content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
'''
    relationships = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
'''
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("3D/3dmodel.model", model_xml)
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a YMCA Lifeguard tag.")
    parser.add_argument("--name", default="Lucy", help="Name below the cross")
    parser.add_argument(
        "--center-mark",
        choices=("cross", "ymca"),
        default="cross",
        help="Use the original cross or the YMCA-logo layout",
    )
    parser.add_argument("--without-hole", action="store_true", help="Omit the keyring hole")
    parser.add_argument("--output", type=Path, default=Path("lifeguard_tag.stl"))
    parser.add_argument(
        "--format",
        choices=("stl", "3mf"),
        default="stl",
        help="Write separate STL parts or one two-color 3MF archive",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = build_lifeguard_tag(
        LifeguardTagParameters(
            name=args.name,
            include_keyring_hole=not args.without_hole,
            center_mark=args.center_mark,
        )
    )
    if args.format == "3mf":
        if args.center_mark == "ymca":
            tag_name, tag_color = "YMCA green tag", "#00A651FF"
        else:
            tag_name, tag_color = "Lifeguard red tag", "#E60012FF"
        path = export_two_color_3mf(
            model,
            args.output,
            tag_name=tag_name,
            tag_color=tag_color,
            inlay_name="White lettering and center mark",
        )
        print(f"Wrote {path.resolve()}")
    else:
        tag_path, letters_path = export_bodies(model, args.output)
        print(f"Wrote {tag_path.resolve()} and {letters_path.resolve()}")


# CQ-editor supplies show_object when it runs this file; OCP CAD Viewer exposes
# the optional _ocp_show_object import above. Showing the bodies separately
# makes the two-colour intent obvious in either preview.
_preview_show_object = globals().get("show_object", _ocp_show_object)
# Do not open a preview merely because another program imports this model.
# CQ-editor has its own execution namespace, while OCP previews occur when the
# file itself is run from VS Code.
if _preview_show_object is not None and (
    ("show_object" in globals() or __name__ == "__main__") and "--output" not in sys.argv
):
    preview_mark = "ymca" if "--center-mark" in sys.argv and "ymca" in sys.argv else "cross"
    preview = build_lifeguard_tag(
        LifeguardTagParameters(name="Lucy", center_mark=preview_mark)
    )
    _preview_show_object(
        preview.tag,
        name="Lifeguard tag",
        options={"color": (0.90, 0.05, 0.05)},
    )
    _preview_show_object(
        preview.letters,
        name="YMCA logo and name" if preview_mark == "ymca" else "Lifeguard lettering",
        options={"color": (0.0, 0.65, 0.25) if preview_mark == "ymca" else (1.0, 1.0, 1.0)},
    )


# In VS Code, the OCP import above means an ordinary Run is a clean preview.
# Supplying --output retains the command-line STL export workflow.
if __name__ == "__main__" and (_ocp_show_object is None or "--output" in sys.argv):
    main()
