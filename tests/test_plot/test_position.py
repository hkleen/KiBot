"""
Tests of position file

The 3Rs.kicad_pcb has R1 on top, R2 on bottom and a thru-hole component R3 on top.
We test (both CSV and ASCII):
- Separated files, mm, only SMD
- Unified file, mm, only SMD
- Unified file, mm, not only SMD
- Separated files, inches, only SMD
- Also test a case:
  - without 'comment' field
  - with coloured logs
  - in quiet mode
  - compressed YAML file

For debug information use:
pytest-3 --log-cli-level debug

"""
import os
import logging
import pytest
from kibot.misc import EXIT_BAD_CONFIG
from . import context

POS_DIR = 'positiondir'
positions = {'R1': (105, 35, 'top', 90),
             'R2': (110, 35, 'bottom', 270),
             'R3': (110, 45, 'top', 0),
             'U1': (100, 100, 'bottom', 90)}
CSV_EXPR = r'^"%s",[^,]+,[^,]+,([-\d\.]+),([-\d\.]+),([-\d\.]+),(\S+)$'
ASCII_EXPR = r'^%s\s+\S+\s+\S+\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+(\S+)\s*$'


def expect_position(ctx, file, comp, no_comp=(), inches=False, csv=False, neg_x=False, a_pos=positions):
    """
    Check if a list of components are or aren't in the file
    """
    # Components that must be found
    texts = []
    for k in comp:
        if csv:
            texts.append(CSV_EXPR % k)
        else:
            texts.append(ASCII_EXPR % k)
    res = ctx.search_in_file(file, texts)
    for k in comp:
        x, y, side, angle = a_pos[k]
        if inches:
            x = x/25.4
            y = y/25.4
        if neg_x:
            x = -x
        matches = res.pop(0)
        assert abs(float(x) - float(matches[0])) < 0.001, k
        assert abs(float(y) + float(matches[1])) < 0.001, k
        assert angle == float(matches[2]) % 360, k
        assert side == matches[3], k

    # Components that must not be found
    texts = []
    for k in no_comp:
        if csv:
            expr = CSV_EXPR % k
        else:
            expr = ASCII_EXPR % k
        texts.append(expr)
    ctx.search_not_in_file(file, texts)


