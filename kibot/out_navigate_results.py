# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# The Assembly image is a composition from Pixlok and oNline Web Fonts
# The rest are KiCad icons
"""
Dependencies:
  - from: RSVG
    role: Create outputs preview
    id: rsvg1
  - from: RSVG
    role: Create PNG icons
    id: rsvg2
  - from: Ghostscript
    role: Create outputs preview
  - from: ImageMagick
    role: Create outputs preview
  - from: Git
    role: Find origin url
"""
import base64
import os
import subprocess
import pprint
from shutil import copy2
from math import ceil
from .bom.kibot_logo import KIBOT_LOGO, KIBOT_LOGO_W, KIBOT_LOGO_H
from .error import KiPlotConfigurationError
from .gs import GS
from .optionable import Optionable, BaseOptions
from .kiplot import config_output, get_output_dir, run_command
from .misc import W_NOTYET, W_MISSTOOL, W_NOOUTPUTS, read_png, force_list
from .pre_base import BasePreFlight
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log, __version__

logger = log.get_logger()
CAT_IMAGE = {'PCB': 'pcbnew',
             'Schematic': 'eeschema',
             'Compress': 'zip',
             'fabrication': 'fabrication',
             'export': 'export',
             'assembly': 'assembly_simple',
             'repair': 'repair',
             'docs': 'project',
             'BoM': 'bom',
             '3D': '3d',
             'gerber': 'gerber',
             'drill': 'load_drill',
             'Auxiliar': 'repair'}
EXT_IMAGE = {'gbr': 'file_gbr',
             'gtl': 'file_gbr',
             'gtp': 'file_gbr',
             'gbo': 'file_gbr',
             'gto': 'file_gbr',
             'gbs': 'file_gbr',
             'gbl': 'file_gbr',
             'gts': 'file_gbr',
             'gml': 'file_gbr',
             'gm1': 'file_gbr',
             'gbrjob': 'file_gerber_job',
             'brd': 'file_brd',
             'bz2': 'file_bz2',
             'dxf': 'file_dxf',
             'cad': 'file_cad',
             'drl': 'file_drl',
             'pdf': 'file_pdf',
             'txt': 'file_txt',
             'pos': 'file_pos',
             'csv': 'file_csv',
             'svg': 'file_svg',
             'eps': 'file_eps',
             'png': 'file_png',
             'jpg': 'file_jpg',
             'plt': 'file_plt',
             'ps': 'file_ps',
             'rar': 'file_rar',
             'scad': 'file_scad',
             'stl': 'file_stl',
             'step': 'file_stp',
             'stp': 'file_stp',
             'wrl': 'file_wrl',
             'html': 'file_html',
             'css': 'file_css',
             'xml': 'file_xml',
             'tsv': 'file_tsv',
             'xlsx': 'file_xlsx',
             'xyrs': 'file_xyrs',
             'xz': 'file_xz',
             'gz': 'file_gz',
             'tar': 'file_tar',
             'zip': 'file_zip',
             'kicad_pcb': 'pcbnew',
             'sch': 'eeschema',
             'kicad_sch': 'eeschema',
             'blend': 'file_blend',
             'pcb3d': 'file_pcb3d',
             'json': 'file_json'}
for i in range(31):
    n = str(i)
    EXT_IMAGE['gl'+n] = 'file_gbr'
    EXT_IMAGE['g'+n] = 'file_gbr'
    EXT_IMAGE['gp'+n] = 'file_gbr'
CAT_REP = {'PCB': ['pdf_pcb_print', 'svg_pcb_print', 'pcb_print'],
           'Schematic': ['pdf_sch_print', 'svg_sch_print']}
