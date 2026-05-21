"""
register.py
============
Directives, nodes, and writer visitors for the LaTeX ``register`` package.

Three directives are provided:

``.. register::``
    Renders a register diagram as inline SVG (HTML) or a ``register`` float
    (LaTeX).  The body contains only row commands (``\\regfield``,
    ``\\reglabel``, ``\\regnewline``, etc.).  The
    ``\\begin{register*}…\\end{register*}`` wrapper is added automatically for
    SVG compilation; the numbered ``\\begin{register}…\\end{register}`` float
    is emitted for LaTeX output so that register numbering and
    ``\\listofregisters`` work correctly.

``.. regdesc::``
    Documents the fields of the preceding register.  The body is written in
    plain RST definition-list syntax (field name as term, description as
    indented body).  For HTML output the content is rendered as a styled
    ``<dl>`` element.  For LaTeX output it is wrapped in the ``register``
    package's ``regdesc`` / ``reglist`` environments, with inline formatting
    (bold, italic, inline code) preserved.

``.. listofregisters::``
    Placeholder replaced at ``doctree-resolved`` time with a list of links to
    every ``.. register::`` in the document (HTML) or with
    ``\\listofregisters`` (LaTeX).
"""

from __future__ import annotations

import html as _html_mod
import re
import textwrap
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from .pipeline import (
    _LATEX_TEMPLATE_FOR_SVG_EXPORT,
    clean_svg,
    compile_to_svg,
    error_block,
    get_cache_dir,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LaTeX document template for SVG compilation
# ---------------------------------------------------------------------------

# Used only when producing SVG for HTML output.  For LaTeX output the raw
# \begin{register}…\end{register} is emitted directly by the LaTeX visitor.
#
# The register package declares Regfloat via the float package.  In a
# standalone document the float machinery (\lastbox, \unkern, \unpenalty)
# fails with "You can't use \lastbox in vertical mode" because there is no
# surrounding column/page context for the float to be placed into.
#
# The fix is to redefine Regfloat as a plain center environment immediately
# after the register package is loaded, replacing the float entirely.  The
# starred register* environment is then used so no caption or list-of-registers
# entry is attempted.


def _build_register_source(
    latex_body: str,
    pkg_options: str,
    extra_packages: str,
    border: str,
) -> str:
    """Return a complete standalone LaTeX document for one register diagram."""
    pkg_lines = ""
    for pkg in extra_packages.split(","):
        pkg = pkg.strip()
        if pkg:
            pkg_lines += f"\\usepackage{{{pkg}}}\n"

    return _LATEX_TEMPLATE_FOR_SVG_EXPORT.format(
        border=border,
        bytefield_pkg_options="",
        register_pkg_options=pkg_options,
        extra_packages=pkg_lines,
        body=latex_body,
    )


# ---------------------------------------------------------------------------
# LaTeX text helpers  (used by regdesc LaTeX visitor)
# ---------------------------------------------------------------------------

_LATEX_SPECIAL = str.maketrans(
    {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "]": "{]}",  # protect ] inside \item[…] optional argument
    }
)


def _latex_escape(text: str) -> str:
    return text.translate(_LATEX_SPECIAL)


def _node_to_latex(node: nodes.Node) -> str:
    """
    Recursively convert a docutils node to a LaTeX string.

    Handles the most common inline elements (Text, emphasis, strong, literal /
    inline code, reference).  Unknown node types fall back to plain escaped
    text via ``.astext()``.
    """
    if isinstance(node, nodes.Text):
        return _latex_escape(str(node))
    if isinstance(node, nodes.literal):
        return f"\\texttt{{{_latex_escape(node.astext())}}}"
    if isinstance(node, nodes.emphasis):
        return f"\\emph{{{_nodes_to_latex(node.children)}}}"
    if isinstance(node, nodes.strong):
        return f"\\textbf{{{_nodes_to_latex(node.children)}}}"
    if isinstance(node, nodes.reference):
        url = node.get("refuri", "")
        text = _nodes_to_latex(node.children)
        if url:
            return f"\\href{{{_latex_escape(url)}}}{{{text}}}"
        return text
    if isinstance(node, nodes.paragraph):
        return _nodes_to_latex(node.children)
    # Generic fallback: process children if any, otherwise escape plain text
    if node.children:
        return _nodes_to_latex(node.children)
    return _latex_escape(node.astext())


def _nodes_to_latex(node_list) -> str:
    return "".join(_node_to_latex(n) for n in node_list)


# ---------------------------------------------------------------------------
# Node ID helpers
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"[^\w\s-]")
_WS_RE = re.compile(r"[\s_]+")


