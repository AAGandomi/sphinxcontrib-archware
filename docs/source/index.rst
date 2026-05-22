sphinxcontrib-archware
======================

A Sphinx extension that renders
`bytefield <https://ctan.org/pkg/bytefield>`_ and
`register <https://ctan.org/pkg/register>`_
LaTeX diagrams as inline SVG in HTML output.

The directive body is raw LaTeX. The extension compiles it on the fly using
your local TeX installation and splices the resulting SVG directly into the
HTML page — no external images, no JavaScript.

For LaTeX output the source is passed through unchanged, so your PDF builds
continue to use the native package rendering without any intermediate step.



Requirements
------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Requirement
     - Notes
   * - Python >= 3.9
     -
   * - Sphinx >= 5.0
     -
   * - A TeX distribution
     - `TeX Live <https://tug.org/texlive/>`_ or
       `MiKTeX <https://miktex.org/>`_
   * - ``latex`` + ``dvisvgm`` >= 2.9
     - **Recommended path** — see `Build pipeline`_. Both included in a full
       TeX Live install.
   * - ``pdflatex`` + SVG converter
     - Fallback path. Converter can be
       `Inkscape <https://inkscape.org/>`_ >= 1.0,
       `dvisvgm <https://dvisvgm.de/>`_ >= 2.9, or
       `pdf2svg <https://github.com/dawbarton/pdf2svg>`_.
   * - ``bytefield`` LaTeX package
     - Available in TeX Live as part of ``texlive-pictures``.
       In MiKTeX the package manager installs it on first use.
   * - ``register`` LaTeX package
     - Available in TeX Live as part of ``texlive-science``.
       In MiKTeX the package manager installs it on first use.


Installation
------------

Install from PyPI:

.. code-block:: bash

   pip install sphinxcontrib-archware

Then register the extension in ``conf.py``:

.. code-block:: python

   extensions = [
       "sphinxcontrib.archware",
   ]

The package lives under the ``sphinxcontrib`` namespace and is structured
as follows::

   sphinxcontrib/
     archware/
       __init__.py      ← Sphinx setup() entry point
       pipeline.py     ← shared LaTeX-to-SVG compilation pipeline
       bytefield.py    ← bytefield directive, node, and visitors
       register.py     ← register, regdesc, and listofregisters


Directives
----------

.. contents:: The following Sphinx directives are defined in this package
   :local:
   :depth: 1


``.. bytefield::``
~~~~~~~~~~~~~~~~~~

Renders a ``bytefield`` packet or register diagram.

The directive body contains only the *row* commands
(``\bitheader``, ``\bitbox``, ``\wordbox``, etc.).
The ``\begin{bytefield}[options]{bitwidth}`` / ``\end{bytefield}`` wrapper
is added automatically from ``:bitwidth:`` and ``:options:``.
Do not include the ``bytefield`` environment in the body.

.. code-block:: rst

   .. bytefield::
      :bitwidth: <n>
      :options:  <bytefield environment options>
      :packages: <pkg1>, <pkg2>, ...
      :align:    left | center | right
      :caption:  <text>
      :scale:    <0-100>
      :border:   <TeX length>

      \bitheader{...} \\
      \bitbox{...}{...} ...

.. list-table::
   :header-rows: 1
   :widths: 15 18 12 55

   * - Option
     - Type
     - Default
     - Description
   * - ``:bitwidth:``
     - positive integer
     - **required**
     - Width of the diagram in bits. Used as the mandatory argument to
       ``\begin{bytefield}{n}``.
   * - ``:options:``
     - string
     - *(none)*
     - Inserted verbatim as the optional argument of the ``bytefield``
       environment, e.g. ``bitheight=6ex, endianness=big``.
   * - ``:packages:``
     - string
     - *(none)*
     - Comma-separated list of extra LaTeX packages to load,
       e.g. ``color, hyperref``.
   * - ``:align:``
     - ``left`` | ``center`` | ``right``
     - ``center``
     - Horizontal alignment of the diagram within the page.
   * - ``:caption:``
     - string
     - *(none)*
     - Text rendered as a ``<figcaption>`` below the diagram.
   * - ``:scale:``
     - integer 0-100
     - ``100``
     - Scale factor as a percentage. ``75`` shrinks the SVG to 75 % of its
       natural size.
   * - ``:border:``
     - TeX length
     - ``6pt``
     - Padding added around the diagram before the page is cropped by the
       ``standalone`` class. Increase this if labels or annotations are
       clipped.


