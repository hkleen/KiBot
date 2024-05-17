# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: MIT
# Project: KiBot (formerly KiPlot)
"""
# Internal BoM (Bill of Materials) output for KiBot.
# This is somehow compatible with KiBoM.
Dependencies:
  - from: KiCost
    role: Find components costs and specs
    version: 1.1.8
  - from: RSVG
    role: SVG logos for the BoM
  - name: XLSXWriter
    role: Create XLSX files
    python_module: true
    debian: python3-xlsxwriter
    arch: python-xlsxwriter
    version: 1.1.2
    downloader: python
"""
import csv
from copy import deepcopy
import os
import re
from .gs import GS
from .misc import W_BADFIELD, W_NEEDSPCB, DISTRIBUTORS, W_NOPART, W_MISSREF, DISTRIBUTORS_STUBS, DISTRIBUTORS_STUBS_SEPS
from .optionable import Optionable, BaseOptions
from .registrable import RegOutput
from .error import KiPlotConfigurationError
from .kiplot import get_board_comps_data, load_any_sch, register_xmp_import, expand_fields, run_command
from .kicad.v5_sch import SchematicComponent, SchematicField
from .bom.columnlist import ColumnList, BoMError
from .bom.bom import do_bom
from .var_kibom import KiBoM
from .fil_base import (BaseFilter, apply_exclude_filter, apply_fitted_filter, apply_fixed_filter, reset_filters,
                       KICOST_NAME_TRANSLATIONS, apply_pre_transform)
from .macros import macros, document, output_class  # noqa: F401
from . import log
# To debug the `with document` we can use:
# from .mcpyrate.debug import macros, step_expansion
# with step_expansion:

logger = log.get_logger()
VALID_STYLES = {'modern-blue', 'modern-green', 'modern-red', 'classic'}
DEFAULT_ALIASES = [['r', 'r_small', 'res', 'resistor'],
                   ['l', 'l_small', 'inductor'],
                   ['c', 'c_small', 'cap', 'capacitor'],
                   ['sw', 'switch'],
                   ['zener', 'zenersmall'],
                   ['d', 'diode', 'd_small'],
                   ]


class CompsFromCSV(object):
    """ Class used to fake an schematic using a CSV file """
    def __init__(self, fname, comps):
        super().__init__()
        self.revision = ''
        self.date = GS.format_date('', fname, 'SCH')
        self.title = os.path.basename(fname)
        self.company = ''
        self.comps = comps

    def get_components(self):
        return self.comps


class BoMJoinField(Optionable):
    """ Fields to join """
    def __init__(self, field=None):
        super().__init__()
        if field:
            self.field = field.lower()
            self.text = None
            self.text_before = ''
            self.text_after = ''
            return
        self._unknown_is_error = True
        with document:
            self.field = ''
            """ *Name of the field """
            self.text = ''
            """ Text to use instead of a field. This option is incompatible with the `field` option.
                Any space to separate it should be added in the text.
                Use \\n for newline and \\t for tab """
            self.text_before = ''
            """ Text to add before the field content. Will be added only if the field isn't empty.
                Any space to separate it should be added in the text.
                Use \\n for newline and \\t for tab """
            self.text_after = ''
            """ Text to add after the field content. Will be added only if the field isn't empty.
                Any space to separate it should be added in the text.
                Use \\n for newline and \\t for tab """
        self._field_example = 'Voltage'
        self._nl = re.compile(r'([^\\]|^)\\n')
        self._tab = re.compile(r'([^\\]|^)\\t')

    def unescape(self, text):
        text = self._nl.sub(r'\1\n', text)
        text = self._tab.sub(r'\1\t', text)
        return text

    def config(self, parent):
        super().config(parent)
        if not self.field and not self.text:
            raise KiPlotConfigurationError("Missing or empty `field` and `text` in join list ({})".format(str(self._tree)))
        if self.field and self.text:
            raise KiPlotConfigurationError("You can't specify a `field` and a `text` in a join list ({})".
                                           format(str(self._tree)))
        self.field = self.field.lower()
        if self.text_before is None:
            self.text_before = ''
        if self.text_after is None:
            self.text_after = ''
        self.text = self.unescape(self.text)
        self.text_before = self.unescape(self.text_before)
        self.text_after = self.unescape(self.text_after)

    def get_text(self, field_getter):
        if self.text:
            return self.text
        value = field_getter(self.field)
        if not value:
            return None
        separator = '' if self.text_before else ' '
        return separator + self.text_before + value + self.text_after

    def __repr__(self):
        if self.text:
            return '`{}`'.format(self.text)
        return '`{}`+{}+`{}`'.format(self.text_before, self.field, self.text_after)


class BoMColumns(Optionable):
    """ Information for the BoM columns """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.field = ''
            """ *Name of the field to use for this column.
                Use `_field_lcsc_part` to get the value defined in the global options """
            self.name = ''
            """ *Name to display in the header. The field is used when empty """
            self.join = BoMJoinField
            """ [list(dict)|list(string)|string=''] List of fields to join to this column """
            self.level = 0
            """ Used to group columns. The XLSX output uses it to collapse columns """
            self.comment = ''
            """ Used as explanation for this column. The XLSX output uses it """
        self._field_example = 'Row'
        self._name_example = 'Line'

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError("Missing or empty `field` in columns list ({})".format(str(self._tree)))
        self.field = self.solve_field_name(self.field)
        field = self.field.lower()
        # Ensure this is None or a list
        # Also arrange it as field, cols...
        if isinstance(self.join, type):
            self.join = None
        elif isinstance(self.join, str):
            if self.join:
                self.join = [field, BoMJoinField(self.join)]
            else:
                self.join = None
        else:
            join = [field]
            for c in self.join:
                if isinstance(c, str):
                    join.append(BoMJoinField(c))
                else:
                    join.append(c)
            self.join = join


