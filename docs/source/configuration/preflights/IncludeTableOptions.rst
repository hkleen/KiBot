.. _IncludeTableOptions:


IncludeTableOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **outputs** :index:`: <pair: preflight - include_table - include_table; outputs>`  [:ref:`IncTableOutputOptions parameters <IncTableOutputOptions>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: computed for your project) List of CSV-generating outputs.
   When empty we include all possible outputs.
-  ``enabled`` :index:`: <pair: preflight - include_table - include_table; enabled>` [:ref:`boolean <boolean>`] (default: ``true``) Enable the check. This is the replacement for the boolean value.
-  ``group_name`` :index:`: <pair: preflight - include_table - include_table; group_name>` [:ref:`string <string>`] (default: ``'kibot_table'``) Name for the group containing the table. The name of the group
   should be <group_name>_X where X is the output name. |br|
   When the output generates more than one CSV use *kibot_table_out[2]*
   to select the second CSV.

.. toctree::
   :caption: Used dicts

   IncTableOutputOptions