def test_position_3Rs_1(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_filename()
    pos_bot = ctx.get_pos_bot_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'])
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'])
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Just checking with modern KiCad")
def test_panel_C1x4_base(test_dir):
    """ This tests a 4 boards panel with just one component C1
        Half of the panel is rotated 180 degrees """
    ctx = context.TestContext(test_dir, 'panel_C1x4', 'simple_position_csv', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_csv_filename()
    rows, header, info = ctx.load_csv(os.path.basename(pos_top))
    assert len(rows) == 4
    assert sum(1 for x in rows if float(x[5]) == 180) == 2
    assert sum(1 for x in rows if float(x[5]) == 0) == 2
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Just checking with modern KiCad")
def test_panel_C1x4_rep(test_dir):
    """ This tests a 4 boards panel with just one component C1
        In this case the schematic also has four C1 components
        Half of the panel is rotated 180 degrees """
    ctx = context.TestContext(test_dir, 'panel_C1x4_rep', 'simple_position_csv', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_csv_filename()
    rows, header, info = ctx.load_csv(os.path.basename(pos_top))
    assert len(rows) == 4
    assert sum(1 for x in rows if float(x[5]) == 180) == 2
    assert sum(1 for x in rows if float(x[5]) == 0) == 2
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Just checking with modern KiCad")
def test_panel_U1x4_base(test_dir):
    """ This tests a 4 boards panel with just one component U1
        The component has 3 sub-units
        Half of the panel is rotated 180 degrees """
    ctx = context.TestContext(test_dir, 'panel_U1x4', 'simple_position_csv', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_csv_filename()
    rows, header, info = ctx.load_csv(os.path.basename(pos_top))
    assert len(rows) == 4
    assert sum(1 for x in rows if float(x[5]) == 180) == 2
    assert sum(1 for x in rows if float(x[5]) == 0) == 2
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Just checking with modern KiCad")
def test_panel_U1x4_rep(test_dir):
    """ This tests a 4 boards panel with just one component U1
        The component has 3 sub-units. The schematic has 4 copies of U1, one with the 3 units and the rest with 2
        Half of the panel is rotated 180 degrees """
    ctx = context.TestContext(test_dir, 'panel_U1x4_rep', 'simple_position_csv', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_csv_filename()
    rows, header, info = ctx.load_csv(os.path.basename(pos_top))
    assert len(rows) == 4
    assert sum(1 for x in rows if float(x[5]) == 180) == 2
    assert sum(1 for x in rows if float(x[5]) == 0) == 2
    ctx.clean_up()


def test_position_3Rs_neg_x(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_neg_x', POS_DIR)
    ctx.run()
    ctx.sub_dir = os.path.join(ctx.sub_dir, 'position')
    pos_top = ctx.get_pos_top_filename()
    pos_bot = ctx.get_pos_bot_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'])
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], neg_x=True)
    ctx.clean_up()


def test_position_3Rs_unified(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_unified', POS_DIR)
    ctx.run()
    expect_position(ctx, ctx.get_pos_both_filename(), ['R1', 'R2'], ['R3'])
    ctx.clean_up()


def test_position_3Rs_unified_th(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_unified_th', POS_DIR)
    ctx.run()
    expect_position(ctx, os.path.join(POS_DIR, ctx.board_name+'-position.pos'), ['R1', 'R2', 'R3'])
    ctx.clean_up()


def test_position_3Rs_inches(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_inches', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_filename()
    pos_bot = ctx.get_pos_bot_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'], True)
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], True)
    ctx.clean_up()


def test_position_3Rs_csv(test_dir):
    """ Also test a case without comment and color logs """
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_csv', POS_DIR)
    ctx.run(use_a_tty=True)
    pos_top = ctx.get_pos_top_csv_filename()
    pos_bot = ctx.get_pos_bot_csv_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'], csv=True)
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], csv=True)
    assert ctx.search_err(r"\[36m.\[1mDEBUG:") is not None
    ctx.clean_up()


def test_position_csv_cols(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_csv_cols', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_csv_filename()
    pos_bot = ctx.get_pos_bot_csv_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    assert ctx.search_in_file(pos_top, ["Ref,Value,Center X"]) is not None
    ctx.search_in_file(pos_top, ['^"R1",'])
    ctx.search_not_in_file(pos_top, ['^"R2",', '^"R3",'])
    ctx.search_in_file(pos_bot, ['^"R2",'])
    ctx.search_not_in_file(pos_bot, ['^"R1",', '^"R3",'])
    ctx.clean_up()


def test_position_3Rs_pre_csv(test_dir):
    """ Test using preprocessor """
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_csv_pre', POS_DIR+'_millimeters')
    ctx.run(extra=['-E', 'UNITS=millimeters'])
    pos_top = ctx.get_pos_top_csv_filename()
    pos_bot = ctx.get_pos_bot_csv_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'], csv=True)
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], csv=True)
    ctx.sub_dir = POS_DIR+'_inches'
    ctx.run(extra=['-E', 'UNITS=inches'])
    pos_top = ctx.get_pos_top_csv_filename()
    pos_bot = ctx.get_pos_bot_csv_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'], csv=True, inches=True)
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], csv=True, inches=True)
    ctx.clean_up()


def test_position_3Rs_unified_csv(test_dir):
    """ Also test the quiet mode """
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_unified_csv', POS_DIR)
    ctx.run(no_verbose=True, extra=['-q'])
    expect_position(ctx, ctx.get_pos_both_csv_filename(), ['R1', 'R2'], ['R3'], csv=True)
    size = os.path.getsize(ctx.get_out_path('error.txt'))
    assert size == 0
    ctx.clean_up()


def test_position_3Rs_unified_th_csv(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_unified_th_csv', POS_DIR)
    ctx.run()
    expect_position(ctx, os.path.join(POS_DIR, 'Test_3Rs-both_pos_OK.csv'), ['R1', 'R2', 'R3'], csv=True)
    ctx.clean_up()


def test_position_3Rs_inches_csv(test_dir):
    """ Also test a compressed configuration YAML file """
    ctx = context.TestContext(test_dir, '3Rs', 'simple_position_inches_csv', POS_DIR,
                              yaml_compressed=True)
    ctx.run()
    pos_top = ctx.get_pos_top_csv_filename()
    pos_bot = ctx.get_pos_bot_csv_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'], inches=True, csv=True)
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], inches=True, csv=True)
    ctx.clean_up()