def _make_node_id(name: str, index: int) -> str:
    """Return a stable, URL-safe HTML id for a register node."""
    slug = _SLUG_RE.sub("", name.lower())
    slug = _WS_RE.sub("-", slug).strip("-")
    return f"register-{index}-{slug}" if slug else f"register-{index}"


# ===========================================================================
# register  (diagram)
# ===========================================================================


class register_node(nodes.General, nodes.Element):
    """
    Carries a register diagram through the Sphinx doctree.

    Attributes stored on the node
    ------------------------------
    latex           Row commands (\\regfield, \\reglabel, \\regnewline, …).
    name            Register name (shown in caption / list of registers).
    address         Memory address / offset, e.g. ``0x250``.  May be empty.
    bitwidth        Maximum bits per row (``\\regBitWidth``).
    pkg_options     Options forwarded to ``\\usepackage[…]{register}``.
    packages        Comma-separated extra ``\\usepackage`` entries.
    align           HTML figure alignment: ``left``, ``center``, ``right``.
    caption         Override for the HTML ``<figcaption>`` text.
    border          TeX length for the ``standalone`` border before crop.
    scale           Float SVG scale multiplier (1.0 = 100 %).
    node_id         HTML element ``id``; assigned by ``doctree-resolved``.
    """


class RegisterDirective(SphinxDirective):
    """
    Render a ``register`` diagram as inline SVG (HTML) or a register float
    (LaTeX).

    The directive body contains only the row commands — do not include the
    ``\\begin{register}`` / ``\\end{register}`` wrapper.

    Required option
    ---------------
    :name:  Register name shown in the caption and the list of registers.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "name": directives.unchanged,
        "address": directives.unchanged,
        "bitwidth": directives.positive_int,
        "color": directives.flag,
        "options": directives.unchanged,
        "packages": directives.unchanged,
        "align": lambda x: directives.choice(x, ("left", "center", "right")),
        "caption": directives.unchanged,
        "scale": directives.percentage,
        "border": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        if "name" not in self.options:
            return [
                self.state_machine.reporter.error(
                    "register directive requires the :name: option",
                    line=self.lineno,
                )
            ]

        latex_body = "\n".join(self.content)
        if not latex_body.strip():
            return [
                self.state_machine.reporter.warning(
                    "register directive is empty",
                    line=self.lineno,
                )
            ]

        # Build the pkg_options string: user-supplied options, plus "color"
        # if the :color: flag is present.
        user_opts = self.options.get("options", "")
        color_opt = "color" if "color" in self.options else ""
        pkg_options = ", ".join(filter(None, [color_opt, user_opts]))
        if not pkg_options:
            pkg_options = getattr(self.env.config, "register_package_options", "")

        scale_raw = self.options.get("scale", None)

        latex_body = (
            f"\\renewcommand{{\\regBitWidth}}{{{self.options.get("bitwidth", 32)}}}"
            f"\\begin{{register*}}{{H}}{{{self.options.get("name", "")}}}{{{self.options.get("address", "")}}}\n"
            f"{latex_body}\n"
            f"\\end{{register*}}\n"
        )

        node = register_node()
        node["latex"] = latex_body
        node["name"] = self.options.get("name", "")
        node["address"] = self.options.get("address", "")
        node["bitwidth"] = self.options.get("bitwidth", 32)
        node["pkg_options"] = pkg_options
        node["packages"] = self.options.get("packages", "")
        node["align"] = self.options.get("align", "center")
        node["caption"] = self.options.get("caption", "")
        node["border"] = self.options.get("border", "6pt")
        node["scale"] = float(scale_raw) / 100.0 if scale_raw else 1.0
        node["node_id"] = ""  # filled in by on_doctree_resolved
        return [node]


# ── HTML visitors ─────────────────────────────────────────────────────────────


def visit_register_html(self: Any, node: register_node) -> None:
    """Compile the register diagram and splice the SVG into the HTML body."""
    full_source = _build_register_source(
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
    caption = node["caption"] or node["name"]
    if node["address"]:
        caption = f"{caption} ({node['address']})"
    node_id = node["node_id"]
    svg = clean_svg(svg_raw, scale=node["scale"])

    id_attr = f' id="{_html_mod.escape(node_id)}"' if node_id else ""
    self.body.append(
        f'<figure class="register-diagram"{id_attr}'
        f' style="text-align:{align};display:block;margin:1em auto">\n'
    )
    self.body.append(svg)
    self.body.append(
        f'\n<figcaption style="font-size:.875em;color:#555;margin-top:.4em">'
        f"{_html_mod.escape(caption)}</figcaption>"
    )
    self.body.append("\n</figure>\n")
    raise nodes.SkipNode


def depart_register_html(self: Any, node: register_node) -> None:
    pass  # never reached — visit raises SkipNode


# ── LaTeX visitors ────────────────────────────────────────────────────────────


def visit_register_latex(self: Any, node: register_node) -> None:
    """
    Emit a numbered ``register`` float into the LaTeX document.

    The unstarred environment is used so that the diagram is counted, captioned,
    and listed by ``\\listofregisters``.
    """
    latex_body = node["latex"].replace(node["name"], _latex_escape(node["name"]))
    latex_body = latex_body.replace(node["address"], _latex_escape(node["address"]))
    latex_body = latex_body.replace("register*", "register")
    self.body.append(latex_body)
    raise nodes.SkipNode


def depart_register_latex(self: Any, node: register_node) -> None:
    pass  # never reached — visit raises SkipNode


# ── Unsupported-format visitors ───────────────────────────────────────────────


def visit_register_unsupported(self: Any, node: register_node) -> None:
    logger.warning(
        "register: output format not supported — diagram skipped.",
        location=node,
    )
    raise nodes.SkipNode


def depart_register_unsupported(self: Any, node: register_node) -> None:
    pass  # never reached — visit raises SkipNode


# ===========================================================================
# regdesc  (field descriptions)
# ===========================================================================


class regdesc_node(nodes.General, nodes.Element):
    """
    Container for register field descriptions.

    Wraps a standard docutils ``definition_list`` produced by parsing the
    directive body as RST.  Writer visitors add package-specific wrappers
    around the standard list rendering.
    """


class RegdescDirective(SphinxDirective):
    """
    Document register fields using a plain RST definition list.

    Each entry in the body is a field name followed by an indented
    description::

        .. regdesc::

           FieldName
              Description of the field.  Inline markup is supported:
              ``code``, *emphasis*, **bold**.

           AnotherField
              Another description.

    For HTML output the list is rendered as a ``<dl class="regdesc">``
    element.  For LaTeX output it is wrapped in the ``register`` package's
    ``regdesc`` / ``reglist`` environments.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {}

    def run(self) -> list[nodes.Node]:
        node = regdesc_node()
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