class RowColors(Optionable):
    """ Filters to give colors to rows """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.description = ''
            """ *A description for this color, must be filled """
            self.color = '#FF8080'
            """ *Color used for this category """
            self.filter = Optionable
            """ *[string|list(string)='_none'] Name of the filter to match.
                Be careful because this filter should be coherent with the grouping fields.
                KiBot will assume that all the components grouped in the same group will
                return the same value when applying this filter """
        self._description_example = "Components that can't be replaced"

    def config(self, parent):
        super().config(parent)
        self.validate_colors(['color'])
        if not self.description:
            raise KiPlotConfigurationError('You must add a description for a colored row')
        if isinstance(self.filter, type):
            raise KiPlotConfigurationError('You must provide a filter to match the rows')
        self.filter = BaseFilter.solve_filter(self.filter, 'colored rows')


class BoMLinkable(Optionable):
    """ Base class for HTML and XLSX formats """
    def __init__(self):
        super().__init__()
        with document:
            self.col_colors = True
            """ Use colors to show the field type """
            self.datasheet_as_link = ''
            """ *Column with links to the datasheet """
            self.digikey_link = Optionable
            """ [string|list(string)=''] Column/s containing Digi-Key part numbers, will be linked to web page """
            self.mouser_link = Optionable
            """ [string|list(string)=''] Column/s containing Mouser part numbers, will be linked to web page """
            self.lcsc_link = Optionable
            """ [boolean|string|list(string)=''] Column/s containing LCSC part numbers, will be linked to web page.
                Use **true** to copy the value indicated by the `field_lcsc_part` global option """
            self.generate_dnf = True
            """ *Generate a separated section for DNF (Do Not Fit) components """
            self.hide_pcb_info = False
            """ Hide project information """
            self.hide_stats_info = False
            """ Hide statistics information """
            self.highlight_empty = True
            """ Use a color for empty cells. Applies only when `col_colors` is `true` """
            self.logo = Optionable
            """ *[string|boolean=''] PNG/SVG file to use as logo, use false to remove.
                Note that when using an SVG this is first converted to a PNG using `logo_width` """
            self.logo_width = 370
            """ Used when the logo is an SVG image. This width is used to render the SVG image """
            self.title = 'KiBot Bill of Materials'
            """ *BoM title """
            self.extra_info = Optionable
            """ [string|list(string)=''] Information to put after the title and before the pcb and stats info """
            self.row_colors = RowColors
            """ [list(dict)] Used to highlight rows using filters. Rows that match a filter can be colored.
                Note that these rows won't have colored columns """

    def config(self, parent):
        super().config(parent)
        # *_link
        self.digikey_link = self.force_list(self.digikey_link, comma_sep=False, lower_case=True)
        self.mouser_link = self.force_list(self.mouser_link, comma_sep=False, lower_case=True)
        if isinstance(self.lcsc_link, bool):
            self.lcsc_link = self.field_lcsc_part if self.lcsc_link else ''
        self.lcsc_link = self.force_list(self.lcsc_link, comma_sep=False, lower_case=True)
        # Logo
        if isinstance(self.logo, type):
            self.logo = ''
        elif isinstance(self.logo, bool):
            self.logo = '' if self.logo else None
        elif self.logo:
            if not os.path.isabs(self.logo):
                self.logo = os.path.abspath(os.path.expandvars(os.path.expanduser(self.logo)))
            if not os.path.isfile(self.logo):
                raise KiPlotConfigurationError('Missing logo file `{}`'.format(self.logo))
        # Extra info lines
        self.extra_info = Optionable.force_list(self.extra_info, comma_sep=False)
        # Datasheet as link
        self.datasheet_as_link = self.datasheet_as_link.lower()
        # Row colors
        if isinstance(self.row_colors, type):
            self.row_colors = []


class BoMHTML(BoMLinkable):
    """ HTML options """
    def __init__(self):
        super().__init__()
        with document:
            self.style = 'modern-blue'
            """ Page style. Internal styles: modern-blue, modern-green, modern-red and classic.
                Or you can provide a CSS file name. Please use .css as file extension. """

    def config(self, parent):
        super().config(parent)
        # Style
        if not self.style:
            self.style = 'modern-blue'
        if self.style not in VALID_STYLES:
            self.style = os.path.abspath(self.style)
            if not os.path.isfile(self.style):
                raise KiPlotConfigurationError('Missing style file `{}`'.format(self.style))


class BoMCSV(Optionable):
    """ CSV options """
    def __init__(self):
        super().__init__()
        with document:
            self.separator = ','
            """ *CSV Separator. TXT and TSV always use tab as delimiter.
                Only one character can be specified """
            self.hide_header = False
            """ Hide the header line (names of the columns) """
            self.hide_pcb_info = False
            """ Hide project information """
            self.hide_stats_info = False
            """ Hide statistics information """
            self.quote_all = False
            """ *Enclose all values using double quotes """

    def config(self, parent):
        super().config(parent)
        if self.separator:
            self.separator = self.separator.replace(r'\t', '\t')
            self.separator = self.separator.replace(r'\n', '\n')
            self.separator = self.separator.replace(r'\r', '\r')
            self.separator = self.separator.replace(r'\\', '\\')
        if len(self.separator) != 1:
            raise KiPlotConfigurationError('The CSV separator must be one character (`{}`)'.format(self.separator))


class BoMTXT(Optionable):
    """ HRTXT options """
    def __init__(self):
        super().__init__()
        with document:
            self.separator = 'I'
            """ *Column Separator """
            self.header_sep = '-'
            """ Separator between the header and the data """
            self.justify = 'left'
            """ [left,right,center] Text justification """
            self.hide_header = False
            """ Hide the header line (names of the columns) """
            self.hide_pcb_info = False
            """ Hide project information """
            self.hide_stats_info = False
            """ Hide statistics information """

    def config(self, parent):
        super().config(parent)
        if self.separator:
            self.separator = self.separator.replace(r'\t', '\t')
            self.separator = self.separator.replace(r'\n', '\n')
            self.separator = self.separator.replace(r'\r', '\r')
            self.separator = self.separator.replace(r'\\', '\\')


