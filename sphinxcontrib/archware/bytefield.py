"""
bytefield.py
=============
``.. bytefield::`` directive, docutils node, LaTeX template, and writer visitors.

The directive body contains only the *rows* of the diagram.  The
``\\begin{bytefield}`` / ``\\end{bytefield}`` wrapper is inserted automatically
using the values of ``:bitwidth:`` and ``:options:``.

The full standalone LaTeX document is built here and handed to
:func:`_pipeline.compile_to_svg` for compilation — this module has no
knowledge of how compilation works.
"""

from __future__ import annotations

import html as _html_mod
import textwrap
from typing import Any

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util import logging

from .pipeline import clean_svg, compile_to_svg, error_block, get_cache_dir

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LaTeX document template
# ---------------------------------------------------------------------------

# Every literal LaTeX brace that is not a Python format placeholder must be
# doubled so that str.format() does not mistake it for a substitution field.
#
# Always-included packages
# ------------------------
# rotating  – \turnbox used by \bitlabel / \rotbitheader
# xcolor    – \color, \textcolor, \colorbox used by \colorbitbox
# graphicx  – \includegraphics, \rotatebox (common in hardware docs)
# array     – extended column types for tabular inside bit boxes
# multirow  – \multirow for spanning rows in tables inside boxes
#
# Always-included custom commands
# --------------------------------
# \colorbitbox[sides]{color}{width}{content}
#     A \bitbox with a solid background colour.  The optional first argument
#     controls which borders are drawn (default: all four).
#
# \bitlabel{width}{label}
#     A borderless bitbox whose content is rotated 45° upward, suitable for
#     use in a header row above narrow single-bit fields.
#
# \rotbitheader{label}
#     Shorthand for \bitlabel{1}{label} — one rotated label per bit.
#
# \memsection{name}{size}{startaddr}{endaddr}
#     Renders one row of a memory-map diagram.  Designed for 32-bit-wide
#     bytefield environments (6-bit address column + 26-bit name column).
#     The row height is controlled by \memsectionheight (default 5\baselineskip).
#
# \descbox{width}{content}
#     A \bitbox whose content is wrapped in a centred \parbox, useful for
#     longer descriptions that must line-wrap inside a field cell.

_LATEX_TEMPLATE = textwrap.dedent(
    r"""
    \documentclass[varwidth, crop=true, border={border}]{{standalone}}
    \usepackage[T1]{{fontenc}}
    \usepackage{{lmodern}}
    \usepackage{{rotating}}
    \usepackage{{xcolor}}
    \usepackage{{graphicx}}
    \usepackage{{array}}
    \usepackage{{multirow}}
    \usepackage[{pkg_options}]{{bytefield}}
    {extra_packages}
    %% -----------------------------------------------------------------------
    %% \colorbitbox[sides]{{color}}{{width}}{{content}}
    \newcommand{{\colorbitbox}}[4][lrtb]{{%
      \rlap{{\bitbox[]{{#3}}{{\textcolor{{#2}}{{\rule{{\width}}{{\height}}}}}}}}%
      \bitbox[#1]{{#3}}{{#4}}%
    }}
    %% \bitlabel{{width}}{{label}}  –  borderless box with 45-degree rotated label
    \newcommand{{\bitlabel}}[2]{{%
      \bitbox[]{{#1}}{{%
        \raisebox{{0pt}}[4ex][0pt]{{%
          \turnbox{{45}}{{\fontsize{{7}}{{7}}\selectfont #2}}%
        }}%
      }}%
    }}
    %% \rotbitheader{{label}}  –  single-bit rotated header label
    \newcommand{{\rotbitheader}}[1]{{\bitlabel{{1}}{{#1}}}}
    %% \memsection{{name}}{{size}}{{startaddr}}{{endaddr}}
    \newlength{{\memsectionheight}}
    \setlength{{\memsectionheight}}{{5\baselineskip}}
    \newcommand{{\memsection}}[4]{{%
      \bytefieldsetup{{bitheight=\memsectionheight}}%
      \bitbox[]{{6}}{{\tt\scriptsize\begin{{tabular}}{{@{{}}r@{{}}}}#3\\#4\end{{tabular}}}}%
      \bitbox{{26}}{{#1\\{{\small(#2)}}}}%
    }}
    %% \descbox{{width}}{{content}}  –  centred word-wrapped description cell
    \newcommand{{\descbox}}[2]{{%
      \bitbox{{#1}}{{\parbox{{\width}}{{\centering\small #2}}}}%
    }}
    %% -----------------------------------------------------------------------
    \begin{{document}}
    {body}
    \end{{document}}
"""
).lstrip()


def _build_source(
    latex_body: str,
    pkg_options: str,
    extra_packages: str,
    border: str,
) -> str:
    """Return a complete standalone LaTeX document for one bytefield diagram."""
    pkg_lines = ""
    for pkg in extra_packages.split(","):
        pkg = pkg.strip()
        if pkg:
            pkg_lines += f"\\usepackage{{{pkg}}}\n"

    return _LATEX_TEMPLATE.format(
        border=border,
        pkg_options=pkg_options,
        extra_packages=pkg_lines,
        body=latex_body,
    )


