Bytefield examples
==================

This page reproduces all diagrams from the ``bytefield`` package documentation.
Every example uses the ``.. bytefield::`` directive — the
``\begin{bytefield}`` / ``\end{bytefield}`` wrapper is added automatically
from ``:bitwidth:``.  The custom commands ``\colorbitbox``, ``\bitlabel``,
``\rotbitheader``, ``\memsection``, and ``\descbox`` are always available
without any extra ``:packages:`` option.


Basic bit fields
----------------

The simplest possible diagram — a header row followed by named fields.

.. bytefield::
   :bitwidth: 16
   :caption: Simple 16-bit word

   \bitheader{0-15} \\
   \bitbox{4}{Type} &
   \bitbox{4}{Flags} &
   \bitbox{8}{Value}


IPv4 header
-----------

A full IPv4 packet header, spanning four 32-bit rows.

.. bytefield::
   :bitwidth: 32
   :caption: IPv4 header

   \bitheader{0,3-4,7-8,15-16,18-19,23-24,31} \\
   \bitbox{4}{Version} &
   \bitbox{4}{IHL} &
   \bitbox{6}{DSCP} &
   \bitbox{2}{ECN} &
   \bitbox{16}{Total Length} \\
   \bitbox{16}{Identification} &
   \bitbox{1}{0} &
   \bitbox{1}{DF} &
   \bitbox{1}{MF} &
   \bitbox{13}{Fragment Offset} \\
   \bitbox{8}{TTL} &
   \bitbox{8}{Protocol} &
   \bitbox{16}{Header Checksum} \\
   \wordbox{1}{Source Address} \\
   \wordbox{1}{Destination Address} \\
   \wordbox[lrt]{1}{\small Options (if IHL $>$ 5)} \\
   \skippedwords \\
   \wordbox[lrb]{1}{}


IPv6 header
-----------

IPv6 uses a fixed 40-byte header with no options.

.. bytefield::
   :bitwidth: 32
   :caption: IPv6 header

   \bitheader{0,3-4,11-12,15-16,23-24,31} \\
   \bitbox{4}{Version} &
   \bitbox{8}{Traffic Class} &
   \bitbox{20}{Flow Label} \\
   \bitbox{16}{Payload Length} &
   \bitbox{8}{Next Header} &
   \bitbox{8}{Hop Limit} \\
   \wordbox{4}{Source Address (128 bits)} \\
   \wordbox{4}{Destination Address (128 bits)}


TCP header
----------

TCP with all flag bits labelled using rotated single-bit headers.

.. bytefield::
   :bitwidth: 32
   :caption: TCP header
   :name: TCP header structure

   \bitheader{0,15-16,31} \\
   \bitbox{16}{Source Port} &
   \bitbox{16}{Destination Port} \\
   \wordbox{1}{Sequence Number} \\
   \wordbox{1}{Acknowledgement Number} \\
   \bitbox{4}{Data Offset} &
   \bitbox{3}{Res.} &
   \rotbitheader{NS} &
   \rotbitheader{CWR} &
   \rotbitheader{ECE} &
   \rotbitheader{URG} &
   \rotbitheader{ACK} &
   \rotbitheader{PSH} &
   \rotbitheader{RST} &
   \rotbitheader{SYN} &
   \rotbitheader{FIN} &
   \bitbox{16}{Window Size} \\
   \bitbox{16}{Checksum} &
   \bitbox{16}{Urgent Pointer} \\
   \wordbox[lrt]{1}{\small Options (0--320 bits, if Data Offset $>$ 5)} \\
   \skippedwords \\
   \wordbox[lrb]{1}{}


UDP header
----------

A simple 8-byte fixed header.

.. bytefield::
   :bitwidth: 32
   :caption: UDP header

   \bitheader{0,15-16,31} \\
   \bitbox{16}{Source Port} &
   \bitbox{16}{Destination Port} \\
   \bitbox{16}{Length} &
   \bitbox{16}{Checksum}


Big-endian bit numbering
------------------------

Use ``:options: endianness=big`` to place bit 0 on the right and the
highest bit number on the left, as is common in many hardware reference
manuals.

.. bytefield::
   :bitwidth: 32
   :options: endianness=big
   :caption: 32-bit register (big-endian bit numbering)

   \bitheader{0,7-8,15-16,23-24,31} \\
   \bitbox{8}{Field D} &
   \bitbox{8}{Field C} &
   \bitbox{8}{Field B} &
   \bitbox{8}{Field A}


Custom bit height
-----------------

Use ``bitheight`` to make rows taller, giving more room for multi-line
labels.