# ── HTML visitors ─────────────────────────────────────────────────────────────


def visit_regdesc_html(self: Any, node: regdesc_node) -> None:
    """Open a <div class="regdesc"> wrapper; children are rendered normally."""
    self.body.append('<div class="regdesc">\n')


def depart_regdesc_html(self: Any, node: regdesc_node) -> None:
    self.body.append("</div>\n")


# ── LaTeX visitors ────────────────────────────────────────────────────────────


def visit_regdesc_latex(self: Any, node: regdesc_node) -> None:
    """
    Reconstruct the field list as a ``regdesc`` / ``reglist`` LaTeX environment.

    The standard Sphinx LaTeX writer would render the inner ``definition_list``
    as a ``\\begin{description}`` list, which does not use the ``register``
    package's styling.  This visitor intercepts the node, reconstructs the list
    manually, and raises ``SkipNode`` so the children are not processed again.

    Inline formatting (bold, italic, inline code, hyperlinks) is preserved via
    ``_node_to_latex()``.
    """
    # Collect all definition_list_items from child definition_list nodes
    items: list[tuple[str, str]] = []  # (term_latex, definition_latex)
    for child in node.children:
        if not isinstance(child, nodes.definition_list):
            continue
        for item in child.children:
            if not isinstance(item, nodes.definition_list_item):
                continue
            term_latex = ""
            defn_latex = ""
            for part in item.children:
                if isinstance(part, nodes.term):
                    # Use .astext() on the term directly and then escape.
                    # Walking part.children with _nodes_to_latex is unsafe
                    # because RST backslash escapes (e.g. ``\_``) cause
                    # docutils to emit intermediate nodes whose .astext()
                    # returns U+FFFD, corrupting the output.  Field names in
                    # regdesc are always plain text and never need inline markup.
                    term_latex = _latex_escape(part.astext())
                elif isinstance(part, nodes.definition):
                    para_parts = []
                    for para in part.children:
                        if isinstance(para, nodes.paragraph):
                            para_parts.append(_nodes_to_latex(para.children))
                        else:
                            para_parts.append(_node_to_latex(para))
                    defn_latex = "\n\n".join(para_parts)
            if term_latex:
                items.append((term_latex, defn_latex))

    if not items:
        raise nodes.SkipNode

    # Use the longest term as the reglist width-calibration argument
    longest = max(items, key=lambda t: len(t[0]))[0]

    self.body.append(f"\\begin{{regdesc}}\n\\begin{{reglist}}[{longest}]\n")
    for term, defn in items:
        self.body.append(f"\\item[{term}] {defn}\n")
    self.body.append("\\end{reglist}\n\\end{regdesc}\n")
    raise nodes.SkipNode


