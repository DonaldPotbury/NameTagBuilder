# NameTagBuilder — Development Environment Setup

**Last updated:** October 10, 2026  
**Status:** Don's macOS environment verified; Ken's Windows 11 environment pending

## Purpose

This document records the development environment for NameTagBuilder, a collaborative project to create customizable, 3D-printable name tags using Python and CadQuery.

**Repository:** https://github.com/DonaldPotbury/NameTagBuilder

The goal is for Don and Ken to run the same modeling source code on their respective computers and export models suitable for 3D printing.

## Don's macOS environment — verified

| Component | Configuration |
| --- | --- |
| Hardware | MacBook, Apple M4, 16 GB memory |
| Operating system | macOS Tahoe 26.6.2 |
| Editor | Visual Studio Code |
| Environment manager | Conda |
| Environment name | `nametagbuilder` |
| Python | 3.12.15 |
| CadQuery | 2.8.0 |

The Conda environment has been activated successfully, and CadQuery's installed version was verified with:

```bash
conda activate nametagbuilder
python -c "import cadquery as cq; print('CadQuery:', cq.__version__)"
```

Expected version output:

```text
CadQuery: 2.8.0
```

A simple 60 × 20 × 5 mm block model and a corresponding `hello_cadquery.stl` file are present in Don's CadQuery experiments workspace. This is separate from the NameTagBuilder repository.

## Ken's Windows 11 environment — pending

Ken uses a Windows 11 laptop. His existing Python, Conda, and VS Code installations have not yet been confirmed. The proposed target is:

| Component | Proposed configuration |
| --- | --- |
| Editor | Visual Studio Code |
| Environment manager | Conda |
| Environment name | `nametagbuilder` |
| Python | 3.12.15, subject to package compatibility |
| CadQuery | 2.8.0, subject to package availability |

### Initial inventory (no installation yet)

Open **Windows PowerShell** and run these commands one at a time:

```powershell
python --version
conda --version
code --version
```

Record the output or any error messages. A command not being recognized does not necessarily mean the software is absent; it may not be on the current PATH.

**Do not install, uninstall, or change existing environments until the results have been reviewed together.**

### Guided installation plan

- [ ] Review Ken's initial inventory and any existing development projects.
- [ ] Select or configure a suitable Conda installation.
- [ ] Create an isolated environment named `nametagbuilder`.
- [ ] Install compatible Python and CadQuery versions, aiming to match Don's verified versions.
- [ ] Configure VS Code to use the new environment.
- [ ] Confirm the active Python and CadQuery versions.
- [ ] Run a simple CadQuery model and export an STL file.
- [ ] Inspect the STL in an appropriate viewer or slicer.
- [ ] Confirm access to the shared GitHub repository.
- [ ] Record the actual commands used and any Windows-specific issues below.

### Verification commands (after setup)

```powershell
conda activate nametagbuilder
python --version
python -c "import cadquery as cq; print('CadQuery:', cq.__version__)"
```

### Windows installation notes

_To be completed during Ken's guided installation._

## Shared development principles

- Keep NameTagBuilder dependencies isolated from unrelated Python projects.
- Use the GitHub repository as the authoritative source for code and technical documentation.
- Prefer the same Python and CadQuery versions on both machines where practical.
- Verify model generation and STL export on both operating systems before considering setup complete.
- Record confirmed installation steps rather than assumptions.

## Next session

Start by reviewing Ken's output from `python --version`, `conda --version`, and `code --version`. Choose installation steps based on those results, then update this document with the verified Windows procedure.
