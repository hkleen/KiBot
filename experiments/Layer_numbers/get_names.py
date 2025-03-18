import pcbnew
for la in range(60):
    print(pcbnew.BOARD.GetStandardLayerName(la))