def check_comps(rows, comps):
    assert len(rows) == len(comps)
    logging.debug('{} components OK'.format(len(rows)))
    col1 = [r[0] for r in rows]
    assert col1 == comps
    logging.debug('Components list {} OK'.format(comps))


def test_position_variant_t2i(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'simple_position_t2i', POS_DIR)
    ctx.run()
    files = ['-both_pos.csv', '-both_pos_[2].csv', '-both_pos_(production).csv', '-both_pos_(test).csv']
    files = [prj+f for f in files]
    rows, header, info = ctx.load_csv(files[0])
    check_comps(rows, ['R1', 'R2', 'R3'])
    rows, header, info = ctx.load_csv(files[1])
    check_comps(rows, ['R1', 'R2'])
    rows, header, info = ctx.load_csv(files[2])
    check_comps(rows, ['C2', 'R1', 'R2', 'R3'])
    rows, header, info = ctx.load_csv(files[3])
    check_comps(rows, ['C1', 'C2', 'R1', 'R3'])
    files = [POS_DIR+'/'+f for f in files]
    ctx.test_compress(prj+'-result.tar.bz2', files)
    ctx.clean_up(keep_project=True)


def test_position_rot_1(test_dir):
    """ Rotation filter inside a variant.
        Also testing the import mechanism for them """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'simple_position_rot_1', POS_DIR)
    ctx.run()
    output = prj+'_cpl_jlc.csv'
    ctx.expect_out_file(output)
    ctx.compare_txt(output)
    ctx.compare_txt(prj+'_bom_jlc.csv')
    ctx.search_err(r"can't import `foobar` filter")
    ctx.search_err(r"can't import `foobar` variant")
    ctx.clean_up(keep_project=True)


def test_position_rot_2(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'simple_position_rot_2', POS_DIR)
    ctx.run(extra_debug=True)
    output = prj+'_cpl_jlc.csv'
    ctx.expect_out_file(output)
    ctx.compare_txt(output)
    ctx.compare_txt(prj+'_bom_jlc.csv')
    ctx.clean_up(keep_project=True)


def test_position_rot_3(test_dir):
    """ Aux origin """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'simple_position_rot_3', POS_DIR)
    ctx.run(extra_debug=True)
    output = prj+'_cpl_jlc_aux.csv'
    ctx.expect_out_file(output)
    ctx.compare_txt(output)
    ctx.clean_up(keep_project=True)


def test_position_rot_4(test_dir):
    """ Importing the variant and filter with a simple import """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'simple_position_rot_4', POS_DIR)
    ctx.run(extra_debug=True)
    output = prj+'_cpl_jlc_aux.csv'
    ctx.expect_out_file(output)
    ctx.compare_txt(output)
    ctx.clean_up(keep_project=True)


def test_position_rot_5(test_dir):
    """ Generate a JLC compatible position file using the Internal BoM """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'simple_position_rot_5', POS_DIR)
    ctx.run()
    output = prj+'_cpl_jlc.csv'
    ctx.expect_out_file(output)
    ctx.compare_txt(output, prj+'_cpl_jlc_nc.csv')
    ctx.clean_up(keep_project=True)


def test_position_rot_6(test_dir):
    """ Generate a MacroFab XYRS compatible position file using the Internal BoM """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'simple_position_rot_6', POS_DIR)
    ctx.run()
    output = prj+'.XYRS'
    ctx.expect_out_file(output)
    ctx.compare_txt(output)
    ctx.clean_up(keep_project=True)


def test_position_rot_bottom(test_dir):
    ctx = context.TestContext(test_dir, 'comp_bottom', 'simple_position_rot_bottom', POS_DIR)
    ctx.run()
    pos_bot = ctx.get_pos_both_filename()
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_bot, ['U1'], neg_x=True)
    ctx.clean_up()


