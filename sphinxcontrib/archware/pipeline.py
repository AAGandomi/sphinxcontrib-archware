"""
pipeline.py
============
Shared LaTeX-to-SVG compilation pipeline.

This module is responsible solely for turning a complete LaTeX source string
into an SVG string.  It knows nothing about bytefield, register, or any other
LaTeX package — those concerns live in their own modules.

Public API
----------
get_cache_dir(builder)                  → str
    Derive the shared cache directory from the Sphinx builder's output path.

compile_to_svg(full_source, cache_dir)  → str
    Compile a complete LaTeX source string to SVG, with caching.

clean_svg(svg, scale)                   → str
    Strip XML declaration / DOCTYPE and optionally scale width/height.

error_block(source, message)            → str
    Return an HTML error box for use when compilation fails.

Cache layout
------------
Every diagram is keyed by a SHA-256 hash of its full LaTeX source.  All
artefacts share the same stem inside the cache directory::

    _build/
      archware/cache/
        diagram-<hash>.tex
        diagram-<hash>.dvi   (or .pdf)
        diagram-<hash>.log
        diagram-<hash>.latex.log
        diagram-<hash>.pdflatex.log
        diagram-<hash>.aux
        diagram-<hash>.svg   ← sentinel: if this exists, the pipeline is skipped

Compilation priority
--------------------
1.  ``latex``    → DVI → ``dvisvgm``          (recommended — best text quality)
2.  ``pdflatex`` → PDF → ``inkscape``         (fallback)
3.  ``pdflatex`` → PDF → ``dvisvgm --pdf``    (fallback)
4.  ``pdflatex`` → PDF → ``pdf2svg``          (last resort)
"""

from __future__ import annotations

import hashlib
import html as _html_mod
import os
import re
import shutil
import subprocess
from pathlib import Path
import textwrap
from typing import Any

from sphinx.util import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Latex template for SVG output
# ---------------------------------------------------------------------------

_LATEX_TEMPLATE_FOR_SVG_EXPORT = textwrap.dedent(
    r"""
    \documentclass[varwidth, crop=true, border={border}]{{standalone}}
    \usepackage[T1]{{fontenc}}
    \usepackage{{lmodern}}
    \usepackage{{rotating}}
    \usepackage{{xcolor}}
    \usepackage{{graphicx}}
    \usepackage{{array}}
    \usepackage{{multirow}}
    \usepackage[{bytefield_pkg_options}]{{bytefield}}
    \usepackage[{register_pkg_options}]{{register}}
    \usepackage{{amsmath}}
    \usepackage{{pict2e}}
    \usepackage{{eulervm}}
    {extra_packages}
    %% -----------------------------------------------------------------------
    %% \colorbitbox[sides]{{color}}{{width}}{{content}}
    \newcommand{{\colorbitbox}}[4][lrtb]{{%
      \rlap{{\bitbox[]{{#3}}{{\textcolor{{#2}}{{\rule{{\width}}{{\height}}}}}}}}%
      \bitbox[#1]{{#3}}{{#4}}%
    }}
    %% \bitlabel{{width}}{{label}}  -  borderless box with 45-degree rotated label
    \newcommand{{\bitlabel}}[2]{{%
      \bitbox[]{{#1}}{{%
        \raisebox{{0pt}}[4ex][0pt]{{%
          \turnbox{{45}}{{\fontsize{{7}}{{7}}\selectfont #2}}%
        }}%
      }}%
    }}
    %% \rotbitheader{{label}}  -  single-bit rotated header label
    \newcommand{{\rotbitheader}}[1]{{\bitlabel{{1}}{{#1}}}}
    %% \memsection{{name}}{{size}}{{startaddr}}{{endaddr}}
    \newlength{{\memsectionheight}}
    \setlength{{\memsectionheight}}{{5\baselineskip}}
    \newcommand{{\memsection}}[4]{{%
      \bytefieldsetup{{bitheight=\memsectionheight}}%
      \bitbox[]{{6}}{{\tt\scriptsize\begin{{tabular}}{{@{{}}r@{{}}}}\texttt{{#3}}\\\texttt{{#4}}\end{{tabular}}}}%
      \bitbox{{26}}{{#1\\{{\small(#2)}}}}%
    }}
    %% \descbox{{width}}{{content}}  -  centred word-wrapped description cell
    \newcommand{{\descbox}}[2]{{%
      \bitbox{{#1}}{{\parbox{{\width}}{{\centering\small #2}}}}%
    }}
    %% -----------------------------------------------------------------------
    %% Make Regfloat a no-op so the float package's internal machinery
    %% (\lastbox, \unkern, \unpenalty, group nesting) is never invoked.
    %% The [1][] spec consumes the optional placement argument [H] that
    %% register* passes.  register* already provides \centering itself.
    \renewenvironment{{Regfloat}}[1][]{{}}{{}}
    %% ----------------------------------------------------------------------
    \begin{{document}}
    {body}
    \end{{document}}
"""
).lstrip()

