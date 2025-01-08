import pcbnew
b = pcbnew.LoadBoard('../../tests/board_samples/kicad_8/light_control.kicad_pcb')
with open('list_k8.txt') as f:
    for c, line in enumerate(f):
        print(f'{c}: {b.GetLayerID(line.strip())},')