.. bytefield::
   :bitwidth: 32
   :options: bitheight=8ex
   :caption: Tall rows with multi-line field names

   \bitheader{0,7-8,15-16,23-24,31} \\
   \bitbox{8}{Destination\\Address} &
   \bitbox{8}{Source\\Address} &
   \bitbox{4}{Data\\Type} &
   \bitbox{4}{Seq\\Num} &
   \bitbox{8}{Payload\\Length}


Right word group
----------------

``\begin{rightwordgroup}`` draws a curly brace with a label to the right
of the diagram, grouping one or more rows.

.. bytefield::
   :bitwidth: 32
   :caption: Grouped rows with right label

   \bitheader{0,15-16,31} \\
   \begin{rightwordgroup}{Header}
     \bitbox{16}{Source Port} & \bitbox{16}{Destination Port} \\
     \wordbox{1}{Sequence Number} \\
     \wordbox{1}{Acknowledgement Number}
   \end{rightwordgroup} \\
   \begin{rightwordgroup}{Payload}
     \wordbox[lrt]{1}{\small Data} \\
     \skippedwords \\
     \wordbox[lrb]{1}{}
   \end{rightwordgroup}


Left word group
---------------

``\begin{leftwordgroup}`` places the curly brace and label on the left.

.. bytefield::
   :bitwidth: 32
   :caption: Left-labelled groups

   \bitheader{0,15-16,31} \\
   \begin{leftwordgroup}{Control\\Words}
     \bitbox{8}{Op} & \bitbox{8}{Flags} & \bitbox{16}{Operand} \\
     \wordbox{1}{Extended Operand}
   \end{leftwordgroup} \\
   \begin{leftwordgroup}{Data\\Words}
     \wordbox[lrt]{1}{Payload} \\
     \skippedwords \\
     \wordbox[lrb]{1}{}
   \end{leftwordgroup}


Skipped words
-------------

``\skippedwords`` draws a cross-hatched stripe indicating that a variable
number of rows has been omitted.

.. bytefield::
   :bitwidth: 32
   :caption: Variable-length field with skipped words

   \bitheader{0,31} \\
   \wordbox[lrt]{1}{First data word} \\
   \skippedwords \\
   \wordbox[lrb]{1}{Last data word}


Selective borders
-----------------

Pass a border-side string as the optional first argument to ``\bitbox`` or
``\wordbox``.  Lowercase enables a side; uppercase disables it.  Here
adjacent cells share a border by disabling the right edge of the left cell.

.. bytefield::
   :bitwidth: 32
   :caption: Cells with selective borders

   \bitheader{0,7-8,15-16,23-24,31} \\
   \bitbox{8}{A} &
   \bitbox[lrt]{8}{B} &
   \bitbox[lrtB]{8}{C} &
   \bitbox{8}{D} \\
   \bitbox[lrb]{8}{} &
   \bitbox[rb]{8}{B cont.} &
   \bitbox[lrb]{8}{} &
   \bitbox{8}{}


Coloured bit boxes
------------------

``\colorbitbox`` (always available, no extra ``:packages:`` needed) draws a
solid background colour behind the cell.

.. bytefield::
   :bitwidth: 32
   :caption: Coloured fields

   \bitheader{0,7-8,15-16,23-24,31} \\
   \colorbitbox{red!20}{8}{Type} &
   \colorbitbox{green!25}{8}{Flags} &
   \colorbitbox{blue!20}{8}{Sequence} &
   \colorbitbox{yellow!30}{8}{Checksum} \\
   \colorbitbox{cyan!20}{16}{Source Address} &
   \colorbitbox{magenta!15}{16}{Destination Address}


Rotated bit labels
------------------

``\bitlabel{width}{text}`` renders a borderless cell with the text rotated
45° upward.  Use it in a header row above narrow fields.  ``\rotbitheader``
is a shorthand for single-bit labels.

.. bytefield::
   :bitwidth: 16
   :caption: Status register with rotated single-bit labels

   \bitlabel{4}{} &
   \rotbitheader{OVF} &
   \rotbitheader{ZRO} &
   \rotbitheader{NEG} &
   \rotbitheader{CRY} &
   \rotbitheader{IRQ} &
   \rotbitheader{NMI} &
   \rotbitheader{BRK} &
   \rotbitheader{STP} &
   \rotbitheader{HLT} &
   \rotbitheader{DBG} &
   \rotbitheader{RES} &
   \bitlabel{4}{} \\
   \bitbox{4}{\small Reserved} &
   \bitbox{1}{V} &
   \bitbox{1}{Z} &
   \bitbox{1}{N} &
   \bitbox{1}{C} &
   \bitbox{1}{I} &
   \bitbox{1}{M} &
   \bitbox{1}{B} &
   \bitbox{1}{S} &
   \bitbox{1}{H} &
   \bitbox{1}{D} &
   \bitbox{1}{R} &
   \bitbox{4}{\small Reserved}


