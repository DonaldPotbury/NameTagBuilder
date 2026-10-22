# NameTagBuilder

NameTagBuilder generates customizable, 3D-printable name tags with Python and
[CadQuery](https://cadquery.readthedocs.io/). It is deliberately parameter-driven:
the name, tag dimensions, lettering, keyring hole, and font live in one model
definition rather than needing CAD edits for each tag.

## Current model

`nametag_builder.py` produces a rounded rectangular name tag with raised text and
a keyring hole. All dimensions are millimetres. The default tag is 75 × 28 × 3 mm
with 0.8 mm raised lettering.

## Generate an STL

Activate the project Conda environment, then run:

```bash
python nametag_builder.py --name "Alex" --output output/alex_name_tag.stl
```

Useful optional parameters include `--width`, `--height`, `--thickness`,
`--text-height`, and `--font`:

```bash
python nametag_builder.py --name "Ken" --width 80 --text-height 16 --font "Arial" --output output/ken.stl
```

The script validates the key dimensions before creating the solid. Open the STL
in your slicer, check that the lettering is legible at the chosen size, and slice
using the material and printer settings appropriate for the job.

## Preview in CQ-editor

CQ-editor is a convenient way to iterate on the model before exporting an STL.
Open `nametag_builder.py` in CQ-editor and run it. The default name tag will
appear in the 3D viewer as **Name tag**. Change the values in
`NameTagParameters` in the preview call near the end of the file, run again,
and inspect the result.

For a reusable custom preview, replace the default preview call with your own
parameter values:

```python
show_object(
    build_name_tag(NameTagParameters(name="Ken", width=80, text_height=16)),
    name="Ken name tag",
)
```

Use the command-line form above when you are ready to export the final STL.

## Model parameters

Use `NameTagParameters` in `nametag_builder.py` when you want to control all
settings programmatically. It includes:

| Parameter | Meaning |
| --- | --- |
| `name` | Text on the tag |
| `width`, `height`, `thickness` | Base dimensions |
| `corner_radius` | Rounded base corners |
| `text_height`, `text_raise`, `font` | Lettering appearance |
| `hole_diameter`, `hole_margin` | Keyring-hole size and placement |

## Project direction

The next useful design decisions are the physical tag style (rectangle, badge,
or clip), text treatment (raised or engraved), and whether to support extras such
as a logo, two-line names, or a magnetic backing. The source is structured so
those options can become additional parameters without changing the workflow.

## Collaboration

Use a feature branch and a GitHub pull request for each change. This lets both
contributors test a proposed model before it reaches `main`. See
[the Git workflow](Docs/git-workflow.md) for the agreed process and test checklist.
For a GitHub Desktop-only walkthrough, see [Ken's workflow](Docs/github-desktop-workflow.md).
For copy-and-paste help when working with Codex, see
[Codex prompts for Ken](Docs/codex-prompts-for-ken.md).

This is a little test by Don.
