"""
Tests SCH errors


For debug information use:
pytest-3 --log-cli-level debug
"""
import pytest
from . import context
from kibot.misc import CORRUPTED_SCH


def setup_ctx(test_dir, test, error):
    sch = ('v5' if context.ki5() else 'v6')+'_errors/error_'+test
    test = 'test_sch_errors_'+test
    ctx = context.TestContextSCH(test_dir, sch, 'int_bom_simple_csv', test_name='sch_'+test)
    ctx.run(CORRUPTED_SCH)
    ctx.search_err(error)
    ctx.clean_up()


def test_sch_errors_no_signature(test_dir):
    sig = 'eeschema' if context.ki5() else 'kicad_sch'
    setup_ctx(test_dir, 'no_signature', 'No '+sig+' signature')


def test_sch_errors_no_eelayer(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'no_eelayer', 'Missing EELAYER')


def test_sch_errors_no_eelayer_end(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'no_eelayer_end', 'Missing EELAYER END')


def test_sch_errors_unknown_def(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'unknown_def', 'Unknown definition')


def test_sch_errors_eof(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'eof', 'Unexpected end of file')


def test_sch_errors_l1(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'l1', 'Unexpected end of file')


def test_sch_errors_l2(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'l2', 'Unexpected end of file')


def test_sch_errors_l3(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'l3', 'Malformed component field')


# Now we support it:
# def test_sch_errors_l4(test_dir):
#     setup_ctx(test_dir, 'l4', 'Missing component field name')


def test_sch_errors_l5(test_dir):
    if context.ki6():
        return
    setup_ctx(test_dir, 'l5', ['Unknown polygon definition', 'Expected 6 coordinates and got 8 in polygon',
                               'Unknown square definition', 'Unknown circle definition', 'Unknown arc definition',
                               'Unknown text definition', 'Unknown pin definition', 'Failed to load component definition',
                               'Unknown draw element'])


def test_sch_errors_l6(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'l6', 'Missing library signature')


def test_sch_errors_l7(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'l7', 'Unknown library entry')


def test_sch_errors_l8(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'l8', ['Unknown DCM entry', 'Unknown DCM attribute'])


def test_sch_errors_l9(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'l9', ['Missing DCM signature', 'Component (.*?) is not annotated'])


def test_sch_errors_field(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'field', 'Malformed component field')


def test_sch_errors_field_name(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'field_name', 'Missing component field name')


def test_sch_errors_ar(test_dir):
    if context.ki6():
        return
    setup_ctx(test_dir, 'ar', ['Unknown AR field .?Bogus.?', 'Alternative Reference without path',
                               'Alternative Reference without reference', 'Component `U1` without the basic fields',
                               'Footprint with more than one colon'])


def test_sch_errors_miss_label(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_label', 'Missing component label')


def test_sch_errors_bad_label(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_label', 'Malformed component label')


def test_sch_errors_miss_unit(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_unit', 'Missing component unit')


def test_sch_errors_bad_unit(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_unit', 'Malformed component unit')


def test_sch_errors_miss_pos(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_pos', 'Missing component position')


def test_sch_errors_bad_pos(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_pos', ['Malformed component position', 'Inconsistent position for component'])


def test_sch_errors_miss_red_pos(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_red_pos', 'Missing component redundant position')


def test_sch_errors_bad_red_pos(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_red_pos', 'Malformed component redundant position')


def test_sch_errors_miss_matrix(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_matrix', 'Missing component orientation matrix')


def test_sch_errors_bad_matrix(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_matrix', 'Malformed component orientation matrix')


def test_sch_errors_wrong_ref(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'wrong_ref', 'Malformed component reference')


def test_sch_errors_bad_conn(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_conn', 'Malformed no/connection')


def test_sch_errors_bad_text(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_text', 'Malformed .?Text.?')


def test_sch_errors_bad_text2(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_text2', 'Missing .?Text.? shape')


def test_sch_errors_bad_text3(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_text3', 'Not a number in .?Text.?')


def test_sch_errors_bad_wire(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_wire', 'Malformed wire')


def test_sch_errors_bad_wire2(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_wire2', 'Malformed wire')


def test_sch_errors_bad_wire3(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_wire3', 'Malformed wire')


def test_sch_errors_bad_wire4(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_wire4', 'Malformed wire')


def test_sch_errors_bad_entry(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_entry', 'Malformed entry')


def test_sch_errors_bmp_miss_pos(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bmp_miss_pos', 'Missing bitmap position')


def test_sch_errors_bmp_bad_pos(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bmp_bad_pos', 'Malformed bitmap position')


def test_sch_errors_bmp_miss_sca(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bmp_miss_sca', 'Missing bitmap scale')


def test_sch_errors_bmp_bad_sca(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bmp_bad_sca', 'Malformed bitmap scale')


def test_sch_errors_bmp_miss_dat(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bmp_miss_dat', 'Missing bitmap data')


def test_sch_errors_bmp_bad_dat(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bmp_bad_dat', 'Malformed bitmap data')


def test_sch_errors_bmp_miss_end(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bmp_miss_end', 'Missing end of bitmap')


def test_sch_errors_bad_plabel(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_plabel', 'Malformed sheet port label')


def test_sch_errors_miss_spos(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_spos', 'Missing sheet size and position')


def test_sch_errors_bad_spos(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_spos', 'Malformed sheet size and position')


def test_sch_errors_bad_slabel(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_slabel', 'Malformed sheet label')


def test_sch_errors_bad_sname(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_sname', 'Malformed sheet name')


def test_sch_errors_miss_sname(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_sname', 'Missing sub-sheet name')


def test_sch_errors_bad_sfname(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_sfname', 'Malformed sheet file name')


def test_sch_errors_miss_sfname(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_sfname', 'Missing sub-sheet file name')


def test_sch_errors_miss_descr(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'miss_descr', r'Missing \$Descr')


def test_sch_errors_bad_encoding(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_encoding', 'Unsupported encoding')


def test_sch_errors_bad_snum(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_snum', 'Wrong sheet number')


def test_sch_errors_bad_tbentry(test_dir):
    if context.ki5():
        setup_ctx(test_dir, 'bad_tbentry', 'Wrong entry in title block')


def test_imported_k6(test_dir):
    """ Test we can load an schematic with an imported sub-sheet (#178) """
    if context.ki6():
        prj = 'imported_top'
        ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_csv')
        ctx.run()


@pytest.mark.skipif(not context.ki8(), reason="Just v8 test")
def test_field_duplicated(test_dir):
    """ Test MNP vs mnp collision """
    prj = 'field_duplicated'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_csv_mpn')
    ctx.run()
    ctx.search_err("Field conflict: MNP='Different' vs mnp='Test_1'")
    ctx.clean_up()