# ---------------------------------------------------------------------------
# Docutils node
# ---------------------------------------------------------------------------


class bytefield_node(nodes.General, nodes.Element):
    """
    Carries a bytefield diagram through the Sphinx doctree.

    Attributes stored on the node
    ------------------------------
    latex       Complete ``\\begin{bytefield}…\\end{bytefield}`` source.
    pkg_options Options passed to ``\\usepackage[…]{bytefield}``.
    packages    Comma-separated extra ``\\usepackage`` entries.
    align       HTML figure alignment: ``left``, ``center``, or ``right``.
    caption     Optional HTML ``<figcaption>`` text.
    border      TeX length used as the ``standalone`` border before crop.
    scale       Float SVG scale multiplier (1.0 = 100 %).
    """


# ---------------------------------------------------------------------------
# Directive
# ---------------------------------------------------------------------------


class BytefieldDirective(Directive):
    """
    Render a ``bytefield`` diagram as inline SVG (HTML) or raw LaTeX.

    The directive body contains only the row commands
    (``\\bitheader``, ``\\bitbox``, ``\\wordbox``, etc.).
    The ``\\begin{bytefield}[options]{bitwidth}`` wrapper is added
    automatically from ``:bitwidth:`` and ``:options:``.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "bitwidth": directives.positive_int,
        "options": directives.unchanged,
        "packages": directives.unchanged,
        "align": lambda x: directives.choice(x, ("left", "center", "right")),
        "caption": directives.unchanged,
        "scale": directives.percentage,
        "border": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        if "bitwidth" not in self.options:
            return [
                self.state_machine.reporter.error(
                    "bytefield directive requires the :bitwidth: option",
                    line=self.lineno,
                )
            ]

        latex_body = "\n".join(self.content)
        if not latex_body.strip():
            return [
                self.state_machine.reporter.warning(
                    "bytefield directive is empty",
                    line=self.lineno,
                )
            ]

        bitwidth = self.options["bitwidth"]
        bf_options = self.options.get("options", "")
        opt_str = f"[{bf_options}]" if bf_options else ""
        latex_body = (
            f"\\begin{{bytefield}}{opt_str}{{{bitwidth}}}\n"
            f"{latex_body}\n"
            f"\\end{{bytefield}}"
        )

        scale_raw = self.options.get("scale", None)

        node = bytefield_node()
        node["latex"] = latex_body
        node["pkg_options"] = self.options.get("options", "")
        node["packages"] = self.options.get("packages", "")
        node["align"] = self.options.get("align", "center")
        node["caption"] = self.options.get("caption", "")
        node["border"] = self.options.get("border", "6pt")
        node["scale"] = float(scale_raw) / 100.0 if scale_raw else 1.0
        return [node]


# ---------------------------------------------------------------------------
# HTML visitors
# ---------------------------------------------------------------------------


def visit_bytefield_html(self: Any, node: bytefield_node) -> None:
    """Compile the diagram and splice the resulting SVG into the HTML body."""
    full_source = _build_source(
        latex_body=node["latex"],
        pkg_options=node["pkg_options"],
        extra_packages=node["packages"],
        border=node["border"],
    )
    try:
        svg_raw = compile_to_svg(full_source, get_cache_dir(self.builder))
    except RuntimeError as exc:
        self.body.append(error_block(node["latex"], str(exc)))
        raise nodes.SkipNode from exc

    align = node["align"]
    caption = node["caption"]
    svg = clean_svg(svg_raw, scale=node["scale"])

    self.body.append(
        f'<figure class="bytefield-diagram"'
        f' style="text-align:{align};display:block;margin:1em auto">\n'
    )
    self.body.append(svg)
    if caption:
        self.body.append(
            f'\n<figcaption style="font-size:.875em;color:#555;margin-top:.4em">'
            f"{_html_mod.escape(caption)}</figcaption>"
        )
    self.body.append("\n</figure>\n")
    raise nodes.SkipNode


def depart_bytefield_html(self: Any, node: bytefield_node) -> None:
    pass  # never reached — visit raises SkipNode


# ---------------------------------------------------------------------------
# LaTeX visitors
# ---------------------------------------------------------------------------


def visit_bytefield_latex(self: Any, node: bytefield_node) -> None:
    """Emit the raw bytefield source directly into the LaTeX document."""
    self.body.append("\n")
    self.body.append(node["latex"])
    self.body.append("\n")
    raise nodes.SkipNode


def depart_bytefield_latex(self: Any, node: bytefield_node) -> None:
    pass


# ---------------------------------------------------------------------------
# Unsupported-format visitors
# ---------------------------------------------------------------------------


def visit_bytefield_unsupported(self: Any, node: bytefield_node) -> None:
    logger.warning(
        "bytefield: output format not supported — diagram skipped.",
        location=node,
    )
    raise nodes.SkipNode


def depart_bytefield_unsupported(self: Any, node: bytefield_node) -> None:
    pass