``.. register::``
~~~~~~~~~~~~~~~~~

Renders a hardware register diagram using the ``register`` LaTeX package.
Field names are typeset rotated at 45°, with bit positions and reset values
shown below each field.

The directive body contains only the row commands (``\regfield``,
``\reglabel``, ``\regnewline``, etc.).  The ``\begin{register}`` /
``\end{register}`` wrapper is added automatically.

For HTML output the diagram is compiled using ``\begin{register*}``
(unnumbered, no list-of-registers entry) to avoid float infrastructure
issues in the standalone document.  For LaTeX output the numbered
``\begin{register}`` float is emitted so that register numbering and
``\listofregisters`` work correctly.

.. code-block:: rst

   .. register::
      :name:     <register name>
      :address:  <memory offset>
      :bitwidth: <n>
      :color:
      :options:  <register package options>
      :packages: <pkg1>, <pkg2>, ...
      :align:    left | center | right
      :caption:  <text>
      :scale:    <0-100>
      :border:   <TeX length>

      \regfield{name}{length}{startbit}{reset}
      \reglabel{Reset}\regnewline
      ...

.. list-table::
   :header-rows: 1
   :widths: 15 18 12 55

   * - Option
     - Type
     - Default
     - Description
   * - ``:name:``
     - string
     - **required**
     - Register name shown in the caption and the list of registers.
   * - ``:address:``
     - string
     - *(none)*
     - Memory offset or address, e.g. ``0x250``. Appended to the caption in
       parentheses when set.
   * - ``:bitwidth:``
     - positive integer
     - ``32``
     - Maximum number of bits per row (sets ``\regBitWidth``).
   * - ``:color:``
     - flag
     - off
     - Enables the ``color`` option of the ``register`` package, allowing
       ``\regfield[color]{...}`` syntax for field background colours.
   * - ``:options:``
     - string
     - *(none)*
     - Additional options forwarded to ``\usepackage[...]{register}``,
       e.g. ``botcaption``.
   * - ``:packages:``
     - string
     - *(none)*
     - Comma-separated list of extra LaTeX packages to load.
   * - ``:align:``
     - ``left`` | ``center`` | ``right``
     - ``center``
     - Horizontal alignment of the diagram within the page.
   * - ``:caption:``
     - string
     - ``:name:``
     - Override for the HTML ``<figcaption>`` text. Defaults to the register
       name and address when not set.
   * - ``:scale:``
     - integer 0-100
     - ``100``
     - Scale factor as a percentage.
   * - ``:border:``
     - TeX length
     - ``6pt``
     - Padding added around the diagram before the page is cropped. The
       ``register`` package's rotated field names typically need more space
       than ``bytefield`` diagrams; ``12pt``-``16pt`` is a reasonable
       starting point.


``.. regdesc::``
~~~~~~~~~~~~~~~~

Documents the fields of the preceding register diagram using a plain RST
definition list. The content is rendered as searchable, accessible HTML
text — not baked into the SVG.

The body uses standard RST definition-list syntax: field name on one line,
description indented below. Inline markup (``code``, *emphasis*,
**bold**, hyperlinks) is fully supported and is preserved in LaTeX output.

For HTML output the list is rendered as a ``<dl class="regdesc">`` element.
For LaTeX output it is wrapped in the ``register`` package's ``regdesc`` /
``reglist`` environments, with the longest field name used to set the
correct label margin.