# ---------------------------------------------------------------------------
# Cache configuration
# ---------------------------------------------------------------------------

_CACHE_SUBDIR = "archware/cache"
_STEM_PREFIX = "diagram"


# ---------------------------------------------------------------------------
# Public helper: locate the cache directory
# ---------------------------------------------------------------------------


def get_cache_dir(builder: Any) -> str:
    """
    Return the path to the shared cache directory.

    The cache lives one level above the builder's ``outdir`` so that it is
    shared between HTML, LaTeX, and other builder runs.  Falls back to
    ``/tmp/archware/cache`` when no builder is available.
    """
    outdir = getattr(builder, "outdir", None)
    build_root = os.path.dirname(outdir) if outdir else "/tmp"
    return os.path.join(build_root, _CACHE_SUBDIR)


# ---------------------------------------------------------------------------
# Internal subprocess helper
# ---------------------------------------------------------------------------


def _run(cmd: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


# ---------------------------------------------------------------------------
# SVG converter helpers  (DVI path)
# ---------------------------------------------------------------------------


def _try_dvisvgm_dvi(dvi_path: str, svg_path: str, cwd: str) -> bool:
    """DVI → SVG via dvisvgm (no --pdf flag). Returns True on success."""
    if not shutil.which("dvisvgm"):
        return False
    r = _run(
        [
            "dvisvgm",
            "--no-fonts",  # embed all glyphs as SVG paths
            "--bbox=preview",  # tight crop using the preview bounding box
            f"--output={svg_path}",
            dvi_path,
        ],
        cwd,
    )
    if r.returncode == 0 and os.path.exists(svg_path):
        return True
    logger.debug("dvisvgm (dvi) failed: %s", r.stderr)
    return False


# ---------------------------------------------------------------------------
# SVG converter helpers  (PDF path)
# ---------------------------------------------------------------------------


def _try_inkscape(pdf_path: str, svg_path: str, cwd: str) -> bool:
    """PDF → SVG via Inkscape. Returns True on success."""
    if not shutil.which("inkscape"):
        return False
    r = _run(
        ["inkscape", "--pdf-poppler", f"--export-filename={svg_path}", pdf_path],
        cwd,
    )
    if r.returncode == 0 and os.path.exists(svg_path):
        return True
    logger.debug("inkscape failed: %s", r.stderr)
    return False


def _try_dvisvgm_pdf(pdf_path: str, svg_path: str, cwd: str) -> bool:
    """PDF → SVG via dvisvgm --pdf. Returns True on success."""
    if not shutil.which("dvisvgm"):
        return False
    r = _run(
        [
            "dvisvgm",
            "--pdf",
            "--no-fonts",
            "--bbox=preview",
            f"--output={svg_path}",
            pdf_path,
        ],
        cwd,
    )
    if r.returncode == 0 and os.path.exists(svg_path):
        return True
    logger.debug("dvisvgm --pdf failed: %s", r.stderr)
    return False


def _try_pdf2svg(pdf_path: str, svg_path: str, cwd: str) -> bool:
    """PDF → SVG via pdf2svg. Returns True on success."""
    if not shutil.which("pdf2svg"):
        return False
    r = _run(["pdf2svg", pdf_path, svg_path], cwd)
    if r.returncode == 0 and os.path.exists(svg_path):
        return True
    logger.debug("pdf2svg failed: %s", r.stderr)
    return False


# ---------------------------------------------------------------------------
# Public API: compile_to_svg
# ---------------------------------------------------------------------------


def compile_to_svg(full_source: str, cache_dir: str) -> str:
    """
    Compile a complete LaTeX source string to an SVG string.

    The caller must supply a *full* document (``\\documentclass`` through
    ``\\end{document}``).  This function handles compilation, conversion, and
    caching; it does not know which LaTeX packages are in use.

    Results are cached in *cache_dir* keyed by a SHA-256 hash of
    *full_source*.  If a ``.svg`` file for that hash already exists, the
    entire pipeline is skipped and the cached SVG is returned immediately.

    All intermediate files (.tex, .dvi / .pdf, .log, .aux) are preserved in
    the cache directory so they are available for debugging.

    Raises
    ------
    RuntimeError
        If neither ``latex`` nor ``pdflatex`` is found, if compilation fails
        after both are tried, or if no SVG converter succeeds.
    """
    content_hash = hashlib.sha256(full_source.encode()).hexdigest()[:16]
    stem = f"{_STEM_PREFIX}-{content_hash}"

    os.makedirs(cache_dir, exist_ok=True)

    svg_file = os.path.join(cache_dir, f"{stem}.svg")
    if os.path.exists(svg_file):
        return Path(svg_file).read_text(encoding="utf-8")

    tex_file = os.path.join(cache_dir, f"{stem}.tex")
    pdf_file = os.path.join(cache_dir, f"{stem}.pdf")
    dvi_file = os.path.join(cache_dir, f"{stem}.dvi")

    Path(tex_file).write_text(full_source, encoding="utf-8")

    # ── Step 1: compile TeX → DVI (preferred) or PDF ────────────────────────
    dvi_ok = False
    pdf_ok = False

    if shutil.which("latex"):
        r = _run(
            [
                "latex",
                "-interaction=nonstopmode",
                "-output-directory",
                cache_dir,
                tex_file,
            ],
            cache_dir,
        )
        # Always write the captured output to a dedicated log file so it is
        # preserved even when latex crashes before writing its own .log file,
        # or when pdflatex subsequently overwrites the same-named .log.
        Path(os.path.join(cache_dir, f"{stem}.latex.log")).write_text(
            r.stdout, encoding="utf-8", errors="replace"
        )
        if r.returncode == 0 and os.path.exists(dvi_file):
            dvi_ok = True
        else:
            excerpt = "\n".join(r.stdout.strip().splitlines()[-20:])
            logger.warning("latex failed:\n%s", excerpt)

    if not dvi_ok and shutil.which("pdflatex"):
        r = _run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory",
                cache_dir,
                tex_file,
            ],
            cache_dir,
        )
        Path(os.path.join(cache_dir, f"{stem}.pdflatex.log")).write_text(
            r.stdout, encoding="utf-8", errors="replace"
        )
        if r.returncode == 0 and os.path.exists(pdf_file):
            pdf_ok = True
        else:
            excerpt = "\n".join(r.stdout.strip().splitlines()[-20:])
            raise RuntimeError(f"pdflatex compilation failed:\n{excerpt}")

    if not dvi_ok and not pdf_ok:
        raise RuntimeError("Neither latex nor pdflatex found on PATH.")

    # ── Step 2: convert to SVG ───────────────────────────────────────────────
    converted = False

    if dvi_ok:
        converted = _try_dvisvgm_dvi(dvi_file, svg_file, cache_dir)

    if not converted and pdf_ok:
        converted = (
            _try_inkscape(pdf_file, svg_file, cache_dir)
            or _try_dvisvgm_pdf(pdf_file, svg_file, cache_dir)
            or _try_pdf2svg(pdf_file, svg_file, cache_dir)
        )

    if not converted:
        raise RuntimeError(
            "SVG conversion failed.  "
            "Install dvisvgm (≥ 2.9, recommended), inkscape, or pdf2svg."
        )

    return Path(svg_file).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API: clean_svg
