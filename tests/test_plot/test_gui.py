"""
Tests the GUI.

For debug information use:
pytest-3 --log-cli-level debug
"""
from contextlib import contextmanager
import csv
import json
import logging
import os
import pytest
import signal
from subprocess import Popen, TimeoutExpired
import sys
from xvfbwrapper import Xvfb
from . import context
CSVDIR = "tests/GUI/CSV/"
MAIN_OUPUTS_PAGE = 1
MAIN_GROUPS_PAGE = 2
MAIN_PREFLIGHTS_PAGE = 3
MAIN_FILTERS_PAGE = 4
MAIN_VARIANTS_PAGE = 5
MAIN_ABOUT_PAGE = 6


class PopenContext(Popen):

    def __exit__(self, type, value, traceback):
        logging.debug("Closing pipe with %d", self.pid)
        # Note: currently we don't communicate with the child so these cases are never used.
        # I keep them in case they are needed, but excluded from the coverage.
        # Also note that closing stdin needs extra handling, implemented in the parent class
        # but not here.
        # This can generate a deadlock
        # if self.stdout:
        #     self.stdout.close()  # pragma: no cover
        if self.stderr:
            self.stderr.close()  # pragma: no cover
        if self.stdin:
            self.stdin.close()   # pragma: no cover
        if type:
            logging.debug("Terminating %d", self.pid)
            # KiCad nightly uses a shell script as intermediate to run setup the environment
            # and run the proper binary. If we simply call "terminate" we just kill the
            # shell script. So we create a group and then kill the whole group.
            try:
                os.killpg(os.getpgid(self.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            # self.terminate()
        # Wait for the process to terminate, to avoid zombies.
        try:
            # Wait for 3 seconds
            self.wait(3)
            retry = False
        except TimeoutExpired:  # pragma: no cover
            # The process still alive after 3 seconds
            retry = True
        if retry:  # pragma: no cover
            logging.debug("Killing %d", self.pid)
            # We shouldn't get here. Kill the process and wait upto 10 seconds
            os.killpg(os.getpgid(self.pid), signal.SIGKILL)
            # self.kill()
            self.wait(10)


@contextmanager
def start_record(do_record, video_dir, video_name):
    if do_record:
        video_filename = os.path.join(video_dir, video_name)
        cmd = ['recordmydesktop', '--overwrite', '--no-sound', '--no-frame', '--on-the-fly-encoding',
               '-o', video_filename]
        logging.debug('Recording session with: '+str(cmd))
        with PopenContext(cmd, start_new_session=True) as screencast_proc:
            try:
                yield
            finally:
                logging.debug('Terminating the session recorder')
                screencast_proc.terminate()
    else:
        yield


class Events(object):
    def __init__(self):
        super().__init__()
        self.e = []

    def wait(self, w):
        self.e.append(['', '_WaitDialog', w])

    def wait_splash(self):
        self.wait('splash')

    def wait_main(self):
        self.wait('main_dialog')

    def start(self):
        self.wait_splash()
        self.wait_main()

    def set_path(self, id, cfg):
        self.e.append([id, 'SetPath', cfg])

    def send_event(self, id, ev_name):
        self.e.append([id, '_SendEvent', ev_name])

    def set_cfg(self, cfg):
        self.set_path('ID_CFG_FILE', cfg)
        self.send_event('ID_CFG_FILE', 'EVT_FILEPICKER_CHANGED')

    def set_sch(self, sch):
        self.set_path('ID_SCH', sch)
        self.send_event('ID_SCH', 'EVT_FILEPICKER_CHANGED')

    def set_selection(self, id, selected):
        self.e.append([id, 'SetSelection', selected])

    def set_choice(self, id, selected):
        self.e.append([id, 'SetSelection', selected])
        self.send_event(id, 'EVT_CHOICE')

    def check_path(self, id, path):
        self.e.append([id, '_CheckPath', path])

    def sel_outputs_page(self):
        self.set_selection('ID_MAIN_NOTEBOOK', MAIN_OUPUTS_PAGE)

    def sel_filters_page(self):
        self.set_selection('ID_MAIN_NOTEBOOK', MAIN_FILTERS_PAGE)

    def sel_preflights_page(self):
        self.set_selection('ID_MAIN_NOTEBOOK', MAIN_PREFLIGHTS_PAGE)

    def sel_variants_page(self):
        self.set_selection('ID_MAIN_NOTEBOOK', MAIN_VARIANTS_PAGE)

    def sel_groups_page(self):
        self.set_selection('ID_MAIN_NOTEBOOK', MAIN_GROUPS_PAGE)

    def send_text(self, txt):
        self.e.append(['', '_SendText', txt])

    def send_keys(self, keys):
        self.e.append(['', '_SendText']+keys)

    def send_key(self, key):
        self.e.append(['', '_SendKey', key])

    def new_output(self, name):
        self.send_event('output.add', 'EVT_BUTTON')
        self.wait('choose_an output type')  # From choose_type
        self.send_text(name)
        self.enter()
        self.wait('output.'+name)  # self.dict_type

    def new_group(self, name):
        self.send_event('groups.add', 'EVT_BUTTON')
        self.wait('edit_group')
        self.set_value('edit_group.name', name)

    def add_output_to_group(self, short):
        self.send_event('edit_group.add', 'EVT_BUTTON')
        self.wait('choose_an output')
        self.send_text(short)
        self.enter()
        self.wait('edit_group')

    def add_group_to_group(self, short):
        self.send_event('edit_group.add_add', 'EVT_BUTTON')
        self.wait('choose_a group')
        self.send_text(short)
        self.enter()
        self.wait('edit_group')

    def new_filter(self, name):
        self.send_event('filter.add', 'EVT_BUTTON')
        self.wait('choose_a filter type')
        self.send_text(name)
        self.enter()
        self.wait('filter.'+name)

    def new_preflight(self, name):
        self.send_event('preflight.add', 'EVT_BUTTON')
        self.wait('choose_a preflight')
        self.send_text(name)
        self.enter()
        self.wait('preflight.'+name)

    def new_variant(self, name):
        self.send_event('variant.add', 'EVT_BUTTON')
        self.wait('choose_a variant type')
        self.send_text(name)
        self.enter()
        self.wait('variant.'+name)

    def new_last_preflight(self, name):
        self.send_event('preflight.add', 'EVT_BUTTON')
        self.wait('preflight.'+name)

    def set_value(self, id, value):
        self.e.append([id, 'SetValue', value])

    def toggle_value(self, id):
        self.e.append([id, '_ToggleValue', ''])

    def edit_dict(self, id):
        self.send_event(id, 'EVT_BUTTON')
        self.wait(id)

    def add_dict(self, id):
        self.send_event(id+'.add', 'EVT_BUTTON')
        self.wait(id)

    def ok(self):
        self.send_event('wx.ID_OK', 'EVT_BUTTON')

    def press_button(self, name):
        self.send_event('name:'+name, 'EVT_BUTTON')

    def save(self):
        self.send_event('ID_SAVE', 'EVT_BUTTON')

    def esc(self):
        self.send_key('wx.WXK_ESCAPE')

    def enter(self):
        self.send_key('wx.WXK_RETURN')

    def down(self):
        self.send_key('wx.WXK_DOWN')

    def save_events(self, cfg):
        with open(cfg, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(self.e)


def run_test(num, test_dir, project, recipe, keep_project=False, no_board_file=False, no_yaml_file=False):
    id = "%04d" % num
    base_name = sys._getframe(1).f_code.co_name[9:]
    yaml_base = f'{id}.kibot.yaml'
    yaml_ori = os.path.abspath('tests/GUI/cfg_in/'+yaml_base)
    logging.debug(f'Using `{yaml_ori}` config name')
    assert os.path.isfile(yaml_ori)
    with open(yaml_ori) as f:
        yaml_txt = f.read()
    ctx = context.TestContext(test_dir, project, yaml_ori, test_name=sys._getframe(1).f_code.co_name)
    cfg = ctx.get_out_path('events.csv')
    recipe(ctx).save_events(cfg)
    logging.debug(f'Using `{cfg}` events')
    yaml_out = ctx.get_out_path('result.kibot.yaml')
    try:
        with Xvfb(width=1920, height=1080, colordepth=24):
            with start_record(True, ctx.output_dir, base_name):
                extra = ['--gui', '-I', cfg]
                ctx.run(extra=extra, no_board_file=no_board_file, no_yaml_file=no_yaml_file)
    finally:
        with open(yaml_ori) as f:
            yaml_res = f.read()
        with open(yaml_ori, 'w') as f:
            f.write(yaml_txt)
        with open(yaml_out, 'w') as f:
            f.write(yaml_res)
    ctx.compare_txt(text=os.path.abspath(yaml_out), reference=os.path.abspath('tests/GUI/cfg_out/'+yaml_base))
    ctx.clean_up(keep_project=keep_project)


def new_board_view_recipe(ctx):
    e = Events()
    e.start()
    e.set_cfg(ctx.yaml_file)
    e.set_sch(ctx.sch_file)
    # Check that setting the SCH is enough to also get the PCB
    e.check_path('ID_PCB', 'light_control.kicad_pcb')
    e.sel_outputs_page()
    e.new_output('boardview')
    e.set_value('output.boardview.name.string', 'test_output')
    e.ok()
    e.wait_main()
    e.save()
    e.esc()
    return e


def new_board_view_deep_recipe(ctx):
    e = Events()
    e.start()
    e.check_path('ID_CFG_FILE', 'tests/GUI/cfg_in/0002.kibot.yaml')
    e.check_path('ID_SCH', 'light_control.kicad_sch')
    e.check_path('ID_PCB', 'light_control.kicad_pcb')
    e.sel_outputs_page()
    e.new_output('boardview')
    e.set_value('output.boardview.name.string', 'test_output')
    e.edit_dict('output.boardview.options.dict')
    # Advanced options
    e.set_selection('output.boardview.options.dict.notebook', 1)
    # BVR format
    e.set_choice('output.boardview.options.dict.format.string', 1)
    e.press_button('output.boardview.options.dict.ok')
    e.wait('output.boardview')
    e.press_button('output.boardview.ok')
    e.wait_main()
    e.save()
    e.esc()
    return e


def try_groups_1_recipe(ctx):
    e = Events()
    e.start()
    e.sel_groups_page()
    # A new group fab
    e.new_group('fab')
    e.add_output_to_group('ger')
    e.add_output_to_group('exc')
    e.add_output_to_group('pos')
    e.press_button('edit_group.ok')
    e.wait_main()
    # Edit the plot group
    e.enter()
    e.wait('edit_group')
    e.add_output_to_group('Pcb')
    e.add_output_to_group('Pcb')
    e.press_button('edit_group.ok')
    e.wait_main()
    # Edit the fab_svg group
    e.send_keys(['wx.WXK_DOWN', 'wx.WXK_RETURN'])
    e.wait('edit_group')
    e.add_group_to_group('fab')
    e.press_button('edit_group.ok')
    e.wait_main()
    e.save()
    e.esc()
    return e


@pytest.mark.indep
def test_gui_new_board_view_1(test_dir):
    """ We start without config.
        Force a known YAML, set an SCH, add a boardview output, name it test_output and save """
    run_test(1, test_dir, 'light_control', new_board_view_recipe, keep_project=True, no_board_file=True, no_yaml_file=True)


@pytest.mark.indep
def test_gui_new_board_view_2(test_dir):
    """ We start with config and SCH.
        Add a boardview output, name it test_output and save """
    run_test(2, test_dir, 'light_control', new_board_view_deep_recipe, keep_project=True)


def get_simple(path, items):
    for i in items:
        name = i[0]
        if name == 'variant':
            # Variants are verified during config
            continue
        if (name == 'description' or name == 'template') and path == 'output.kikit_present.options.dict':
            # Is a file name
            continue
        if name == 'name' and path == 'output.kikit_present.options.dict.boards.dict':
            # Is a PCB file
            continue
        if name == 'output' and path.startswith('output.stencil'):
            # Pattern with %i
            continue
        if name == 'layer' and path.endswith('.layers.dict'):
            # Valid layer name
            continue
        if name == 'enabled' and path.startswith('preflight.'):
            continue
        valids = i[1]
        if 'DataTypeDict' in valids:
            continue
        if 'DataTypeString' in valids:
            return name, 'string'
        if 'DataTypeNumber' in valids:
            return name, 'number'
        if 'DataTypeBoolean' in valids:
            return name, 'boolean'
    return None, None


def for_output(e, name, items, level=0):
    input, ikind = get_simple(name, items)
    if input:
        val = name
        if ikind == 'number':
            val = 'str:20'
        elif ikind == 'string' and input == 'separator':
            val = ','
        # Panelize
        elif ikind == 'string' and (input == 'posx' or input == 'hspace' or input == 'vwidth' or input == 'drill' or
                                    input == 'hoffset' or input == 'clearance' or input == 'tolerance'):
            val = '1mm'
        # PcbDraw
        elif ikind == 'string' and input == 'copper':
            val = '#5e283a'
        # KiBoM
        elif ikind == 'string' and input == 'field':
            val = 'References'
        if ikind == 'boolean':
            id = f'{name}.{input}.{ikind}'
            e.toggle_value(id)
            e.send_event(id, 'EVT_CHECKBOX')
        else:
            e.set_value(f'{name}.{input}.{ikind}', val)
    for i in items:
        input, valids, data = i
        if data:
            entry = f'{name}.{input}.dict'
            if ('DataTypeDict' in valids) or ('DataTypeListDictSingular' in valids):
                e.edit_dict(entry)
            else:
                e.add_dict(entry)
            for_output(e, entry, data, level+1)
            e.press_button(entry+'.ok')
            e.wait(name)


def try_all_outputs_recipe(ctx):
    with open('tests/GUI/outputs') as f:
        data = json.load(f)
    e = Events()
    e.start()
    e.sel_outputs_page()
    for o, c in data.items():
        e.new_output(o)
        name = 'output.'+o
        for_output(e, name, c)
        e.press_button(name+'.ok')
        e.wait_main()
    e.save()
    e.esc()
    return e


def try_all_preflights_recipe(ctx):
    with open('tests/GUI/preflights') as f:
        data = json.load(f)
    e = Events()
    e.start()
    e.sel_preflights_page()
    total = len(data)
    for n, (o, c) in enumerate(data.items()):
        if n < total-1:
            e.new_preflight(o)
        else:
            e.new_last_preflight(o)
        name = 'preflight.'+o
        # Preflights can embed the first level
        if len(c) == 1 and c[0][2] and 'DataTypeDict' in c[0][1]:
            if len(c[0][1]) > 1:
                # We have multiple data types, ensure the dict is selected
                e.set_selection(name+'.'+o+'.choices', c[0][1].index('DataTypeDict'))
                e.send_event(name+'.'+o+'.choices', 'EVT_CHOICE')
            for_output(e, name, c[0][2])
        else:
            for_output(e, name, c)
        e.press_button(name+'.ok')
        e.wait_main()
    e.save()
    e.esc()
    return e


def try_all_filters_recipe(ctx):
    with open('tests/GUI/filters') as f:
        data = json.load(f)
    e = Events()
    e.start()
    e.sel_filters_page()
    for o, c in data.items():
        e.new_filter(o)
        name = 'filter.'+o
        for_output(e, name, c)
        e.press_button(name+'.ok')
        e.wait_main()
    e.save()
    e.esc()
    return e


def try_all_variants_recipe(ctx):
    with open('tests/GUI/variants') as f:
        data = json.load(f)
    e = Events()
    e.start()
    e.sel_variants_page()
    for o, c in data.items():
        e.new_variant(o)
        name = 'variant.'+o
        for_output(e, name, c)
        e.press_button(name+'.ok')
        e.wait_main()
    e.save()
    e.esc()
    return e


@pytest.mark.indep
def test_gui_try_all_outputs_1(test_dir):
    run_test(3, test_dir, 'light_control', try_all_outputs_recipe, keep_project=True)


@pytest.mark.indep
def test_gui_try_all_preflights_1(test_dir):
    run_test(4, test_dir, 'light_control', try_all_preflights_recipe, keep_project=True)


@pytest.mark.indep
def test_gui_try_all_filters_1(test_dir):
    run_test(5, test_dir, 'light_control', try_all_filters_recipe, keep_project=True)


@pytest.mark.indep
def test_gui_try_all_variants_1(test_dir):
    run_test(6, test_dir, 'light_control', try_all_variants_recipe, keep_project=True)


@pytest.mark.indep
def test_gui_groups_1(test_dir):
    run_test(7, test_dir, 'light_control', try_groups_1_recipe, keep_project=True)
