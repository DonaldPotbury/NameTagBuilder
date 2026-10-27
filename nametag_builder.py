"""Generate a parameter-driven, 3D-printable name tag with CadQuery.

Run this module with the CadQuery-enabled environment:

    python nametag_builder.py --name "Alex" --output alex_name_tag.stl
"""

from __future__ import annotations

import argparse
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

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

    base = _build_name_tag_base(params)

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

    return base.union(lettering)


def _build_name_tag_base(params: NameTagParameters) -> cq.Workplane:
    """Build the tag body and keyring hole without lettering."""
    base = (
        cq.Workplane("XY")
        .rect(params.width, params.height)
        .extrude(params.thickness)
        .edges("|Z")
        .fillet(params.corner_radius)
    )

    hole_x = params.width / 2 - params.hole_margin
    keyring_hole = (
        cq.Workplane("XY")
        .center(hole_x, 0)
        .circle(params.hole_diameter / 2)
        .extrude(params.thickness + params.text_raise + 1)
    )

    return base.cut(keyring_hole)


def build_name_tag_parts(
    params: NameTagParameters,
    *,
    text_style: str = "raised",
) -> tuple[cq.Workplane, list[tuple[str, cq.Workplane]]]:
    """Return the tag body and, when applicable, one solid per visible character.

    Characters are laid out from their individual font outlines. Whitespace is
    retained as spacing but does not create a model part. ``raised`` letters sit
    above the face, ``inlaid`` letters sit in shallow pockets, and ``engraved``
    pockets are cut into the body and filled with colored letter parts at their floors.
    """
    params.validate()
    if text_style not in {"raised", "inlaid", "engraved"}:
        raise ValueError("text_style must be 'raised', 'inlaid', or 'engraved'")

    base = _build_name_tag_base(params)
    glyphs: list[tuple[str, float, float]] = []
    space_width = params.text_height * 0.33
    letter_gap = params.text_height * 0.08
    for character in params.name.strip():
        if character.isspace():
            glyphs.append((character, space_width, 0.0))
            continue

        glyph = cq.Workplane("XY").text(
            character,
            params.text_height,
            1.0,
            font=params.font,
            halign="center",
            valign="center",
        )
        bounds = glyph.val().BoundingBox()
        glyph_width = bounds.xlen
        glyph_center_x = (bounds.xmin + bounds.xmax) / 2
        if glyph_width <= 0:
            glyph_width = space_width
        glyphs.append((character, glyph_width, glyph_center_x))

    total_width = sum(item[1] for item in glyphs) + letter_gap * max(0, len(glyphs) - 1)
    cursor_x = -total_width / 2
    letter_parts: list[tuple[str, cq.Workplane]] = []
    for index, (character, glyph_width, glyph_center_x) in enumerate(glyphs):
        center_x = cursor_x + glyph_width / 2
        x_offset = center_x - glyph_center_x
        if not character.isspace():
            if text_style == "raised":
                glyph = cq.Workplane("XY").text(
                    character,
                    params.text_height,
                    params.text_raise + 0.05,
                    font=params.font,
                    halign="center",
                    valign="center",
                )
                letter_parts.append(
                    (
                        character,
                        glyph.translate(
                            (x_offset, 0, params.thickness - 0.05)
                        ),
                    )
                )
            elif text_style == "inlaid":
                pocket = cq.Workplane("XY").text(
                    character,
                    params.text_height,
                    params.text_raise + 0.05,
                    font=params.font,
                    halign="center",
                    valign="center",
                ).translate(
                    (x_offset, 0, params.thickness - params.text_raise)
                )
                base = base.cut(pocket)

                top_recess = min(0.05, params.text_raise * 0.1)
                inset_letter = cq.Workplane("XY").text(
                    character,
                    params.text_height,
                    params.text_raise - top_recess,
                    font=params.font,
                    halign="center",
                    valign="center",
                ).translate(
                    (x_offset, 0, params.thickness - params.text_raise)
                )
                letter_parts.append((character, inset_letter))
            else:
                engraving = cq.Workplane("XY").text(
                    character,
                    params.text_height,
                    params.text_raise + 0.05,
                    font=params.font,
                    halign="center",
                    valign="center",
                ).translate(
                    (x_offset, 0, params.thickness - params.text_raise)
                )
                base = base.cut(engraving)
                color_layer_height = min(0.25, params.text_raise * 0.5)
                engraved_color = cq.Workplane("XY").text(
                    character,
                    params.text_height,
                    color_layer_height,
                    font=params.font,
                    halign="center",
                    valign="center",
                ).translate(
                    (x_offset, 0, params.thickness - params.text_raise)
                )
                letter_parts.append((character, engraved_color))
        cursor_x += glyph_width
        if index < len(glyphs) - 1:
            cursor_x += letter_gap

    return base, letter_parts


def _three_mf_mesh(shape: cq.Shape) -> str:
    """Return 3MF mesh XML with vertices deduplicated at exported precision."""
    vertices, triangles = shape.tessellate(0.1)
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


def export_name_tag_3mf(
    base: cq.Workplane,
    letter_parts: list[tuple[str, cq.Workplane]],
    letter_colors: list[str],
    destination: Path,
    *,
    base_color: str = "#D9D9D9FF",
) -> Path:
    """Export an aligned multi-part 3MF with a separate material per letter."""
    if len(letter_parts) != len(letter_colors):
        raise ValueError("Provide one color for every visible letter.")

    destination = destination.with_suffix(".3mf")
    destination.parent.mkdir(parents=True, exist_ok=True)

    material_xml = "".join(
        f'<base name="{escape(name)}" displaycolor="{escape(color)}"/>'
        for name, color in [("Tag body", base_color)]
        + [
            (f"Letter {index}: {character}", color)
            for index, ((character, _), color) in enumerate(
                zip(letter_parts, letter_colors), start=1
            )
        ]
    )

    object_xml: list[str] = [
        f'<object id="2" type="model" name="Tag body" pid="1" pindex="0">{_three_mf_mesh(base.val())}</object>'
    ]
    component_refs = ['<component objectid="2"/>']
    for index, (character, part) in enumerate(letter_parts, start=1):
        object_id = index + 2
        object_name = f"Letter {index}: {character}"
        object_xml.append(
            f'<object id="{object_id}" type="model" name="{escape(object_name)}" pid="1" pindex="{index}">{_three_mf_mesh(part.val())}</object>'
        )
        component_refs.append(f'<component objectid="{object_id}"/>')

    assembly_id = len(letter_parts) + 3
    model_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <metadata name="Title">Name Tag</metadata>
  <resources>
    <basematerials id="1">{material_xml}</basematerials>
    {"".join(object_xml)}
    <object id="{assembly_id}" type="model" name="Name Tag"><components>{"".join(component_refs)}</components></object>
  </resources>
  <build><item objectid="{assembly_id}"/></build>
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