positions_a = {'Q1': (122, 77, 'top', 180),
               # Rotated and moved using *rotations_and_offsets*
               'Q2': (133, 78, 'top', 90),
               # Manually rotated 270
               'Q3': (122, 86, 'top', 270),
               # Manually moved 1,1
               'Q4': (133, 85, 'top', 180),
               'Q5': (122, 77, 'bottom', 0),
               # Offset using *offsets*
               'Q6': (131, 78, 'bottom', 0),
               # Manually rotated 270
               'Q7': (122, 86, 'bottom', 90),
               # Manually moved 1,1
               'Q8': (131, 87, 'bottom', 0)}
POS_TRS = ('Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8')


@pytest.mark.skipif(not context.ki7(), reason="Just testing with 7")
def test_position_rot_a(test_dir):
    """  """
    prj = 'rotations'
    ctx = context.TestContext(test_dir, prj, 'simple_position_rot_a', POS_DIR)
    ctx.run(extra_debug=True)
    output = prj+'-both_pos.csv'
    ctx.expect_out_file(output)
    expect_position(ctx, output, POS_TRS, csv=True, a_pos=positions_a)
    # ctx.compare_txt(output)
    ctx.clean_up()


def test_position_error_same_name(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_position_same_name', POS_DIR)
    ctx.run(EXIT_BAD_CONFIG)
    ctx.search_err(r"(.*)but both with the same name")
    ctx.clean_up()


def check_comp_list(rows, comps):
    cs = set()
    for r in rows:
        cs.add(r[0])
    assert cs == comps


@pytest.mark.skipif(not context.ki6(), reason="in_bom/on_board flags")
def test_position_flags_1(test_dir):
    prj = 'filter_not_in_bom'
    ctx = context.TestContext(test_dir, prj, 'simple_position_unified_csv', POS_DIR)
    ctx.run()
    check_comp_list(ctx.load_csv(prj+'-both_pos.csv')[0], {'R1', 'R2', 'R3', 'R4'})
    ctx.clean_up()


@pytest.mark.skipif(not context.ki6(), reason="in_bom/on_board flags")
def test_position_flags_2(test_dir):
    prj = 'filter_not_in_bom'
    ctx = context.TestContext(test_dir, prj, 'fil_no_bom', POS_DIR)
    ctx.run()
    check_comp_list(ctx.load_csv(prj+'-both_pos.csv')[0], {'R1', 'R4'})
    ctx.clean_up()


@pytest.mark.skipif(not context.ki6(), reason="in_bom/on_board flags")
def test_position_flags_3(test_dir):
    prj = 'filter_not_in_bom'
    ctx = context.TestContext(test_dir, prj, 'fil_no_board', POS_DIR)
    ctx.run()
    check_comp_list(ctx.load_csv(prj+'-both_pos.csv')[0], {'R1', 'R2', 'R3'})
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="needs kicad-cli")
def test_position_gerber_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'simple_position_gbr', POS_DIR)
    ctx.run()
    ctx.expect_out_file_d(prj+'-top_pos.gbr')
    ctx.expect_out_file_d(prj+'-bottom_pos.gbr')
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(context.ki5(), reason="KiKit currently supports KiCad 6 only")
def test_position_sub_pcb_bp_1(test_dir):
    prj = 'batteryPack'
    ctx = context.TestContext(test_dir, prj, 'position_sub_pcb_bp', POS_DIR)
    ctx.run(extra=['-g', 'variant=default[charger]'])
    expect_position(ctx, os.path.join(POS_DIR, prj+'-both_pos_charger.pos'), ['J13'], ['J2', 'J3'],
                    a_pos={'J13': (126.5, 95, 'top', 90)})
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(context.ki5(), reason="KiKit currently supports KiCad 6 only")
def test_position_sub_pcb_bp_2(test_dir):
    prj = 'batteryPack'
    ctx = context.TestContext(test_dir, prj, 'position_sub_pcb_bp_kikit', POS_DIR)
    ctx.run(extra=['-g', 'variant=default[charger]'])
    # KiKit just sends the PCB to 150,100; not centered, A4 page is 270x210:
    # 297/2-150 = -1.5 -> 126.5+1.5
    # 210/2-100 = 5 -> 95-5
    expect_position(ctx, os.path.join(POS_DIR, prj+'-both_pos_charger.pos'), ['J13'], ['J2', 'J3'],
                    a_pos={'J13': (126.5+1.5, 95-5, 'top', 90)})
    ctx.clean_up(keep_project=True)