def depart_regdesc_latex(self: Any, node: regdesc_node) -> None:
    pass  # never reached — visit raises SkipNode


# ── Unsupported-format visitors ───────────────────────────────────────────────


def visit_regdesc_unsupported(self: Any, node: regdesc_node) -> None:
    logger.warning(
        "regdesc: output format not supported — field descriptions skipped.",
        location=node,
    )
    raise nodes.SkipNode


def depart_regdesc_unsupported(self: Any, node: regdesc_node) -> None:
    pass  # never reached — visit raises SkipNode


# ===========================================================================
# listofregisters  (ToC placeholder)
# ===========================================================================


class listofregisters_node(nodes.General, nodes.Element):
    """
    Placeholder replaced at ``doctree-resolved`` time.

    For HTML output it becomes a ``<ul>`` of internal links to every
    ``.. register::`` directive in the document.  For LaTeX output it becomes
    ``\\listofregisters``.
    """


class ListofregistersDirective(SphinxDirective):
    """
    Insert a list of all ``.. register::`` diagrams in the document.

    ::

        .. listofregisters::
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    option_spec = {}

    def run(self) -> list[nodes.Node]:
        return [listofregisters_node()]


# ── Dummy visitors (node is replaced before writers run) ─────────────────────


def visit_listofregisters_html(self: Any, node: listofregisters_node) -> None:
    logger.warning("listofregisters: node was not replaced before HTML write.")
    raise nodes.SkipNode


def depart_listofregisters_html(self: Any, node: listofregisters_node) -> None:
    pass  # never reached — visit raises SkipNode


def visit_listofregisters_latex(self: Any, node: listofregisters_node) -> None:
    logger.warning("listofregisters: node was not replaced before LaTeX write.")
    raise nodes.SkipNode


def depart_listofregisters_latex(self: Any, node: listofregisters_node) -> None:
    pass  # never reached — visit raises SkipNode


def visit_listofregisters_unsupported(self: Any, node: listofregisters_node) -> None:
    raise nodes.SkipNode


def depart_listofregisters_unsupported(self: Any, node: listofregisters_node) -> None:
    pass  # never reached — visit raises SkipNode


# ===========================================================================
# doctree-resolved event handler
# ===========================================================================


def on_doctree_resolved(app: Any, doctree: Any, docname: str) -> None:
    """
    Assign stable HTML IDs to every ``register_node`` and replace every
    ``listofregisters_node`` with a concrete list.

    This event fires once per document, after the doctree is fully resolved
    but before any writer processes it.
    """
    # ── Pass 1: assign node_id to every register_node ────────────────────────
    register_nodes = list(doctree.traverse(register_node))
    for idx, rnode in enumerate(register_nodes, start=1):
        rnode["node_id"] = _make_node_id(rnode["name"], idx)

    # ── Pass 2: replace listofregisters_node placeholders ────────────────────
    for lor_node in doctree.traverse(listofregisters_node):
        replacement = _build_listofregisters(register_nodes, app.builder)
        lor_node.replace_self(replacement)


def _build_listofregisters(
    reg_nodes: list[register_node],
    builder: Any,
) -> list[nodes.Node]:
    """
    Build the concrete replacement for a ``listofregisters_node``.

    For LaTeX output: a single ``nodes.raw`` containing ``\\listofregisters``.
    For all other outputs: a ``bullet_list`` of internal reference nodes.
    """
    builder_format = getattr(builder, "format", "html")

    if builder_format == "latex":
        return [nodes.raw("", "\\listofregisters\n", format="latex")]

    if not reg_nodes:
        return []

    bullet_list = nodes.bullet_list(classes=["listofregisters"])
    for rnode in reg_nodes:
        name = rnode["name"]
        address = rnode["address"]
        node_id = rnode["node_id"]

        display = f"{name} ({address})" if address else name

        ref = nodes.reference(internal=True, refid=node_id)
        ref += nodes.Text(display)
        para = nodes.paragraph()
        para += ref
        item = nodes.list_item()
        item += para
        bullet_list += item

    return [bullet_list]