.. code-block:: rst

   .. regdesc::

      FieldName
         Description of the field. Inline markup is supported:
         ``code``, *emphasis*, **bold**.

      AnotherField
         Another description, possibly spanning multiple paragraphs.


``.. listofregisters::``
~~~~~~~~~~~~~~~~~~~~~~~~

Inserts a list of all ``.. register::`` directives in the document.

For HTML output a bullet list of internal hyperlinks is generated, each
linking to the corresponding diagram. For LaTeX output ``\listofregisters``
is emitted, producing the numbered list provided by the ``register``
package.

.. code-block:: rst

   .. listofregisters::

The list is built at ``doctree-resolved`` time, so it reflects the final
order of registers in the document regardless of where the directive appears.


Examples
--------

Fully working examples — covering every diagram from the ``bytefield`` and
``register`` package documentation — are provided:

.. toctree::

  examples/bytefield_examples
  examples/register_examples


Build pipeline
--------------

For each diagram directive the extension runs the following steps at HTML
write time:

.. code-block:: text

   .tex  --> latex     --> .dvi  --> dvisvgm        --> .svg  (recommended)
         --> pdflatex  --> .pdf  --> inkscape       --> .svg
                                 --> dvisvgm --pdf  --> .svg
                                 --> pdf2svg        --> .svg

The extension tries ``latex`` + ``dvisvgm`` (DVI path) first, falling back
to ``pdflatex`` and then the available PDF-to-SVG converter only if
``latex`` or ``dvisvgm`` is not found on ``PATH``.

**The DVI path is strongly recommended.** ``dvisvgm`` reads DVI natively and
converts text glyphs to precise SVG paths, producing output that is faithful
to the original LaTeX rendering — particularly for small or rotated text such
as bit-header labels and the rotated field names produced by the ``register``
package. The PDF path goes through an additional rasterisation step that can
introduce subtle degradation in text sharpness and positioning.

The pipeline is shared between the ``bytefield`` and ``register`` directives
and lives entirely in ``sphinxcontrib.archware.pipeline``, which has no
knowledge of either LaTeX package.

Caching
~~~~~~~

Compiled artefacts are cached in ``_build/archware/cache/`` using a SHA-256
hash of the full generated LaTeX source as the filename stem. All intermediate
files are kept alongside the final SVG:

.. code-block:: text

   _build/
     archware/cache/
       diagram-a3f1c8e2b4d70912.tex
       diagram-a3f1c8e2b4d70912.dvi   (or .pdf)
       diagram-a3f1c8e2b4d70912.log
       diagram-a3f1c8e2b4d70912.aux
       diagram-a3f1c8e2b4d70912.svg
     html/
     latex/

The cache directory sits one level above the format-specific output
directories so it is shared between ``make html``, ``make latexpdf``, etc.,
and it is expected to be wiped by ``make clean``

If a ``.svg`` file for a given hash already exists the entire compile +
convert pipeline is skipped, making incremental builds fast.

SVG inlining
~~~~~~~~~~~~

The XML declaration (``<?xml ... ?>``) and DOCTYPE are stripped before the SVG
is written into the HTML body, as both are invalid inside an HTML5 document.
Each diagram is wrapped in a ``<figure>`` element:

.. code-block:: text

   <!-- bytefield -->
   <figure class="bytefield-diagram" style="text-align:center; ... ">
     <svg ... > ... </svg>
     <figcaption>Caption text</figcaption>
   </figure>

   <!-- register -->
   <figure class="register-diagram" id="register-1-function-class" ... >
     <svg ... > ... </svg>
     <figcaption>Function Class (0x0008)</figcaption>
   </figure>

The CSS classes ``bytefield-diagram`` and ``register-diagram`` can be
targeted in your Sphinx theme's stylesheet to apply project-wide styling.
Each ``register`` figure also receives a stable ``id`` attribute derived
from its name and position, which is used by the ``listofregisters`` links.


LaTeX output
------------

