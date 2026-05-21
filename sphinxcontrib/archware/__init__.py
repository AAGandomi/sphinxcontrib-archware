"""
sphinxcontrib-archware
======================

Sphinx extension that renders ``bytefield`` and ``register`` LaTeX diagrams
as inline SVG in HTML output.

Directives
----------
``.. bytefield::``
    Renders a ``bytefield`` environment.  See ``bytefield.py``.

``.. register::``
    Renders a ``register`` diagram.  See ``register.py``.

``.. regdesc::``
    Documents register fields using a plain RST definition list.
    See ``register.py``.

``.. listofregisters::``
    Inserts a list of all ``.. register::`` diagrams in the document.
    See ``register.py``.

Module layout
-------------
``pipeline.py``
    Shared LaTeX-to-SVG compilation pipeline.  No knowledge of any specific
    LaTeX package.

``bytefield.py``
    ``bytefield``-specific node, directive, template, and writer visitors.

``register.py``
    ``register``-specific nodes, directives, templates, writer visitors, and
    the ``doctree-resolved`` event handler for ``listofregisters``.

``__init__.py``  (this file)
    Sphinx ``setup()`` entry point.  Registers all nodes, directives, config
    values, and event handlers with the Sphinx application.
"""

from __future__ import annotations

from typing import Any

from .bytefield import (
    BytefieldDirective,
    bytefield_node,
    depart_bytefield_html,
    depart_bytefield_latex,
    depart_bytefield_unsupported,
    visit_bytefield_html,
    visit_bytefield_latex,
    visit_bytefield_unsupported,
)
from .register import (
    ListofregistersDirective,
    RegdescDirective,
    RegisterDirective,
    depart_listofregisters_html,
    depart_listofregisters_latex,
    depart_listofregisters_unsupported,
    depart_regdesc_html,
    depart_regdesc_latex,
    depart_regdesc_unsupported,
    depart_register_html,
    depart_register_latex,
    depart_register_unsupported,
    listofregisters_node,
    on_doctree_resolved,
    regdesc_node,
    register_node,
    visit_listofregisters_html,
    visit_listofregisters_latex,
    visit_listofregisters_unsupported,
    visit_regdesc_html,
    visit_regdesc_latex,
    visit_regdesc_unsupported,
    visit_register_html,
    visit_register_latex,
    visit_register_unsupported,
)

# ---------------------------------------------------------------------------
# Automatic preamble injection for LaTeX builds
# ---------------------------------------------------------------------------


def _on_config_inited(app: Any, config: Any) -> None:
    """
    Inject packages with options and custom commands into the LaTeX output.

    This event fires after ``conf.py`` has been fully processed but before
    any builder is created, so ``latex_elements`` modifications are
    guaranteed to take effect.

    Static packages with no options (``rotating``, ``xcolor``, ``graphicx``,
    ``array``, ``multirow``) are registered directly in ``setup()`` so they
    are always present regardless of the builder.

    ``bytefield`` and ``register`` are registered here because their options
    come from the ``bytefield_package_options`` and ``register_package_options``
    config values, which are only available after ``conf.py`` is processed.

    Custom commands are appended to ``latex_elements["preamble"]`` — there is
    no dedicated Sphinx API for ``\\newcommand`` / ``\\newlength`` definitions.
    """
    bf_opts = (getattr(config, "bytefield_package_options", "") or "").strip()
    app.add_latex_package("bytefield", bf_opts if bf_opts else None)

    reg_opts = (getattr(config, "register_package_options", "") or "").strip()
    app.add_latex_package("register", reg_opts if reg_opts else None)

    custom_commands = r"""
%% ---- custom commands injected by sphinxcontrib-archware -----------------
%% \colorbitbox[sides]{color}{width}{content}
\newcommand{\colorbitbox}[4][lrtb]{%
  \rlap{\bitbox[]{#3}{\textcolor{#2}{\rule{\width}{\height}}}}%
  \bitbox[#1]{#3}{#4}%
}
%% \bitlabel{width}{label}
\newcommand{\bitlabel}[2]{%
  \bitbox[]{#1}{%
    \raisebox{0pt}[4ex][0pt]{%
      \turnbox{45}{\fontsize{7}{7}\selectfont #2}%
    }%
  }%
}
%% \rotbitheader{label}
\newcommand{\rotbitheader}[1]{\bitlabel{1}{#1}}
%% \memsection{name}{size}{startaddr}{endaddr}
\newlength{\memsectionheight}
\setlength{\memsectionheight}{5\baselineskip}
\newcommand{\memsection}[4]{%
  \bytefieldsetup{bitheight=\memsectionheight}%
  \bitbox[]{6}{\tt\scriptsize\begin{tabular}{@{}r@{}}#3\\#4\end{tabular}}%
  \bitbox{26}{#1\\{\small(#2)}}%
}
%% \descbox{width}{content}
\newcommand{\descbox}[2]{%
  \bitbox{#1}{\parbox{\width}{\centering\small #2}}%
}
%% -------------------------------------------------------------------------
"""
    existing = config.latex_elements.get("preamble", "")
    config.latex_elements["preamble"] = custom_commands + existing