BIG_ICON = 256
MID_ICON = 64
OUT_COLS = 12
BIG_2_MID_REL = int(ceil(BIG_ICON/MID_ICON))
IMAGEABLES_SIMPLE = {'png', 'jpg'}
IMAGEABLES_GS = {'pdf', 'eps', 'ps'}
IMAGEABLES_SVG = {'svg'}
TITLE_HEIGHT = 30
STYLE = """
.cat-table { margin-left: auto; margin-right: auto; }
.cat-table td { padding: 20px 24px; }
.nav-table { margin-left: auto; margin-right: auto; }
.nav-table td { padding: 20px 24px; }
.output-table {
  width: 1280px;
  margin-left: auto;
  margin-right: auto;
  border-collapse:
  collapse;
  margin-top: 5px;
  margin-bottom: 4em;
  font-size: 0.9em;
  font-family: sans-serif;
  min-width: 400px;
  border-radius: 5px 5px 0 0;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
}
.output-table thead tr { background-color: #0e4e8e; color: #ffffff; text-align: left; }
.output-table th { padding: 10px 12px; }
.output-table td { padding: 5px 7px; }
.out-cell { width: 128px; text-align: center }
.out-img { text-align: center; margin-left: auto; margin-right: auto; }
.cat-img { text-align: center; margin-left: auto; margin-right: auto; }
.td-small { text-align: center; font-size: 0.6em; }
.td-normal { text-align: center; }
.generator { text-align: right; font-size: 0.6em; }
a:link, a:visited { text-decoration: none;}
a:hover, a:active { text-decoration: underline;}
/* The side navigation menu */
.sidenav {
  height: 100%; /* 100% Full-height */
  width: 0; /* 0 width - change this with JavaScript */
  position: fixed; /* Stay in place */
  z-index: 1; /* Stay on top */
  top: 0; /* Stay at the top */
  left: 0;
  background-color: #0e4e8e; /* Black*/
  overflow-x: hidden; /* Disable horizontal scroll */
  padding-top: 60px; /* Place content 60px from the top */
  transition: 0.5s; /* 0.5 second transition effect to slide in the sidenav */
}
/* The navigation menu links */
.sidenav a {
  padding: 8px 8px 8px 8px;
  text-decoration: none;
  font-size: 16px;
  color: #f1f1f1;
  display: block;
  transition: 0.3s;
}
/* When you mouse over the navigation links, change their color */
.sidenav a:hover {
  color: #ff0000;
}
/* Position and style the close button (top right corner) */
.sidenav .closebtn {
  position: absolute;
  top: 0;
  right: 8px;
  font-size: 36px;
  margin-left: 50px;
}
/* Style page content - use this if you want to push the page content to the right when you open the side navigation */
#main {
  transition: margin-left .5s;
  padding: 20px;
  margin-top: @TOP_MAR@px;
}
/* On smaller screens, where height is less than 450px, change the style of the sidenav (less padding and a smaller font
   size) */
@media screen and (max-height: 450px) {
  .sidenav {padding-top: 15px;}
  .sidenav a {font-size: 18px;}
}
ul {
  display: block;
  list-style-type: none;
  margin-block: -1em 0px;
  margin-inline: 0px 0px;
  padding-inline-start: 10px;
}
ul li {
  margin-block: 0px -1em;
}
.topmenu {
  overflow: hidden;
  position: fixed; /* Set the navbar to fixed position */
  top: 0; /* Position the navbar at the top of the page */
  width: 100%; /* Full width */
  background-color: white; /* Otherwise is transparent and overlaps */
}
"""
SCRIPT = """
<script>
function openNav() {
  document.getElementById("theSideNav").style.width = "360px";
  document.getElementById("main").style.marginLeft = "360px";
  document.getElementById("theTopMenu").style.marginLeft = "360px";
  document.getElementById("bmenu").style.display = "none";
}

function closeNav() {
  document.getElementById("theSideNav").style.width = "0";
  document.getElementById("main").style.marginLeft= "0";
  document.getElementById("theTopMenu").style.marginLeft = "0";
  document.getElementById("bmenu").style.display = "block";
}

function ScrollUp() {
  /* When we come here from the navbar we must scroll to avoid the top menu */
  var p = document.getElementById("main");
  var style = p.currentStyle || window.getComputedStyle(p);
  var m_top = parseInt(style.marginTop)

  window.scrollBy(0, -(m_top + 5));
}

window.onload = ScrollUp;
</script>
"""


def _run_command(cmd):
    logger.debug('- Executing: '+GS.pasteable_cmd(cmd))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if e.output:
            logger.debug('Output from command: '+e.output.decode())
        logger.non_critical_error(f'Failed to run {cmd[0]}, error {e.returncode}')
        return False
    if cmd_output.strip():
        logger.debug('- Output from command:\n'+cmd_output.decode())
    return True


