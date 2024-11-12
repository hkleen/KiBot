# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from .gs import GS
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401


class Sch_Variant_Options(VariantOptions):
    def __init__(self):
        with document:
            self.copy_project = False
            """ Copy the KiCad project to the destination directory.
                Disabled by default for compatibility with older versions """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
        super().__init__()

    def get_targets(self, out_dir):
        targets = list(GS.sch.file_names_variant(out_dir))
        if self.copy_project:
            targets.extend(GS.copy_project_names(GS.sch_file, ref_dir=out_dir))
        return targets

    def run(self, output_dir):
        super().run(output_dir)
        # Create the schematic
        self.set_title(self.title, sch=True)
        replaced_images = self.sch_replace_images(GS.sch)
        GS.sch.save_variant(output_dir)
        self.restore_title(sch=True)
        if replaced_images:
            self.sch_restore_images(GS.sch)
        if self.copy_project:
            GS.copy_project(os.path.join(output_dir, GS.sch_basename+'.kicad_pcb'))


@output_class
class Sch_Variant(BaseOutput):  # noqa: F821
    """ Schematic with variant generator
        Creates a copy of the schematic with all the filters and variants applied.
        This copy isn't intended for development.
        Is just a tweaked version of the original where you can look at the results.
        Supports the image replacement using the prefix indicated by the `sch_image_prefix` global variable """
    def __init__(self):
        super().__init__()
        with document:
            self.options = Sch_Variant_Options
            """ *[dict={}] Options for the `sch_variant` output """
        self._sch_related = True

    def get_output_sch_name(self, out_dir):
        return os.path.join(out_dir, os.path.basename(GS.sch_file))

    def run(self, output_dir):
        # No output member, just a dir
        self.options.run(output_dir)
