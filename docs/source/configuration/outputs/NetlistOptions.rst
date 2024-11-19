.. _NetlistOptions:


NetlistOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

-  **format** :index:`: <pair: output - netlist - options; format>` [:ref:`string <string>`] (default: ``'classic'``) (choices: "classic", "ipc") The `classic` format is the KiCad internal format, and is generated
   from the schematic. The `ipc` format is the IPC-D-356 format, useful for PCB
   testing, is generated from the PCB.
-  **output** :index:`: <pair: output - netlist - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=netlist/IPC-D-356, %x=net/d356). Affected by global options.
-  ``dnf_filter`` :index:`: <pair: output - netlist - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the variant.

-  ``exclude_filter`` :index:`: <pair: output - netlist - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the variant.

-  ``pre_transform`` :index:`: <pair: output - netlist - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the variant.

-  ``variant`` :index:`: <pair: output - netlist - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Used for sub-PCBs.