Description boxes
-----------------

``\descbox{width}{text}`` wraps long text in a centred ``\parbox`` inside
the cell, allowing multi-line descriptions in wide fields.

.. bytefield::
   :bitwidth: 32
   :caption: Fields with wrapped descriptions

   \bitheader{0,15-16,31} \\
   \descbox{16}{Destination port number (0--65535)} &
   \descbox{16}{Source port number (0--65535)} \\
   \descbox{32}{Payload data — content and interpretation depend on the
   protocol identified by the port numbers above}


Memory map
----------

``\memsection{name}{size}{startaddr}{endaddr}`` renders a single row of a
32-bit memory map diagram.  The address labels appear in the 6-bit-wide
left column; the region name and size fill the remaining 26 bits.

.. bytefield::
   :bitwidth: 32
   :caption: System memory map

   \memsection{Boot ROM}{32 KB}{0x0000}{0x7FFF} \\
   \memsection{SRAM}{64 KB}{0x8000}{0x17FFF} \\
   \memsection{Peripheral bus}{128 KB}{0x18000}{0x37FFF} \\
   \memsection{Reserved}{}{0x38000}{0xEFFFF} \\
   \memsection{Flash}{64 KB}{0xF0000}{0xFFFFF}


MTP protocol (hyperref usage)
------------------------------------

.. warning:: ``hyperref`` usage is not recommended.

   Regular Sphinx labels and ``:ref:`` can be used to link to a specific
   ``bytefield`` figure with the ``:name:`` option.
   E.g. :ref:`TCP header structure`.

This example is taken directly from the ``bytefield`` package documentation.
It shows how hyperlinks can be embedded inside bit fields using the
``hyperref`` package.

.. bytefield::
   :bitwidth: 32
   :packages: hyperref
   :caption: MTP packet format

   \bitheader{0,7-8,15-16,23-24,31} \\
   \begin{rightwordgroup}{transport \\ header}
     \bitbox{8}{\hyperlink{pv}{\parbox{\width}{\centering protocol version}}} &
     \bitbox{8}{\hyperlink{pt}{packet type}} &
     \bitbox{8}{\hyperlink{tm}{type modifier}} &
     \bitbox{8}{\hyperlink{cc}{client channel}} \\
     \wordbox{1}{\hyperlink{sc}{source connection identifier}} \\
     \wordbox{1}{\hyperlink{dc}{destination connection identifier}} \\
     \wordbox{1}{\hyperlink{ma}{message acceptance criteria}} \\
     \wordbox{1}{\hyperlink{hb}{heartbeat}} \\
     \bitbox{16}{\hyperlink{wn}{window}} &
     \bitbox{16}{\hyperlink{rt}{retention}}
   \end{rightwordgroup} \\
   \begin{rightwordgroup}{data \\ fields}
     \wordbox[lrt]{1}{%
       \parbox{0.6\width}{\centering (data content and format
       dependent on packet type and modifier)}} \\
     \skippedwords \\
     \wordbox[lrb]{1}{}
   \end{rightwordgroup}


Multiple bit-header ranges
--------------------------

``\bitheader`` accepts comma-separated values and ranges.  Only the listed
bit positions receive a label.

.. bytefield::
   :bitwidth: 32
   :caption: Sparse bit header

   \bitheader{0,7-8,15-16,23-24,31} \\
   \bitbox{8}{Byte 3 (MSB)} &
   \bitbox{8}{Byte 2} &
   \bitbox{8}{Byte 1} &
   \bitbox{8}{Byte 0 (LSB)}


\bitboxes shorthand
-------------------

``\bitboxes{n}{labels}`` is shorthand for a sequence of equal-width boxes.
Each character of the string produces one cell.

.. bytefield::
   :bitwidth: 8
   :caption: Eight 1-bit flag fields

   \bitheader{0-7} \\
   \bitboxes{1}{ABCDEFGH}


Little-endian numbering with lsb offset
----------------------------------------

Set ``endianness=little`` and ``lsb`` to start numbering from a value
other than zero, matching hardware reference manual conventions.

.. bytefield::
   :bitwidth: 16
   :options: endianness=little, lsb=16
   :caption: Bits 16--31 of a 32-bit register

   \bitheader{16-31} \\
   \bitbox{8}{High byte (bits 31:24)} &
   \bitbox{8}{Low byte (bits 23:16)}