# ---------------------------------------------------------------------------
# Sphinx setup
# ---------------------------------------------------------------------------


def setup(app: Any) -> dict[str, Any]:
    """Register all nodes, directives, config values, and event handlers."""

    # ── Config values readable from conf.py ───────────────────────────────
    app.add_config_value("bytefield_package_options", default="", rebuild="env")
    app.add_config_value("register_package_options", default="", rebuild="env")

    # ── bytefield ─────────────────────────────────────────────────────────
    app.add_node(
        bytefield_node,
        html=(visit_bytefield_html, depart_bytefield_html),
        latex=(visit_bytefield_latex, depart_bytefield_latex),
        text=(visit_bytefield_unsupported, depart_bytefield_unsupported),
        man=(visit_bytefield_unsupported, depart_bytefield_unsupported),
        texinfo=(visit_bytefield_unsupported, depart_bytefield_unsupported),
    )
    app.add_directive("bytefield", BytefieldDirective)

    # ── register diagram ──────────────────────────────────────────────────
    app.add_node(
        register_node,
        html=(visit_register_html, depart_register_html),
        latex=(visit_register_latex, depart_register_latex),
        text=(visit_register_unsupported, depart_register_unsupported),
        man=(visit_register_unsupported, depart_register_unsupported),
        texinfo=(visit_register_unsupported, depart_register_unsupported),
    )
    app.add_directive("register", RegisterDirective)

    # ── register field descriptions ───────────────────────────────────────
    app.add_node(
        regdesc_node,
        html=(visit_regdesc_html, depart_regdesc_html),
        latex=(visit_regdesc_latex, depart_regdesc_latex),
        text=(visit_regdesc_unsupported, depart_regdesc_unsupported),
        man=(visit_regdesc_unsupported, depart_regdesc_unsupported),
        texinfo=(visit_regdesc_unsupported, depart_regdesc_unsupported),
    )
    app.add_directive("regdesc", RegdescDirective)

    # ── list of registers ─────────────────────────────────────────────────
    app.add_node(
        listofregisters_node,
        html=(visit_listofregisters_html, depart_listofregisters_html),
        latex=(visit_listofregisters_latex, depart_listofregisters_latex),
        text=(visit_listofregisters_unsupported, depart_listofregisters_unsupported),
        man=(visit_listofregisters_unsupported, depart_listofregisters_unsupported),
        texinfo=(visit_listofregisters_unsupported, depart_listofregisters_unsupported),
    )
    app.add_directive("listofregisters", ListofregistersDirective)

    # ── LaTeX packages (static, no options) ──────────────────────────────────
    # Called unconditionally from setup() so they are registered before any
    # builder or config processing occurs.  Sphinx only emits them when
    # actually building LaTeX output.
    for pkg in ("rotating", "xcolor", "graphicx", "array", "multirow"):
        app.add_latex_package(pkg)

    # ── Event handlers ────────────────────────────────────────────────────
    # config-inited fires after conf.py is fully processed but before any
    # builder is created — the earliest safe point to read config values
    # (bytefield_package_options, register_package_options) and to modify
    # latex_elements["preamble"].
    app.connect("config-inited", _on_config_inited)
    app.connect("doctree-resolved", on_doctree_resolved)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
