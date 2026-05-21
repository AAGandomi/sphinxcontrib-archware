Register examples
=================

This page reproduces all diagrams from the ``register`` package documentation
(v2.0, Matthew Lovell).  Every example uses the ``.. register::`` directive.
Field descriptions are written with ``.. regdesc::``.

A ``.. listofregisters::`` at the top of this page generates the complete
list of registers:

.. listofregisters::


Diagnostic Control (Register 2.1)
----------------------------------

A 64-bit register with a large number of single-bit control and mask fields.
This example demonstrates how the ``register`` package handles narrow fields
by rotating the field names at 45°.

.. register::
   :name:     Diagnostic Control
   :address:  0x1F28
   :bitwidth: 64

   \regfield{reserved}{1}{63}{0}
   \regfield{cmp ack64}{1}{62}{0}
   \regfield{cmp req64}{1}{61}{0}
   \regfield{cmp devsel}{1}{60}{0}
   \regfield{cmp stop}{1}{59}{0}
   \regfield{cmp trdy}{1}{58}{0}
   \regfield{cmp irdy}{1}{57}{0}
   \regfield{cmp frame}{1}{56}{0}
   \regfield{reserved}{1}{55}{0}
   \regfield{mask ack64}{1}{54}{0}
   \regfield{mask req64}{1}{53}{0}
   \regfield{mask devsel}{1}{52}{0}
   \regfield{mask stop}{1}{51}{0}
   \regfield{mask trdy}{1}{50}{0}
   \regfield{mask irdy}{1}{49}{0}
   \regfield{mask frame}{1}{48}{0}
   \regfield{cmp cbe}{8}{40}{0}
   \regfield{mask cbe}{8}{32}{0}
   \reglabel{Reset}\regnewline
   \regfield{reserved}{1}{31}{0}
   \regfield{cmp arb}{7}{24}{0}
   \regfield{reserved}{1}{23}{0}
   \regfield{mask arb}{7}{16}{0}
   \regfield{reserved}{5}{11}{0}
   \regfield{grp en cntl}{1}{10}{0}
   \regfield{grp en cbe}{1}{9}{0}
   \regfield{grp en arb}{1}{8}{0}
   \regfield{grp en fifo}{1}{7}{0}
   \regfield{dly frame}{1}{6}{0}
   \regfield{level frame}{1}{5}{0}
   \regfield{level cntl}{1}{4}{0}
   \regfield{level cbe}{1}{3}{0}
   \regfield{level arb}{1}{2}{0}
   \regfield{hlt trg on 1}{1}{1}{0}
   \regfield{alwys cnt 1}{1}{0}{0}
   \reglabel{Reset}


Function Class (Register 2.2)
------------------------------

A 64-bit PCI function class register with field descriptions.  This example
is taken from the ``register`` package documentation and shows the combination
of a register diagram with a ``.. regdesc::`` block.

.. register::
   :name:     Function Class
   :address:  0x0008
   :bitwidth: 64

   \regfield{BIST}{8}{56}{0}
   \regfield{Header Type}{8}{48}{0}
   \regfield{Latency Timer}{8}{40}{0}
   \regfield{Line Size}{8}{32}{0}
   \reglabel{Reset}\regnewline
   \regfield{Class Code}{24}{8}{{0x060000}}
   \regfield{Revision}{8}{0}{{0x10}}
   \reglabel{Reset}

.. regdesc::

   BIST
      (Read only) Always returns 0.

   Header Type
      (Read only) Always returns 0.

   Latency Timer
      PCI Latency Timer value (PCI 2.2 spec, Section 6.2.4).

   Line Size
      PCI Cache Line Size (PCI 2.2 spec, Section 6.2.4).
      Valid values are listed below; any other value will be treated as
      indicating 64 byte cache lines.

      - ``0010 0000`` — 128 bytes
      - ``0001 0000`` — 64 bytes

   Class Code
      (Read only) PCI Class Code (PCI 2.2 spec, Section 6.2.1).
      Chip identifies itself as a Host bridge.

   Revision
      (Read only) Chip revision number.  Bits 4-7 provide the major revision
      number, and bits 0-3 provide the minor revision number.


Example register (Register 3.1)
---------------------------------

The worked example from section 3 of the ``register`` documentation.  A
64-bit register split across two rows using ``\regnewline``.

.. register::
   :name:     Example
   :address:  0x250
   :bitwidth: 32

   \regfield{FIFO depth}{6}{58}{{random}}
   \regfield{Something}{4}{54}{1100}
   \regfield{Status}{21}{33}{{uninitialized}}
   \regfield{Enable}{1}{32}{1}
   \reglabel{Reset}\regnewline
   \regfield{Counter}{10}{22}{{0x244}}
   \regfield{Howdy}{5}{17}{1\_1010}
   \regfield{Control}{1}{16}{-}
   \regfield{Hardfail}{1}{15}{1}
   \regfield{Data}{15}{0}{{uninitialized}}
   \reglabel{Reset}


Configuration (Register 3.2)
------------------------------