class BoMXLSX(BoMLinkable):
    """ XLSX options """
    def __init__(self):
        super().__init__()
        with document:
            self.max_col_width = 60
            """ [20,999] Maximum column width (characters) """
            self.style = 'modern-blue'
            """ Head style: modern-blue, modern-green, modern-red and classic """
            self.kicost = False
            """ *Enable KiCost worksheet creation.
                Note: an example of how to use it on CI/CD can be found [here](https://github.com/set-soft/kicost_ci_test) """
            self.kicost_api_enable = Optionable
            """ [string|list(string)=''] List of KiCost APIs to enable """
            self.kicost_api_disable = Optionable
            """ [string|list(string)=''] List of KiCost APIs to disable """
            self.kicost_dist_desc = False
            """ Used to add a column with the distributor's description. So you can check this is the right component """
            self.kicost_config = ''
            """ KiCost configuration file. It contains the keys for the different distributors APIs.
                The regular KiCost config is used when empty.
                Important for CI/CD environments: avoid exposing your API secrets!
                To understand how to achieve this, and also how to make use of the cache please visit the
                [kicost_ci_test](https://github.com/set-soft/kicost_ci_test) repo """
            self.specs = False
            """ *Enable Specs worksheet creation. Contains specifications for the components.
                Works with only some KiCost APIs """
            self.specs_columns = BoMColumns
            """ [list(dict)|list(string)] Which columns are included in the Specs worksheet. Use `References` for the
                references, 'Row' for the order and 'Sep' to separate groups at the same level. By default all are included.
                Column names are distributor specific, the following aren't: '_desc', '_value', '_tolerance', '_footprint',
                '_power', '_current', '_voltage', '_frequency', '_temp_coeff', '_manf', '_size' """
            self.logo_scale = 2
            """ Scaling factor for the logo. Note that this value isn't honored by all spreadsheet software """

    def process_columns_config(self, cols):
        if isinstance(cols, type):
            return (None, None, None, None, None)
        columns = []
        column_levels = []
        column_comments = []
        column_rename = {}
        join = []
        # Create the different lists
        for col in cols:
            if isinstance(col, str):
                # Just a string, add to the list of used
                new_col = col
                new_col_l = new_col.lower()
                level = 0
                comment = ''
                if new_col_l[0] == '_':
                    column_rename[new_col_l] = new_col_l[1:].capitalize()
            else:
                # A complete entry
                new_col = col.field
                new_col_l = new_col.lower()
                # A column rename
                if col.name:
                    column_rename[new_col_l] = col.name
                elif new_col_l[0] == '_':
                    column_rename[new_col_l] = new_col_l[1:].capitalize()
                # Attach other columns
                if col.join:
                    join.append(col.join)
                level = col.level
                comment = col.comment
            columns.append(new_col)
            column_levels.append(level)
            column_comments.append(comment)
        return (columns, column_levels, column_comments, column_rename, join)

    def config(self, parent):
        super().config(parent)
        # Style
        if not self.style:
            self.style = 'modern-blue'
        if self.style not in VALID_STYLES:
            raise KiPlotConfigurationError('Unknown style `{}`'.format(self.style))
        if self.kicost_config and not os.path.isfile(self.kicost_config):
            raise KiPlotConfigurationError('Missing KiCost configuration file `{}`'.format(self.kicost_config))
        if not self.kicost_config:
            self.kicost_config = None
        # KiCost APIs
        self.kicost_api_enable = Optionable.force_list(self.kicost_api_enable)
        self.kicost_api_disable = Optionable.force_list(self.kicost_api_disable)
        # Specs columns
        (self.s_columns, self.s_levels, self.s_comments, self.s_rename,
         self.s_join) = self.process_columns_config(self.specs_columns)


class ComponentAliases(Optionable):
    _default = DEFAULT_ALIASES

    def __init__(self):
        super().__init__()


class GroupFields(Optionable):
    _default = ColumnList.DEFAULT_GROUPING + ['voltage', 'tolerance', 'current', 'power']

    def __init__(self):
        super().__init__()


class NoConflict(Optionable):
    _default = "['Config', 'Part']"

    def __init__(self):
        super().__init__()