When building with the LaTeX writer (e.g. ``make latexpdf``) the directive
body is emitted verbatim into the ``.tex`` source. Both the ``bytefield``
and ``register`` packages are loaded automatically in the LaTeX preamble —
no changes to ``latex_elements`` are needed.

Global package options can be set in ``conf.py`` via the following
configuration values:

.. code-block:: python

   # Options forwarded to \usepackage[...]{bytefield}
   bytefield_package_options = "bitheight=6ex, endianness=big"

   # Options forwarded to \usepackage[...]{register}
   register_package_options = "botcaption"

These apply globally to every diagram in the document. Per-diagram options
can still be set with ``:options:`` on individual directives.

For ``register`` diagrams Sphinx emits the numbered ``\begin{register}``
float (not the starred form), so register numbering and ``\listofregisters``
work correctly in the PDF output.


Referencing bytefield and register figures
------------------------------------------

The ``bytefield`` and ``register`` directives support cross-referencing through standard
Sphinx mechanisms.
While it is possible to use LaTeX ``\hyperref`` commands within the directives' LaTeX code,
these references are only resolved during LaTeX compilation and are not part of HTML builds.
This approach is therefore not portable across Sphinx builders and is not recommended.
The recommended Sphinx-native approach is to use the :name: option provided by the directive.
When set, Sphinx assigns a stable document target to the generated figure,
making it available for cross-referencing in both HTML and LaTeX outputs.

For example, for ``bytefield`` directive defines the name "TCP header structure":

.. code-block:: rst
    
  .. bytefield::
    :bitwidth: 32
    :caption: TCP header
    :name: TCP header structure

Hence the following usages of ``:ref:`` role:

.. code-block:: rst

  .. note:: You can use ``:ref:`` to link to archware figures. E.g. :ref:`TCP header structure` and :ref:`Function Class`.

will render as:

.. note::  You can use ``:ref:`` to link to archware figures. E.g. :ref:`TCP header structure` and :ref:`Function Class`.

This approach ensures that references are resolved uniformly across all Sphinx builders,
including HTML and LaTeX, without relying on backend-specific hyperlink mechanisms.


Troubleshooting
---------------

``Neither latex nor pdflatex found on PATH``
   Install TeX Live or MiKTeX and ensure the binaries are on ``PATH``. On
   Debian / Ubuntu: ``sudo apt install texlive-latex-extra``.

``SVG conversion failed``
   Install at least one of dvisvgm, Inkscape, or pdf2svg. On Debian /
   Ubuntu: ``sudo apt install dvisvgm`` or ``sudo apt install inkscape``.

``! LaTeX Error: File 'bytefield.sty' not found``
   The ``bytefield`` LaTeX package is missing from your TeX installation.
   On Debian / Ubuntu: ``sudo apt install texlive-pictures``.
   In MiKTeX the package manager installs it automatically on first use.

``! LaTeX Error: File 'register.sty' not found``
   The ``register`` LaTeX package is missing from your TeX installation.
   On Debian / Ubuntu: ``sudo apt install texlive-science``.
   In MiKTeX the package manager installs it automatically on first use.

Diagram is clipped
   The ``:border:`` option controls the padding added around the diagram
   before the page is cropped. The default is ``6pt``. If labels,
   curly-brace group annotations, or rotated field names are still cut off,
   increase it on the affected directive:

   .. code-block:: rst

      .. register::
         :name:    My Register
         :bitwidth: 32
         :border:  14pt

         ...

   Any valid TeX length is accepted (``8pt``, ``0.5cm``, ``2ex``, etc.).
   The ``register`` package's rotated field names typically need more space
   than ``bytefield`` diagrams; ``12pt``-``16pt`` is a reasonable starting
   point.

Compilation errors during development
   Every failed build preserves the ``.tex`` and ``.log`` files in
   ``_build/archware/cache/``. Inspect the ``.log`` to find the LaTeX
   error. The ``.tex`` file contains the full standalone document that was
   submitted to the compiler and can be compiled independently for debugging.