A 64-bit configuration register showing the ``regdesc`` / ``reglist``
field description pattern from the ``register`` documentation.

.. register::
   :name:     Configuration
   :address:  0x2848
   :bitwidth: 32

   \regfield{soft reset perf}{1}{63}{0}
   \regfield{reserved}{30}{33}{0}
   \regfield{Test mode}{1}{32}{0}
   \reglabel{Reset}\regnewline
   \regfield{reserved}{13}{19}{0}
   \regfield{Request Depth}{7}{12}{1}
   \regfield{reserved}{3}{9}{0}
   \regfield{line\_2x\_L}{1}{8}{?}
   \regfield{reserved}{1}{7}{0}
   \regfield{ill\_cmd\_enable}{1}{6}{0}
   \regfield{LPCE}{1}{5}{0}
   \regfield{DVI disable}{1}{4}{0}
   \regfield{SBA enable}{1}{3}{0}
   \regfield{reserved}{2}{1}{0}
   \regfield{line\_2x\_enable}{1}{0}{0}
   \reglabel{Reset}

.. regdesc::

   line\_2x\_enable
      Setting this bit enables the chip to utilize a second connected data
      line.

   SBA enable
      Setting this bit activates the sideband-address port.  The SBA port
      is only useable in a double-line configuration.

   DVI disable
      Setting this bit *turns off* DVI extraction for DMA requests.

   LPCE
      Line Parity Check Enable.

   ill\_cmd\_enable
      Illegal Command enable.

   line\_2x\_L
      (Read only) Indicates whether this chip is connected to a second data
      line.  When this bit is 0, a second line is available.

   Request Depth
      Controls number of outstanding DMA requests.

   Test mode
      Activates data line test mode.

   soft reset perf
      Indicates that a soft reset has been performed.


Color Example (Register 3.3)
------------------------------

The same register as section 3.1, but with selected fields given background
colours using the ``:color:`` option.

.. register::
   :name:     Color Example
   :address:  0x250
   :bitwidth: 32
   :color:

   \regfield{FIFO depth}{6}{58}{{random}}
   \regfield[green!30]{Something}{4}{54}{1100}
   \regfield[gray!20]{Status}{21}{33}{{uninitialized}}
   \regfield{Enable}{1}{32}{1}
   \reglabel{Reset}\regnewline
   \regfield{Counter}{10}{22}{{0x244}}
   \regfield[red!20]{Howdy}{5}{17}{1\_1010}
   \regfield{Control}{1}{16}{-}
   \regfield[yellow!50]{Hardfail}{1}{15}{1}
   \regfield[gray!20]{Data}{15}{0}{{uninitialized}}
   \reglabel{Reset}


Address and BE phases (Figure 1)
----------------------------------

Figure 1 from the ``register`` documentation — a register diagram produced
*without* reset values using ``\regfieldb``.  This is an unnumbered figure
rather than a register float in the original document; here it is rendered
as a ``.. register::`` directive.

.. register::
   :name:     Address and BE phases for register access
   :bitwidth: 16

   \regfieldb{write en}{1}{15}
   \regfieldb{reserved}{2}{13}
   \regfieldb{function}{1}{12}
   \regfieldb{block}{4}{8}
   \regfieldb{register}{5}{3}
   \regfieldb{reserved}{3}{0}
   \regnewline
   \regfieldb{reserved}{8}{8}
   \regfieldb{BE}{8}{0}


Register with no offset
------------------------

The ``register`` package allows the address argument to be empty.  In that
case the caption shows only the register name.

.. register::
   :name:     Control Word
   :bitwidth: 32

   \regfield{Enable}{1}{31}{0}
   \regfield{Mode}{3}{28}{000}
   \regfield{reserved}{12}{16}{0}
   \regfield{Threshold}{16}{0}{{0x0000}}
   \reglabel{Reset}


Wide register with many rows
------------------------------

A 64-bit register split into two 32-bit rows, demonstrating ``\regnewline``
and the ``\regBitWidth`` / ``:bitwidth:`` option.

.. register::
   :name:     Descriptor Word
   :address:  0x100
   :bitwidth: 32

   \regfield{Valid}{1}{63}{0}
   \regfield{Type}{3}{60}{000}
   \regfield{Length}{12}{48}{{0x000}}
   \regfield{Flags}{8}{40}{{0x00}}
   \regfield{Priority}{8}{32}{{0x00}}
   \reglabel{Reset}\regnewline
   \regfield{Base Address}{32}{0}{{0x00000000}}
   \reglabel{Reset}

.. regdesc::

   Valid
      Set to 1 when this descriptor entry is valid and ready for processing.

   Type
      Descriptor type.  ``000`` = data, ``001`` = command, ``010`` = status.

   Length
      Transfer length in bytes minus one.  Maximum transfer is 4096 bytes.

   Flags
      Control flags.  Bit 7: interrupt on completion.  Bit 6: chain to next
      descriptor.  Bits 5-0: reserved, must be zero.

   Priority
      Arbitration priority.  Higher values indicate higher priority.

   Base Address
      32-bit physical address of the associated data buffer.