# ---------------------------------------------------------------------------

_XML_DECL_RE = re.compile(r"<\?xml[^?]*\?>", re.IGNORECASE)
_DOCTYPE_RE = re.compile(r"<!DOCTYPE[^>]*>", re.IGNORECASE)
_SVG_OPEN_RE = re.compile(
    r"(<svg\b[^>]*)"
    r"(width=['\"])([\d.]+)([a-z]*)['\"]"
    r"([^>]*)"
    r"(height=['\"])([\d.]+)([a-z]*)['\"]",
    re.IGNORECASE,
)


def clean_svg(svg: str, scale: float = 1.0) -> str:
    """
    Prepare an SVG string for inline HTML embedding.

    - Strips the XML declaration (``<?xml … ?>``) and DOCTYPE, both of which
      are invalid inside an HTML5 document.
    - When *scale* ≠ 1.0, multiplies the ``width`` and ``height`` attributes
      on the root ``<svg>`` element by the given factor.
    """
    svg = _XML_DECL_RE.sub("", svg).strip()
    svg = _DOCTYPE_RE.sub("", svg).strip()

    if scale != 1.0:

        def _scale_dim(m: re.Match) -> str:
            return (
                f"{m.group(1)}"
                f'{m.group(2)}{float(m.group(3)) * scale:.2f}{m.group(4)}"'
                f"{m.group(5)}"
                f'{m.group(6)}{float(m.group(7)) * scale:.2f}{m.group(8)}"'
            )

        svg = _SVG_OPEN_RE.sub(_scale_dim, svg, count=1)

    return svg


# ---------------------------------------------------------------------------
# Public API: error_block
# ---------------------------------------------------------------------------


def error_block(source: str, message: str) -> str:
    """Return an HTML error box shown in place of a failed diagram."""
    return (
        '<div class="latexsvg-error" style="'
        'border:1px solid #c00;background:#fff0f0;padding:1em;margin:1em 0">'
        f"<strong>LaTeX diagram error:</strong> {_html_mod.escape(message)}"
        f'<pre style="margin-top:.5em;overflow:auto">{_html_mod.escape(source)}</pre>'
        "</div>"
    )
