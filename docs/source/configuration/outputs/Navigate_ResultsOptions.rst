.. _Navigate_ResultsOptions:


Navigate_ResultsOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **link_from_root** :index:`: <pair: output - navigate_results - options; link_from_root>` [:ref:`string <string>`] (default: ``''``) The name of a file to create at the main output directory linking to the home page.
-  **output** :index:`: <pair: output - navigate_results - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=html, %x=navigate). Affected by global options.
-  ``header`` :index:`: <pair: output - navigate_results - options; header>` [:ref:`boolean <boolean>`] (default: ``true``) Add a header containing information for the project.
-  ``logo`` :index:`: <pair: output - navigate_results - options; logo>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) PNG file to use as logo, use false to remove.
   The KiBot logo is used by default.

-  ``logo_url`` :index:`: <pair: output - navigate_results - options; logo_url>` [:ref:`string <string>`] (default: ``'https://github.com/INTI-CMNB/KiBot/'``) Target link when clicking the logo.
-  ``nav_bar`` :index:`: <pair: output - navigate_results - options; nav_bar>` [:ref:`boolean <boolean>`] (default: ``true``) Add a side navigation bar to quickly access to the outputs.
-  ``skip_not_run`` :index:`: <pair: output - navigate_results - options; skip_not_run>` [:ref:`boolean <boolean>`] (default: ``false``) Skip outputs with `run_by_default: false`.
-  ``title`` :index:`: <pair: output - navigate_results - options; title>` [:ref:`string <string>`] (default: ``''``) Title for the page, when empty KiBot will try using the schematic or PCB title.
   If they are empty the name of the project, schematic or PCB file is used. |br|
   You can use %X values and KiCad variables here.
-  ``title_url`` :index:`: <pair: output - navigate_results - options; title_url>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) Target link when clicking the title, use false to remove.
   KiBot will try with the origin of the current git repo when empty.


