"""
Tests of Printing Schematic files

We test:
- STEP for bom.kicad_pcb

For debug information use:
pytest-3 --log-cli-level debug

"""
import os
import pytest
from glob import glob
from . import context


STEP_DIR = '3D'
# STEP_FILE = 'bom.step'


@pytest.mark.slow
def test_step_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'step_simple', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    name = prj+'-3D.step'
    ctx.expect_out_file_d(name)
    # Check the R and C 3D models are there
    ctx.search_in_file_d(name, ['R_0805_2012Metric', 'C_0805_2012Metric'])
    ctx.search_err(['Missing 3D model for R1: `(.*)R_0805_2012Metrico',
                    'Failed to download `(.*)R_0805_2012Metrico'])
    ctx.clean_up()


@pytest.mark.slow
def test_step_2(test_dir):
    prj = 'bom_fake_models'
    yaml = 'step_simple_2'
    if context.ki6():
        yaml += '_k6'
    ctx = context.TestContext(test_dir, prj, 'step_simple_2', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file_d(prj+'-3D.step')
    ctx.search_err(['Missing 3D model for C1', 'Could not add 3D model to C1'], invert=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
def test_step_3(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'step_simple_3', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file_d(prj+'.step')
    ctx.clean_up()


@pytest.mark.slow
def test_step_gl_env(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'step_gl_env', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    name = prj+'-3D.step'
    ctx.expect_out_file_d(name)
    # Check the R and C 3D models are there
    ctx.search_in_file_d(name, ['R_0805_2012Metric', 'R_0805_2012Metrico', 'C_0805_2012Metric'])
    ctx.search_err(['Missing 3D model for R1: `(.*)R_0805_2012Metrico',
                    'Failed to download `(.*)R_0805_2012Metrico'], invert=True)
    ctx.clean_up()


@pytest.mark.slow
def test_step_variant_1(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'step_variant_1')
    ctx.run(extra_debug=True)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-3D.step')
    tmps = glob(os.path.join(ctx.get_board_dir(), 'tmp*pro'))
    assert len(tmps) == 0, tmps
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
def test_render_3d_variant_1(test_dir):
    # Text variables to ensure they are rendered.
    # Traces
    prj = 'kibom-variant_3_txt'
    yaml = 'render_3d_variant_1'
    if context.ki5():
        yaml += '_k5'
    ctx = context.TestContext(test_dir, prj, yaml)
    ctx.run()
    # Check all outputs are there
    name = prj+'-3D_top.png'
    ctx.expect_out_file(name)
    ctx.compare_image(name, fuzz='7%', tol=1000)
    ctx.clean_up(keep_project=True)