class Aggregate(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.file = ''
            """ Name of the schematic to aggregate """
            self.name = ''
            """ Name to identify this source. If empty we use the name of the schematic """
            self.ref_id = ''
            """ A prefix to add to all the references from this project """
            self.number = 1
            """ Number of boards to build (components multiplier). Use negative to subtract """
            self.delimiter = ','
            """ Delimiter used for CSV files """

    def config(self, parent):
        super().config(parent)
        if not self.file:
            raise KiPlotConfigurationError("Missing or empty `file` in aggregate list ({})".format(str(self._tree)))
        if not self.name:
            self.name = os.path.splitext(os.path.basename(self.file))[0]


class BoMOptions(BaseOptions):
    def __init__(self):
        with document:
            self.number = 1
            """ *Number of boards to build (components multiplier) """
            self.variant = ''
            """ Board variant, used to determine which components
                are output to the BoM. """
            self.output = GS.def_global_output
            """ *filename for the output (%i=bom)"""
            self.format = ''
            """ *[HTML,CSV,TXT,TSV,XML,XLSX,HRTXT] format for the BoM.
                Defaults to CSV or a guess according to the options.
                HRTXT stands for Human Readable TeXT """
            # Equivalent to KiBoM INI:
            self.ignore_dnf = True
            """ *Exclude DNF (Do Not Fit) components """
            self.fit_field = 'Config'
            """ Field name used for internal filters (not for variants) """
            self.use_alt = False
            """ Print grouped references in the alternate compressed style eg: R1-R7,R18 """
            self.columns = BoMColumns
            """ *[list(dict)|list(string)] List of columns to display.
                Can be just the name of the field.
                In addition to all user defined fields you have various special columns, consult :ref:`bom_columns` """
            self.cost_extra_columns = BoMColumns
            """ [list(dict)|list(string)] List of columns to add to the global section of the cost.
                Can be just the name of the field """
            self.normalize_values = False
            """ *Try to normalize the R, L and C values, producing uniform units and prefixes """
            self.normalize_locale = False
            """ When normalizing values use the locale decimal point """
            self.ref_separator = ' '
            """ Separator used for the list of references """
            self.html = BoMHTML
            """ *[dict] Options for the HTML format """
            self.xlsx = BoMXLSX
            """ *[dict] Options for the XLSX format """
            self.csv = BoMCSV
            """ *[dict] Options for the CSV, TXT and TSV formats """
            self.hrtxt = BoMTXT
            """ *[dict] Options for the HRTXT formats """
            # * Filters
            self.pre_transform = Optionable
            """ [string|list(string)='_none'] Name of the filter to transform fields before applying other filters.
                This option is for simple cases, consider using a full variant for complex cases """
            self.exclude_filter = Optionable
            """ [string|list(string)='_mechanical'] Name of the filter to exclude components from BoM processing.
                The default filter (built-in filter '_mechanical') excludes test points, fiducial marks, mounting holes, etc.
                Please consult the built-in filters explanation to fully understand what is excluded by default.
                This option is for simple cases, consider using a full variant for complex cases """
            self.dnf_filter = Optionable
            """ [string|list(string)='_kibom_dnf'] Name of the filter to mark components as 'Do Not Fit'.
                The default filter marks components with a DNF value or DNF in the Config field.
                This option is for simple cases, consider using a full variant for complex cases """
            self.dnc_filter = Optionable
            """ [string|list(string)='_kibom_dnc'] Name of the filter to mark components as 'Do Not Change'.
                The default filter marks components with a DNC value or DNC in the Config field.
                This option is for simple cases, consider using a full variant for complex cases """
            # * Grouping criteria
            self.group_connectors = True
            """ Connectors with the same footprints will be grouped together, independent of the name of the connector """
            self.merge_blank_fields = True
            """ Component groups with blank fields will be merged into the most compatible group, where possible """
            self.merge_both_blank = True
            """ When creating groups two components with empty/missing field will be interpreted as with the same value """
            self.group_fields = GroupFields
            """ *[list(string)] List of fields used for sorting individual components into groups.
                Components which match (comparing *all* fields) will be grouped together.
                Field names are case-insensitive.
                For empty fields the behavior is defined by the `group_fields_fallbacks`, `merge_blank_fields` and
                `merge_both_blank` options.
                Note that for resistors, capacitors and inductors the _Value_ field is parsed and qualifiers, like
                tolerance, are discarded. Please use a separated field and disable `merge_blank_fields` if this
                information is important. You can also disable `parse_value`.
                If empty: ['Part', 'Part Lib', 'Value', 'Footprint', 'Footprint Lib',
                .          'Voltage', 'Tolerance', 'Current', 'Power'] is used """
            self.group_fields_fallbacks = Optionable
            """ [list(string)] List of fields to be used when the fields in `group_fields` are empty.
                The first field in this list is the fallback for the first in `group_fields`, and so on """
            self.component_aliases = ComponentAliases
            """ [list(list(string))] A series of values which are considered to be equivalent for the part name.
                Each entry is a list of equivalen names. Example: ['c', 'c_small', 'cap' ]
                will ensure the equivalent capacitor symbols can be grouped together.
                If empty the following aliases are used:
                - ['r', 'r_small', 'res', 'resistor']
                - ['l', 'l_small', 'inductor']
                - ['c', 'c_small', 'cap', 'capacitor']
                - ['sw', 'switch']
                - ['zener', 'zenersmall']
                - ['d', 'diode', 'd_small'] """
            self.parse_value = True
            """ Parse the `Value` field so things like *1k* and *1000* are interpreted as equal.
                Note that this implies that *1k 1%* is the same as *1k 5%*. If you really need to group using the
                extra information split it in separated fields, add the fields to `group_fields` and disable
                `merge_blank_fields` """
            self.no_conflict = NoConflict
            """ [list(string)] List of fields where we tolerate conflicts.
                Use it to avoid undesired warnings.
                By default the field indicated in `fit_field`, the field used for variants and
                the field `part` are excluded """
            self.aggregate = Aggregate
            """ [list(dict)] Add components from other projects.
                You can use CSV files, the first row must contain the names of the fields.
                The `Reference` and `Value` are mandatory, in most cases `Part` is also needed.
                The `Part` column should contain the name/type of the component. This is important for
                passive components (R, L, C, etc.). If this information isn't available consider
                configuring the grouping to exclude the `Part`. """
            self.ref_id = ''
            """ A prefix to add to all the references from this project. Used for multiple projects """
            self.source_by_id = False
            """ Generate the `Source BoM` column using the reference ID instead of the project name """
            self.int_qtys = True
            """ Component quantities are always expressed as integers. Using the ceil() function """
            self.distributors = Optionable
            """ [string|list(string)] Include this distributors list. Default is all the available """
            self.no_distributors = Optionable
            """ [string|list(string)] Exclude this distributors list. They are removed after computing `distributors` """
            self.count_smd_tht = False
            """ Show the stats about how many of the components are SMD/THT. You must provide the PCB """
            self.units = 'millimeters'
            """ *[millimeters,inches,mils] Units used for the positions ('Footprint X' and 'Footprint Y' columns).
                Affected by global options """
            self.bottom_negative_x = False
            """ Use negative X coordinates for footprints on bottom layer (for XYRS) """
            self.use_aux_axis_as_origin = True
            """ Use the auxiliary axis as origin for coordinates (KiCad default) (for XYRS) """
            self.angle_positive = True
            """ Always use positive values for the footprint rotation """
            self.sort_style = 'type_value'
            """ *[type_value,type_value_ref,ref] Sorting criteria """
            self.footprint_populate_values = Optionable
            """ [string|list(string)='no,yes'] Values for the `Footprint Populate` column """
            self.footprint_type_values = Optionable
            """ [string|list(string)='SMD,THT,VIRTUAL'] Values for the `Footprint Type` column """
            self.expand_text_vars = True
            """ Expand KiCad 6 text variables after applying all filters and variants.
                This is done using a **_expand_text_vars** filter.
                If you need to customize the filter, or apply it before, you can disable this option and
                add a custom filter to the filter chain """
            self.exclude_marked_in_sch = True
            """ Exclude components marked with *Exclude from bill of materials* in the schematic.
                This is a KiCad 6 option """
            self.exclude_marked_in_pcb = False
            """ Exclude components marked with *Exclude from BOM* in the PCB.
                This is a KiCad 6 option """
        self._format_example = 'CSV'
        self._footprint_populate_values_example = 'no,yes'
        self._footprint_type_values_example = 'SMD,THT,VIRTUAL'
        super().__init__()

    @staticmethod
    def _get_columns():
        """ Create a list of valid columns """
        if GS.sch:
            cols = deepcopy(ColumnList.COLUMNS_DEFAULT)
            return (GS.sch.get_field_names(cols), ColumnList.COLUMNS_EXTRA)
        return (ColumnList.COLUMNS_DEFAULT, ColumnList.COLUMNS_EXTRA)

    def _guess_format(self):
        """ Figure out the format """
        if not self.format:
            # If we have HTML options generate an HTML
            if not isinstance(self.html, type):
                return 'html'
            # Same for XLSX
            if not isinstance(self.xlsx, type):
                return 'xlsx'
            # Same for HRTXT
            if not isinstance(self.hrtxt, type):
                return 'hrtxt'
            # Default to a simple and common format: CSV
            return 'csv'
        # Explicit selection
        return self.format.lower()

    def _normalize_variant(self):
        """ Replaces the name of the variant by an object handling it. """
        self.variant = RegOutput.check_variant(self.variant)
        if self.variant is None:
            # If no variant is specified use the KiBoM variant class with basic functionality
            self.variant = KiBoM()
            self.variant.config_field = self.fit_field
            self.variant.variant = []
            self.variant.name = 'default'
            # Delegate any filter to the variant
            self.variant.set_def_filters(self.exclude_filter, self.dnf_filter, self.dnc_filter, self.pre_transform)
            self.exclude_filter = self.dnf_filter = self.dnc_filter = self.pre_transform = None
            self.variant.config(self)  # Fill or adjust any detail

    def process_columns_config(self, cols, valid_columns, extra_columns, add_all=True):
        column_rename = {}
        join = []
        if isinstance(cols, type):
            if not add_all:
                return ([], [], [], column_rename, join)
            # If none specified make a list with all the possible columns.
            # Here are some exceptions:
            # Ignore the part and footprint library, also sheetpath and the Reference in singular
            ignore = [ColumnList.COL_PART_LIB_L, ColumnList.COL_FP_LIB_L, ColumnList.COL_SHEETPATH_L,
                      ColumnList.COL_REFERENCE_L[:-1]]
            if len(self.aggregate) == 0:
                ignore.append(ColumnList.COL_SOURCE_BOM_L)
                if self.number == 1:
                    # For one board avoid COL_GRP_BUILD_QUANTITY
                    ignore.append(ColumnList.COL_GRP_BUILD_QUANTITY_L)
            # Exclude the particular columns
            columns = [h for h in valid_columns if not h.lower() in ignore]
            column_levels = [0]*len(columns)
            column_comments = ['']*len(columns)
        else:
            columns = []
            column_levels = []
            column_comments = []
            # Ensure the column names are valid.
            # Also create the rename and join lists.
            # Lower case available columns (to check if valid)
            valid_columns_l = {c.lower(): c for c in valid_columns + extra_columns}
            logger.debug("Valid columns: {} ({})".format(valid_columns, len(valid_columns)))
            # Create the different lists
            for col in cols:
                if isinstance(col, str):
                    # Just a string, add to the list of used
                    new_col = col
                    new_col_l = new_col.lower()
                    level = 0
                    comment = ''
                else:
                    # A complete entry
                    new_col = col.field
                    new_col_l = new_col.lower()
                    # A column rename
                    if col.name:
                        column_rename[new_col_l] = col.name
                    # Attach other columns
                    if col.join:
                        join.append(col.join)
                    level = col.level
                    comment = col.comment
                # Check this is a valid column
                if new_col_l not in valid_columns_l:
                    # The Field_Rename filter can change this situation:
                    # raise KiPlotConfigurationError('Invalid column name `{}`'.format(new_col))
                    logger.warning(W_BADFIELD+'Invalid column name `{}`. Valid columns are {}.'.
                                   format(new_col, list(valid_columns_l.values())))
                columns.append(new_col)
                column_levels.append(level)
                column_comments.append(comment)
        return (columns, column_levels, column_comments, column_rename, join)

    def config(self, parent):
        super().config(parent)
        self.format = self._guess_format()
        self._expand_id = 'bom'
        self._expand_ext = 'txt' if self.format.lower() == 'hrtxt' else self.format.lower()
        # HTML options
        if self.format == 'html' and isinstance(self.html, type):
            # If no options get the defaults
            self.html = BoMHTML()
            self.html.config(self)
        # CSV options
        if self.format in ['csv', 'tsv', 'txt'] and isinstance(self.csv, type):
            # If no options get the defaults
            self.csv = BoMCSV()
            self.csv.config(self)
        # HRTXT options
        if self.format == 'hrtxt' and isinstance(self.hrtxt, type):
            # If no options get the defaults
            self.hrtxt = BoMTXT()
            self.hrtxt.config(self)
        # XLSX options
        if self.format == 'xlsx' and isinstance(self.xlsx, type):
            # If no options get the defaults
            self.xlsx = BoMXLSX()
            self.xlsx.config(self)
        # Do title %X and ${var} expansions on the BoMLinkable titles
        # Here because some variables needs our parent
        if self.format == 'html' and self.html.title:
            self.html.title = self.expand_filename_both(self.html.title, make_safe=False)
            self.html.extra_info = [self.expand_filename_both(t, make_safe=False) for t in self.html.extra_info]
        if self.format == 'xlsx' and self.xlsx.title:
            self.xlsx.title = self.expand_filename_both(self.xlsx.title, make_safe=False)
            self.xlsx.extra_info = [self.expand_filename_both(t, make_safe=False) for t in self.xlsx.extra_info]
        # group_fields
        if isinstance(self.group_fields, type):
            self.group_fields = GroupFields.get_default()
        else:
            # Make the grouping fields lowercase
            self.group_fields = [f.lower() for f in self.group_fields]
        # group_fields_fallbacks
        if isinstance(self.group_fields_fallbacks, type):
            self.group_fields_fallbacks = []
        else:
            # Make the grouping fields lowercase
            self.group_fields_fallbacks = [f.lower() for f in self.group_fields_fallbacks]
        # Fill with None if needed
        if len(self.group_fields_fallbacks) < len(self.group_fields):
            self.group_fields_fallbacks.extend([None]*(len(self.group_fields)-len(self.group_fields_fallbacks)))
        # component_aliases
        if isinstance(self.component_aliases, type):
            self.component_aliases = DEFAULT_ALIASES
        # Filters
        self.pre_transform = BaseFilter.solve_filter(self.pre_transform, 'pre_transform', is_transform=True)
        self.exclude_filter = BaseFilter.solve_filter(self.exclude_filter, 'exclude_filter')
        self.dnf_filter = BaseFilter.solve_filter(self.dnf_filter, 'dnf_filter')
        self.dnc_filter = BaseFilter.solve_filter(self.dnc_filter, 'dnc_filter')
        # Variants, make it an object
        self._normalize_variant()
        # Field names are handled in lowercase
        self.fit_field = self.fit_field.lower()
        # Fields excluded from conflict warnings
        no_conflict = set()
        if isinstance(self.no_conflict, type):
            no_conflict.add(self.fit_field)
            no_conflict.add('part')
            var_field = self.variant.get_variant_field()
            if var_field is not None:
                no_conflict.add(var_field)
        else:
            for field in self.no_conflict:
                no_conflict.add(field.lower())
        self.no_conflict = no_conflict
        # Make sure aggregate is a list
        if isinstance(self.aggregate, type):
            self.aggregate = []
        # List of distributors
        self.distributors = Optionable.force_list(self.distributors)
        self.no_distributors = Optionable.force_list(self.no_distributors)
        # Column values
        self.footprint_populate_values = Optionable.force_list(self.footprint_populate_values)
        if not self.footprint_populate_values:
            self.footprint_populate_values = ['no', 'yes']
        if len(self.footprint_populate_values) != 2:
            raise KiPlotConfigurationError("The `footprint_populate_values` must contain two values ({})".
                                           format(self.footprint_populate_values))
        self.footprint_type_values = Optionable.force_list(self.footprint_type_values)
        if not self.footprint_type_values:
            self.footprint_type_values = ['SMD', 'THT', 'VIRTUAL']
        if len(self.footprint_type_values) != 3:
            raise KiPlotConfigurationError("The `footprint_type_values` must contain three values ({})".
                                           format(self.footprint_type_values))
        # Columns
        (valid_columns, extra_columns) = self._get_columns()
        (self.columns, self.column_levels, self.column_comments, self.column_rename,
         self.join) = self.process_columns_config(self.columns, valid_columns, extra_columns)
        (self.columns_ce, self.column_levels_ce, self.column_comments_ce, self.column_rename_ce,
         self.join_ce) = self.process_columns_config(self.cost_extra_columns, valid_columns, extra_columns, add_all=False)

    def get_ref_index(self, header, fname):
        ref_n = ColumnList.COL_REFERENCE_L
        ref_index = None
        try:
            ref_index = header.index(ref_n)
        except ValueError:
            try:
                ref_index = header.index(ref_n[:-1])
            except ValueError:
                msg = 'Missing `{}` in aggregated file `{}`'.format(ref_n, fname)
                if GS.global_csv_accept_no_ref:
                    logger.warning(W_MISSREF+msg)
                else:
                    raise KiPlotConfigurationError(msg)
        return ref_index

    def load_csv(self, fname, project, delimiter):
        """ Load components from a CSV file """
        comps = []
        logger.debug('Importing components from `{}`'.format(fname))
        with open(fname) as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            header = [x.lower() for x in next(reader)]
            logger.debugl(1, '- CSV header {}'.format(header))
            # The header must contain at least the reference and the value
            ref_index = self.get_ref_index(header, fname)
            try:
                val_index = header.index(ColumnList.COL_VALUE_L)
            except ValueError:
                raise KiPlotConfigurationError('Missing `{}` in aggregated file `{}`'.format(ColumnList.COL_VALUE_L, fname))
            # Optional important fields:
            fp_index = None
            try:
                fp_index = header.index(ColumnList.COL_FP_L)
            except ValueError:
                pass
            ds_index = None
            try:
                ds_index = header.index(ColumnList.COL_DATASHEET_L)
            except ValueError:
                pass
            pn_index = None
            try:
                pn_index = header.index(ColumnList.COL_PART_L)
            except ValueError:
                logger.warning(W_NOPART+'No `Part` specified, using `Value` instead, this can impact the grouping')
            min_num = len(header)
            for r in reader:
                c = SchematicComponent()
                c.unit = 0
                c.project = project
                c.lib = ''
                c.ref = c.f_ref = c.ref_prefix = ''
                c.ref_suffix = '?'
                c.sheet_path_h = '/'+project
                for n, f in enumerate(r):
                    number = None
                    if n == ref_index:
                        c.ref = c.f_ref = str(f)
                        c.split_ref()
                        number = 0
                    elif n == val_index:
                        c.value = str(f)
                        if pn_index is None:
                            c.name = str(f)
                        number = 1
                    elif n == fp_index:
                        c.footprint = str(f)
                        number = 2
                    elif n == ds_index:
                        c.datasheet = str(f)
                        number = 3
                    elif n == pn_index:
                        c.name = str(f)
                        number = -1
                    fld = SchematicField()
                    fld.number = min_num+n if number is None else number
                    fld.value = str(f)
                    fld.name = header[n]
                    c.add_field(fld)
                comps.append(c)
                logger.debugl(2, '- Adding component {}'.format(c))
        comps.sort(key=lambda g: g.ref)
        return CompsFromCSV(fname, comps)

    def aggregate_comps(self, comps):
        self.qtys = {GS.sch_basename: self.number}
        for prj in self.aggregate:
            if not os.path.isfile(prj.file):
                raise KiPlotConfigurationError("Missing `{}`".format(prj.file))
            logger.debug('Adding components from project {} ({}) using reference id `{}`'.
                         format(prj.name, prj.file, prj.ref_id))
            self.qtys[prj.name] = prj.number
            ext = os.path.splitext(prj.file)[1]
            if ext == '.sch' or ext == '.kicad_sch':
                prj.sch = load_any_sch(prj.file, prj.name)
            else:
                prj.sch = self.load_csv(prj.file, prj.name, prj.delimiter)
            new_comps = expand_fields(prj.sch.get_components(), dont_copy=True)
            for c in new_comps:
                c.ref = prj.ref_id+c.ref
                c.ref_id = prj.ref_id
            comps.extend(new_comps)
            prj.source = os.path.basename(prj.file)

    def solve_logo(self):
        if self.format == 'html':
            logo = self.html.logo
            w = self.html.logo_width
        elif self.format == 'xlsx':
            logo = self.xlsx.logo
            w = self.xlsx.logo_width
        else:
            return None
        if not logo:
            return None
        ext = os.path.splitext(logo)[1]
        if ext.lower() != '.svg':
            return None
        png = GS.tmp_file(suffix='.png')
        cmd = [self.ensure_tool('RSVG'), '-w', str(w), '-f', 'png', '-o', png, logo]
        run_command(cmd)
        self._old_logo = logo
        if self.format == 'html':
            self.html.logo = png
        elif self.format == 'xlsx':
            self.xlsx.logo = png
        return png

    def run(self, output):
        format = self.format.lower()
        if format == 'xlsx':
            if self.xlsx.kicost:
                self.ensure_tool('KiCost')
            self.ensure_tool('XLSXWriter')
        # Add some info needed for the output to the config object.
        # So all the configuration is contained in one object.
        self.source = GS.sch_basename
        self.date = GS.sch_date
        self.revision = GS.sch_rev
        self.debug_level = GS.debug_level
        self.kicad_version = GS.kicad_version
        self.conv_units = GS.unit_name_to_scale_factor(self.units)
        # Get the components list from the schematic
        # We use a copy because we could expand the field values using ${VAR}
        comps = expand_fields(GS.sch.get_components())
        get_board_comps_data(comps)
        if self.count_smd_tht and not GS.pcb_file:
            logger.warning(W_NEEDSPCB+"`count_smd_tht` is enabled, but no PCB provided")
            self.count_smd_tht = False
        # Apply the reference prefix
        for c in comps:
            c.ref = self.ref_id+c.ref
            c.ref_id = self.ref_id
        # Aggregate components from other projects
        self.aggregate_comps(comps)
        # Apply all the filters
        reset_filters(comps)
        if self.exclude_marked_in_sch:
            for c in comps:
                if c.included:
                    c.included = c.in_bom
        if self.exclude_marked_in_pcb:
            for c in comps:
                if c.included:
                    c.included = c.in_bom_pcb
        comps = apply_pre_transform(comps, self.pre_transform)
        apply_exclude_filter(comps, self.exclude_filter)
        apply_fitted_filter(comps, self.dnf_filter)
        apply_fixed_filter(comps, self.dnc_filter)
        # Apply the variant
        comps = self.variant.filter(comps)
        # Now expand the text variables, the user can disable it and insert a customized filter
        # in the variant or even before.
        if self.expand_text_vars:
            comps = apply_pre_transform(comps, BaseFilter.solve_filter('_expand_text_vars', 'KiCad 6 text vars',
                                                                       is_transform=True))
        # We add the main project to the aggregate list so do_bom sees a complete list
        base_sch = Aggregate()
        base_sch.file = GS.sch_file
        base_sch.name = GS.sch_basename
        base_sch.ref_id = self.ref_id
        base_sch.number = self.number
        base_sch.sch = GS.sch
        self.aggregate.insert(0, base_sch)
        # To translate project to ID
        if self.source_by_id:
            self.source_to_id = {prj.name: prj.ref_id for prj in self.aggregate}
        tmp_png = self.solve_logo()
        try:
            do_bom(output, format, comps, self)
        except BoMError as e:
            raise KiPlotConfigurationError(str(e))
        finally:
            if tmp_png:
                os.remove(tmp_png)
                if self.format == 'html':
                    self.html.logo = self._old_logo
                elif self.format == 'xlsx':
                    self.xlsx.logo = self._old_logo
        # Undo the reference prefix
        if self.ref_id:
            l_id = len(self.ref_id)
            for c in filter(lambda c: c.project == GS.sch_basename, comps):
                c.ref = c.ref[l_id:]
                c.ref_id = ''

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]


