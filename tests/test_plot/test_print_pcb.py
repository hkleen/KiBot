"""
Tests of Printing PCB files

We test:
- PDF for bom.kicad_pcb

For debug information use:
pytest-3 --log-cli-level debug

"""
import logging
import pytest
from . import context
PDF_DIR = 'Layers'
PDF_FILE = 'bom-F_Cu+F_SilkS.pdf'
PDF_FILE_B = 'PCB_Bot.pdf'
PDF_FILE_C = 'PCB_Bot_def.pdf'


@pytest.mark.slow
def test_print_pcb_simple(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'print_pcb', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file_d(PDF_FILE)
    ctx.clean_up()


@pytest.mark.slow
def test_print_pcb_svg_simple_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_svg')
    ctx.run()
    # Check all outputs are there
    file = PDF_FILE.replace('.pdf', '.svg')
    ctx.expect_out_file(file)
    ctx.compare_image(file)
    ctx.clean_up()


@pytest.mark.slow
def test_print_pcb_svg_simple_2(test_dir):
    """ Check the portrait version is OK """
    prj = 'bom_portrait'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_svg')
    ctx.run()
    # Check all outputs are there
    file = prj+'-F_Cu+F_SilkS.svg'
    ctx.expect_out_file(file)
    ctx.compare_image(file)
    ctx.clean_up()


@pytest.mark.slow
def test_print_pcb_refill_1(test_dir):
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_zone-refill')
    ctx.run()
    ctx.expect_out_file(PDF_FILE_B)
    ctx.compare_image(PDF_FILE_B)
    ctx.clean_up()


@pytest.mark.slow
def test_print_pcb_refill_2(test_dir):
    """ Using KiCad 6 colors """
    if context.ki5():
        return
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_zone-refill_def')
    ctx.run()
    ctx.expect_out_file(PDF_FILE_B)
    ctx.compare_image(PDF_FILE_B, PDF_FILE_C)
    ctx.clean_up()


@pytest.mark.slow
def test_print_variant_1(test_dir):
    prj = 'kibom-variant_3_txt'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_variant_1')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-F_Fab.pdf'
    ctx.search_err(r'KiCad project file not found', True)
    ctx.expect_out_file(fname)
    ctx.compare_pdf(fname, height='100%')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
def test_print_pcb_options(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_options', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(PDF_FILE)
    ctx.compare_pdf(PDF_FILE)
    ctx.clean_up()


@pytest.mark.slow
def test_print_wrong_paste(test_dir):
    prj = 'wrong_paste'
    ctx = context.TestContext(test_dir, prj, 'wrong_paste', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-F_Fab.pdf')
    ctx.search_err(r'Pad with solder paste, but no copper')
    ctx.clean_up()


@pytest.mark.slow
def test_pcb_print_simple_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'pcb_print_2')
    ctx.run()
    ctx.expect_out_file(prj+'-assembly_page_01.png')
    ctx.expect_out_file(prj+'-assembly_page_02.png')
    ctx.expect_out_file(prj+'-assembly_page_01.eps')
    ctx.expect_out_file(prj+'-assembly_page_01.svg')
    ctx.expect_out_file(prj+'-assembly.ps')
    ctx.clean_up(keep_project=True)


def test_pcb_print_simple_2(test_dir):
    if context.ki6():
        prj = 'pcb_print_rare'
        yaml = 'pcb_print_3'
    else:
        prj = 'bom_portrait'
        yaml = 'pcb_print_4'
    ctx = context.TestContext(test_dir, prj, yaml)
    ctx.run()
    file = ctx.expect_out_file(prj+'-assembly.pdf')
    w, h = ctx.get_pdf_size(file)
    logging.debug('PDF size {} x {} mm'.format(w, h))
    if context.ki6():
        assert abs(w-431.8) < 0.1 and abs(h-279.4) < 0.1
    else:
        assert abs(w-210.0) < 0.1 and abs(h-297.0) < 0.1
    ctx.clean_up()