class Navigate_ResultsOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=html, %x=navigate) """
            self.link_from_root = ''
            """ *The name of a file to create at the main output directory linking to the home page """
            self.skip_not_run = False
            """ Skip outputs with `run_by_default: false` """
            self.logo = Optionable
            """ [string|boolean=''] PNG file to use as logo, use false to remove.
                The KiBot logo is used by default """
            self.logo_url = 'https://github.com/INTI-CMNB/KiBot/'
            """ Target link when clicking the logo """
            self.title = ''
            """ Title for the page, when empty KiBot will try using the schematic or PCB title.
                If they are empty the name of the project, schematic or PCB file is used.
                You can use %X values and KiCad variables here """
            self.title_url = Optionable
            """ [string|boolean=''] Target link when clicking the title, use false to remove.
                KiBot will try with the origin of the current git repo when empty """
            self.nav_bar = True
            """ Add a side navigation bar to quickly access to the outputs """
            self.header = True
            """ Add a header containing information for the project """
        super().__init__()
        self._expand_id = 'navigate'
        self._expand_ext = 'html'

    def config(self, parent):
        super().config(parent)
        # Logo
        if isinstance(self.logo, bool):
            self.logo = '' if self.logo else None
        elif self.logo:
            self.logo = os.path.abspath(self.logo)
            if not os.path.isfile(self.logo):
                raise KiPlotConfigurationError('Missing logo file `{}`'.format(self.logo))
            try:
                self._logo_data, self._logo_w, self._logo_h, _ = read_png(self.logo, logger)
            except TypeError as e:
                raise KiPlotConfigurationError(f'Only PNG images are supported for the logo ({e})')
        if self.logo == '':
            # Internal logo
            self._logo_w = int(KIBOT_LOGO_W/2)
            self._logo_h = int(KIBOT_LOGO_H/2)
            self._logo_data = base64.b64decode(KIBOT_LOGO)
        elif self.logo is None:
            self._logo_w = self._logo_h = 0
            self._logo_data = ''
        # Title URL
        if isinstance(self.title_url, bool):
            self.title_url = '' if self.title_url else None

    def add_to_tree(self, cat, out, o_tree):
        # Add `out` to `o_tree` in the `cat` category
        cat = cat.split('/')
        node = o_tree
        for c in cat:
            if c not in node:
                # New one
                node[c] = {}
            node = node[c]
        node[out.name] = out

    def svg_to_png(self, svg_file, png_file, width):
        cmd = [self.rsvg_command, '-w', str(width), '-f', 'png', '-o', png_file, svg_file]
        return _run_command(cmd)

    def copy(self, img, width):
        """ Copy an SVG icon to the images/ dir.
            Tries to convert it to PNG. """
        img_w = "{}_{}".format(os.path.basename(img), width)
        if img_w in self.copied_images:
            # Already copied, just return its name
            return self.copied_images[img_w]
        src = os.path.join(self.img_src_dir, img+'.svg') if not img.endswith('.svg') else img
        dst = os.path.join(self.out_dir, 'images', img_w)
        id = img_w
        if self.rsvg_command is not None and self.svg_to_png(src, dst+'.png', width):
            img_w += '.png'
        else:
            copy2(src, dst+'.svg')
            img_w += '.svg'
        name = os.path.join('images', img_w)
        self.copied_images[id] = name
        return name

    def can_be_converted(self, ext):
        if ext in IMAGEABLES_SVG and self.rsvg_command is None:
            logger.warning(W_MISSTOOL+"Missing SVG to PNG converter")
            return False
        if ext in IMAGEABLES_GS and not self.ps2img_avail:
            logger.warning(W_MISSTOOL+"Missing PS/PDF to PNG converter")
            return False
        if ext in IMAGEABLES_SIMPLE and self.convert_command is None:
            logger.warning(W_MISSTOOL+"Missing ImageMagick converter")
            return False
        return ext in IMAGEABLES_SVG or ext in IMAGEABLES_GS or ext in IMAGEABLES_SIMPLE

    def get_image_for_cat(self, cat):
        img = None
        # Check if we have an output that can represent this category
        if cat in CAT_REP and self.convert_command is not None:
            outs_rep = CAT_REP[cat]
            rep_file = None
            # Look in all outputs
            for o in RegOutput.get_outputs():
                # Is this one that can be used to represent it?
                if o.type in outs_rep:
                    out_dir = get_output_dir(o.dir, o, dry=True)
                    targets = o.get_targets(out_dir)
                    # Look the output targets
                    for tg in targets:
                        ext = os.path.splitext(tg)[1][1:].lower()
                        # Can be converted to an image?
                        if os.path.isfile(tg) and self.can_be_converted(ext):
                            rep_file = tg
                            break
                    if rep_file:
                        break
            if rep_file:
                cat, _ = self.get_image_for_file(rep_file, cat, no_icon=True)
                return cat
        if cat in CAT_IMAGE:
            img = self.copy(CAT_IMAGE[cat], BIG_ICON)
            cat_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, cat, BIG_ICON, BIG_ICON)
            cat = ('<table class="cat-img"><tr><td>{}<br>{}</td></tr></table>'.
                   format(cat_img, cat))
        return cat

    def compose_image(self, file, ext, img, out_name, no_icon=False):
        if not os.path.isfile(file):
            logger.warning(W_NOTYET+"{} not yet generated, using an icon".format(os.path.relpath(file)))
            return False, None, None
        if self.convert_command is None:
            return False, None, None
        # Create a unique name using the output name and the generated file name
        bfname = os.path.splitext(os.path.basename(file))[0]
        fname = os.path.join(self.out_dir, 'images', out_name+'_'+bfname+'.png')
        # Full path for the icon image
        icon = os.path.join(self.out_dir, img)
        if ext == 'pdf':
            # Only page 1
            file += '[0]'
        if ext == 'svg':
            tmp_name = GS.tmp_file(suffix='.png')
            logger.debug('Temporal convert: {} -> {}'.format(file, tmp_name))
            if not self.svg_to_png(file, tmp_name, BIG_ICON):
                return False, None, None
            file = tmp_name
        cmd = [self.convert_command, file,
               # Size for the big icons (width)
               '-resize', str(BIG_ICON)+'x']
        if ext == 'ps':
            # ImageMagick 6.9.11 (and also the one in Debian 11) rotates the PS
            cmd.extend(['-rotate', '90'])
        if not no_icon:
            cmd.extend([  # Add the file type icon
                        icon,
                        # At the bottom right
                        '-gravity', 'south-east',
                        # This is a composition, not 2 images
                        '-composite'])
        cmd.append(fname)
        res = _run_command(cmd)
        if ext == 'svg':
            logger.debug('Removing temporal {}'.format(tmp_name))
            os.remove(tmp_name)
        return res, fname, os.path.relpath(fname, start=self.out_dir)

    def get_image_for_file(self, file, out_name, no_icon=False, image=None):
        ext = os.path.splitext(file)[1][1:].lower()
        wide = False
        # Copy the icon for this file extension
        icon_name = 'folder' if os.path.isdir(file) else EXT_IMAGE.get(ext, 'unknown')
        img = self.copy(image or icon_name, MID_ICON)
        # Full name for the file
        file_full = file
        # Just the file, to display it
        file = os.path.basename(file)
        # The icon size
        height = width = MID_ICON
        # Check if this file can be represented by an image
        if self.can_be_converted(ext):
            # Try to compose the image of the file with the icon
            ok, fimg, new_img = self.compose_image(file_full, ext, img, 'cat_'+out_name, no_icon)
            if ok:
                # It was converted, replace the icon by the composited image
                img = new_img
                # Compute its size
                try:
                    _, width, height, _ = read_png(fimg, logger)
                except TypeError:
                    width = height = 0
                # We are using the big size
                wide = True
        # Now add the image with its file name as caption
        ext_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, file, width, height)
        file = ('<table class="out-img"><tr><td>{}</td></tr><tr><td class="{}">{}</td></tr></table>'.
                format(ext_img, 'td-normal' if no_icon else 'td-small', out_name if no_icon else file))
        return file, wide

    def add_back_home(self, f, prev):
        if prev is not None:
            prev += '.html'
            f.write('<table class="nav-table">')
            f.write(' <tr>')
            f.write('  <td><a href="{}"><img src="{}" width="{}" height="{}" alt="go back"></a></td>'.
                    format(prev, self.back_img, MID_ICON, MID_ICON))
            f.write('  <td><a href="{}"><img src="{}" width="{}" height="{}" alt="go home"></a></td>'.
                    format(self.home, self.home_img, MID_ICON, MID_ICON))
            f.write(' </tr>')
            f.write('</table>')
        f.write('<p class="generator">Generated by <a href="https://github.com/INTI-CMNB/KiBot/">KiBot</a> v{}</p>\n'.
                format(__version__))
        f.write('</div>\n')
        if self.nav_bar:
            f.write(SCRIPT)

    def write_head(self, f, title):
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('<head>\n')
        f.write(' <title>{}</title>\n'.format(title if title else 'Main page'))
        f.write(' <meta charset="UTF-8">\n')  # UTF-8 encoding for unicode support
        f.write(' <link rel="stylesheet" href="styles.css">\n')
        f.write(' <link rel="icon" href="favicon.ico">\n')
        f.write('</head>\n')
        f.write('<body>\n')
        f.write(self.navbar)
        f.write(self.top_menu)
        f.write('<div id="main">\n')

    def generate_cat_page_for(self, name, node, prev, category):
        logger.debug('- Categories: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            # Limit to 5 categories by row
            c_cats = len(node)
            rows = ceil(c_cats/5.0)
            by_row = c_cats/rows
            acc = 0
            f.write('<table class="cat-table">\n<tr>\n')
            for cat, content in node.items():
                if not isinstance(content, dict):
                    continue
                if acc >= by_row:
                    # Flush the table and create another
                    acc = 0
                    f.write('</tr>\n</table>\n<table class="cat-table">\n<tr>\n')
                pname = name+'_'+cat+ext
                self.generate_page_for(content, pname, name, category+'/'+cat)
                f.write(' <td><a href="{}">{}</a></td>\n'.format(pname, self.get_image_for_cat(cat)))
                acc += 1
            f.write('</tr>\n</table>\n')
            self.generate_outputs(f, node)
            self.add_back_home(f, prev)
            f.write('</body>\n</html>\n')

    def generate_outputs(self, f, node):
        for oname, out in node.items():
            if isinstance(out, dict):
                continue
            f.write(f'<table id="{oname}" class="output-table">\n')
            out_name = oname.replace(' ', '_')
            oname = oname.replace('_', ' ')
            oname = oname[0].upper()+oname[1:]
            if out.comment:
                oname += ': '+out.comment
            f.write('<thead><tr><th colspan="{}">{}</th></tr></thead>\n'.format(OUT_COLS, oname))
            out_dir = get_output_dir(out.dir, out, dry=True)
            f.write('<tbody><tr>\n')
            targets, icons = out.get_navigate_targets(out_dir)
            c_targets = len(targets)
            # Make the icons a list with same len as targets
            if icons is None:
                icons = [None]*c_targets
            else:
                c_icons = len(icons)
                if c_icons < c_targets:
                    icons.extend([None]*(c_targets-c_icons))
            if len(targets) == 1:
                tg_rel = os.path.relpath(os.path.abspath(targets[0]), start=self.out_dir)
                img, _ = self.get_image_for_file(targets[0], out_name, image=icons[0] if icons else None)
                f.write('<td class="out-cell" colspan="{}"><a href="{}">{}</a></td>\n'.
                        format(OUT_COLS, tg_rel, img))
            else:
                c = 0
                for tg, icon in zip(targets, icons):
                    if c == OUT_COLS:
                        f.write('</tr>\n<tr>\n')
                        c = 0
                    tg_rel = os.path.relpath(os.path.abspath(tg), start=self.out_dir)
                    img, wide = self.get_image_for_file(tg, out_name, image=icon)
                    # Check if we need to break this row
                    span = 1
                    if wide:
                        span = BIG_2_MID_REL
                        remain = OUT_COLS-c
                        if span > remain:
                            f.write('<td class="out-cell" colspan="{}"></td></tr>\n<tr>\n'.format(remain))
                    # Add a new cell
                    f.write('<td class="out-cell" colspan="{}"><a href="{}">{}</a></td>\n'.format(span, tg_rel, img))
                    c = c+span
                if c < OUT_COLS:
                    f.write('<td class="out-cell" colspan="{}"></td>\n'.format(OUT_COLS-c))
            f.write('</tr>\n')
            # This row is just to ensure we have at least 1 cell in each column
            f.write('<tr>\n')
            for _ in range(OUT_COLS):
                f.write('<td></td>\n')
            f.write('</tr>\n')
            f.write('</tbody>\n')
            f.write('</table>\n')

    def generate_end_page_for(self, name, node, prev, category):
        logger.debug('- Outputs: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            self.generate_outputs(f, node)
            self.add_back_home(f, prev)
            f.write('</body>\n</html>\n')

    def generate_page_for(self, node, name, prev=None, category=''):
        logger.debug('Generating page for '+name)
        if isinstance(list(node.values())[0], dict):
            self.generate_cat_page_for(name, node, prev, category)
        else:
            self.generate_end_page_for(name, node, prev, category)

    def get_targets(self, out_dir):
        # Listing all targets is too complex, we list the most relevant
        # This is good enough to compress the result
        name = self._parent.expand_filename(out_dir, self.output)
        files = [os.path.join(out_dir, 'images'),
                 os.path.join(out_dir, 'styles.css'),
                 os.path.join(out_dir, 'favicon.ico')]
        if self.link_from_root:
            files.append(os.path.join(GS.out_dir, self.link_from_root))
        self.out_dir = out_dir
        self.get_html_names(self.create_tree(), name, files)
        return files

    def get_html_names_cat(self, name, node, prev, category, files):
        files.append(os.path.join(self.out_dir, name))
        name, ext = os.path.splitext(name)
        for cat, content in node.items():
            if not isinstance(content, dict):
                continue
            pname = name+'_'+cat+ext
            self.get_html_names(content, pname, files, name, category+'/'+cat)

    def get_html_names(self, node, name, files, prev=None, category=''):
        if isinstance(list(node.values())[0], dict):
            self.get_html_names_cat(name, node, prev, category, files)
        else:
            files.append(os.path.join(self.out_dir, name))

    def create_tree(self):
        o_tree = {}
        BasePreFlight.configure_all()
        for n in BasePreFlight.get_in_use_names():
            pre = BasePreFlight.get_preflight(n)
            cat = force_list(pre.get_category())
            if not cat:
                continue
            for c in cat:
                self.add_to_tree(c, pre, o_tree)
        for o in RegOutput.get_outputs():
            if not o.run_by_default and self.skip_not_run:
                # Skip outputs that aren't generated in a regular run
                continue
            config_output(o)
            cat = o.category
            if cat is None:
                continue
            for c in cat:
                self.add_to_tree(c, o, o_tree)
        return o_tree

    def generate_navbar_one(self, node, lvl, name, ext):
        """ Recursively create a menu containing all outputs.
            Using ul and li items """
        indent = ' '+' '*lvl
        code = indent+'<ul>\n'
        indent += ' '
        for k, v in node.items():
            if isinstance(v, dict):
                new_name = name+'_'+k
                code += indent+f'<li><a href="{new_name}{ext}">{k}</a></li>\n'
                code += self.generate_navbar_one(v, lvl+1, new_name, ext)
            else:
                code += indent+f'<li><a href="{name}{ext}#{v.name}">{v.name}</a></li>\n'
        code += indent[:-1]+'</ul>\n'
        return code

    def generate_navbar(self, node, name):
        name, ext = os.path.splitext(name)
        code = '<div id="theSideNav" class="sidenav">\n'
        code += '<a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>\n'
        code += self.generate_navbar_one(node, 0, name, ext)
        code += '</div>\n'
        return code

    def generate_top_menu(self):
        # Div for the top info
        fsize = f'{TITLE_HEIGHT}px'
        code = '<div id="theTopMenu" class="topmenu">\n'
        code += ' <table style="width:100%">\n'
        code += '  <tr>\n'
        code += '   <td valign="top" align="left">\n'
        if self.nav_bar:
            code += f'    <span id="bmenu" style="font-size:{fsize};cursor:pointer" onclick="openNav()">&#9776;</span>\n'
        code += '   </td>\n'
        code += '   <td>\n'
        if self.logo is not None and self.header:
            img_name = os.path.join('images', 'logo.png')
            if self.logo_url:
                code += f'     <a href="{self.logo_url}">\n'
            code += '     <img src="'+img_name+'" alt="Logo" width="'+str(self._logo_w)+'" height="'+str(self._logo_h)+'">\n'
            if self.logo_url:
                code += '     </a>\n'
        code += '   </td>\n'
        code += '   <td>\n'
        if self.header:
            if self.title_url:
                code += f'     <a href="{self.title_url}">\n'
            code += f'     <span style="font-size:{fsize};">{self._solved_title}</span>\n'
            if self.title_url:
                code += '     </a>\n'
        code += '   </td>\n'
        code += '  </tr>\n'
        code += ' </table>\n'
        code += '</div>\n'
        return code

    def solve_title(self):
        base_title = None
        if GS.sch:
            base_title = GS.sch.get_title()
        if GS.board and not base_title:
            tb = GS.board.GetTitleBlock()
            base_title = tb.GetTitle()
        if not base_title:
            base_title = GS.pro_basename or GS.sch_basename or GS.pcb_basename or 'Unknown'
        text = self.expand_filename_sch(self.title if self.title else '+')
        if text[0] == '+':
            text = base_title+text[1:]
        self._solved_title = text
        # Now the URL
        if self.title_url is not None and not self.title_url:
            # Empty but not None
            self._git_command = self.check_tool('Git')
            if self._git_command:
                res = ''
                try:
                    res = run_command([self._git_command, 'remote', 'get-url', 'origin'], just_raise=True)
                except subprocess.CalledProcessError:
                    pass
                if res:
                    self.title_url = res

    def run(self, name):
        self.out_dir = os.path.dirname(name)
        self.img_src_dir = GS.get_resource_path('images')
        self.img_dst_dir = os.path.join(self.out_dir, 'images')
        os.makedirs(self.img_dst_dir, exist_ok=True)
        self.copied_images = {}
        name = os.path.basename(name)
        # Create a tree with all the outputs
        o_tree = self.create_tree()
        logger.debug('Collected outputs:\n'+pprint.pformat(o_tree))
        if not o_tree:
            logger.warning(W_NOOUTPUTS+'No outputs for navigate results')
            return
        with open(os.path.join(self.out_dir, 'styles.css'), 'wt') as f:
            if not self.header:
                top_margin = 0 if not self.nav_bar else TITLE_HEIGHT
            else:
                top_margin = str(max(self._logo_h, TITLE_HEIGHT))
            f.write(STYLE.replace('@TOP_MAR@', str(top_margin)))
        self.rsvg_command = self.check_tool('rsvg1')
        self.convert_command = self.check_tool('ImageMagick')
        self.ps2img_avail = self.check_tool('Ghostscript')
        # Create the pages
        self.home = name
        self.back_img = self.copy('back', MID_ICON)
        self.home_img = self.copy('home', MID_ICON)
        copy2(os.path.join(self.img_src_dir, 'favicon.ico'), os.path.join(self.out_dir, 'favicon.ico'))
        # Copy the logo image
        if self.logo is not None and self.header:
            with open(os.path.join(self.out_dir, 'images', 'logo.png'), 'wb') as f:
                f.write(self._logo_data)
        self.solve_title()
        self.navbar = self.generate_navbar(o_tree, name) if self.nav_bar else ''
        self.top_menu = self.generate_top_menu() if self.nav_bar or self.header else ''
        self.generate_page_for(o_tree, name)
        # Link it?
        if self.link_from_root:
            redir_file = os.path.join(GS.out_dir, self.link_from_root)
            rel_start = os.path.relpath(os.path.join(self.out_dir, name), start=GS.out_dir)
            logger.debug('Creating redirector: {} -> {}'.format(redir_file, rel_start))
            with open(redir_file, 'wt') as f:
                f.write('<html>\n<head>\n<meta http-equiv="refresh" content="0; {}"/>'.format(rel_start))
                f.write('</head>\n</html>')


@output_class
class Navigate_Results(BaseOutput):  # noqa: F821
    """ Navigate Results
        Generates a web page to navigate the generated outputs """
    def __init__(self):
        super().__init__()
        # Make it low priority so it gets created after all the other outputs
        self.priority = 10
        with document:
            self.options = Navigate_ResultsOptions
            """ *[dict={}] Options for the `navigate_results` output """
        # The help is inherited and already mentions the default priority
        self.fix_priority_help()
        self._any_related = True

    @staticmethod
    def get_conf_examples(name, layers):
        outs = BaseOutput.simple_conf_examples(name, 'Web page to browse the results', 'Browse')  # noqa: F821
        outs[0]['options'] = {'link_from_root': 'index.html', 'skip_not_run': True}
        return outs