@output_class
class BoM(BaseOutput):  # noqa: F821
    """ BoM (Bill of Materials)
        Used to generate the BoM in CSV, HTML, TSV, TXT, XML or XLSX format using the internal BoM.
        This output can generate XYRS files (pick and place files).
        Is compatible with KiBoM, but doesn't need to update the XML netlist because the components
        are loaded from the schematic.
        Important differences with KiBoM output:
        - All options are in the main `options` section, not in `conf` subsection.
        - The `Component` column is named `Row` and works just like any other column.
        This output is what you get from the 'Tools/Generate Bill of Materials' menu in eeschema. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = BoMOptions
            """ *[dict] Options for the `bom` output """
        self._sch_related = True
        self._category = 'Schematic/BoM'

    @staticmethod
    def create_bom(fmt, subd, group_fields, join_fields, fld_names, cols=None):
        gb = {}
        gb['name'] = subd.lower()+'_bom_'+fmt.lower()
        gb['comment'] = '{} Bill of Materials in {} format'.format(subd, fmt)
        gb['type'] = 'bom'
        gb['dir'] = os.path.join('BoM', subd)
        ops = {'format': fmt}
        if fmt == 'HRTXT':
            ops['hrtxt'] = {'separator': '|'}
        if group_fields:
            ops['group_fields'] = group_fields
        if join_fields:
            columns = []
            for c in fld_names:
                if c.lower() == 'value':
                    columns.append({'field': c, 'join': list(join_fields)})
                else:
                    columns.append(c)
            ops['columns'] = columns
        if cols:
            ops['columns'] = cols
        if GS.board:
            ops['count_smd_tht'] = True
        gb['options'] = ops
        return gb

    @staticmethod
    def process_templates(mpn_fields, dists):
        # Rename MPN for something we have, or just remove it
        if mpn_fields:
            defs = {'_KIBOT_MPN_FIELD': '- field: manf#'}
        elif dists:
            defs = {'_KIBOT_MPN_FIELD': '- field: '+list(dists)[0]+'#'}
        else:
            defs = {'_KIBOT_MPN_FIELD': ''}
        register_xmp_import('MacroFab_XYRS', defs)

    @staticmethod
    def get_conf_examples(name, layers):
        outs = []
        # Make a list of available fields
        fld_names, extra_names = BoMOptions._get_columns()
        fld_names_l = [f.lower() for f in fld_names]
        fld_set = set(fld_names_l)
        logger.debug(' - Available fields {}'.format(fld_names_l))
        # Look for the manufacturer part number
        mpn_set = {k for k, v in KICOST_NAME_TRANSLATIONS.items() if v == 'manf#'}
        mpn_set.add('manf#')
        mpn_fields = fld_set.intersection(mpn_set)
        # Look for distributor part number
        dpn_set = set()
        for stub in DISTRIBUTORS_STUBS:
            for dist in DISTRIBUTORS:
                dpn_set.add(dist+stub)
                if stub != '#':
                    for sep in DISTRIBUTORS_STUBS_SEPS:
                        dpn_set.add(dist+sep+stub)
        dpn_fields = fld_set.intersection(dpn_set)
        # Collect the used distributors
        dists = set()
        for dist in DISTRIBUTORS:
            for fld in dpn_fields:
                if dist in fld:
                    dists.add(dist)
                    break
        # Add it to the group_fields
        xpn_fields = mpn_fields | dpn_fields
        group_fields = None
        if xpn_fields:
            group_fields = GroupFields.get_default().copy()
            group_fields.extend(list(xpn_fields))
            logger.debug(' - Adding grouping fields {}'.format(xpn_fields))
        # Look for fields to join to the value
        joinable_set = {'tolerance', 'voltage', 'power', 'current'}
        join_fields = fld_set.intersection(joinable_set)
        if join_fields:
            logger.debug(' - Fields to join with Value: {}'.format(join_fields))
        # Create a generic version
        SIMP_FMT = ['HTML', 'CSV', 'HRTXT', 'TSV', 'XML']
        XYRS_FMT = ['HTML']
        if GS.check_tool(name, 'XLSXWriter') is not None:
            SIMP_FMT.append('XLSX')
            XYRS_FMT.append('XLSX')
        for fmt in SIMP_FMT:
            outs.append(BoM.create_bom(fmt, 'Generic', group_fields, join_fields, fld_names))
        if GS.board:
            # Create an example showing the positional fields
            cols = ColumnList.COLUMNS_DEFAULT + ColumnList.COLUMNS_EXTRA
            for fmt in XYRS_FMT:
                gb = BoM.create_bom(fmt, 'Positional', group_fields, None, fld_names, cols)
                gb['options'][fmt.lower()] = {'style': 'modern-red'}
                outs.append(gb)
        # Create a costs version
        if GS.check_tool(name, 'KiCost') is not None:  # and dists?
            logger.debug(' - KiCost distributors {}'.format(dists))
            grp = group_fields
            if group_fields:
                # We will apply KiCost rename rules, so we must use their names
                grp = GroupFields.get_default().copy()
                if mpn_fields:
                    grp.append('manf#')
                for d in dists:
                    grp.append(d+'#')
            gb = BoM.create_bom('XLSX', 'Costs', grp, join_fields, fld_names)
            gb['options']['xlsx'] = {'style': 'modern-green', 'kicost': True, 'specs': True}
            # KitSpace seems to be failing all the time
            gb['options']['xlsx']['kicost_api_disable'] = 'KitSpace'
            gb['options']['pre_transform'] = '_kicost_rename'
            # gb['options']['distributors'] = list(dists)
            outs.append(gb)
        # Add the list of layers to the templates
        BoM.process_templates(mpn_fields, dists)
        return outs
