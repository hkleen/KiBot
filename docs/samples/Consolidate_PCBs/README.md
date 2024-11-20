# Consolidate PCB example

Here we have 3 PCBs:

- *batteryPack-variant_battery.kicad_pcb*
- *batteryPack-variant_charger.kicad_pcb*
- *batteryPack-variant_connector.kicad_pcb*

And we want to create a new PCB containing them using the layout found in
*batteryPack_new_layout.kicad_pcb*

So we use the following *consolidate_pcb.kibot.yaml*:

```yaml
kibot:
  version: 1

preflight:
  consolidate_pcbs:
    - name: Battery
      file: batteryPack-variant_battery.kicad_pcb
    - name: Charger
      file: batteryPack-variant_charger.kicad_pcb
    - name: Connector
      file: batteryPack-variant_connector.kicad_pcb
```

Note that the names (Battery, Charger and Connector) are the names used inside
the text boxes in *batteryPack_new_layout.kicad_pcb*

After running this script, i.e.:

```
kibot -b batteryPack_new_layout.kicad_pcb
```

The *batteryPack_new_layout.kicad_pcb* will be replaced by the desired PCB.
The old PCB is renamed to *batteryPack_new_layout.kicad_pcb-bak*.

This new PCB can be used to create a 3D render containing the 3 PCBs.


# Note about the 3 PCBs

These PCBs were generated using the *batteryPack.kicad_pcb* example and the
following config:

```yaml
kibot:
  version: 1

variants:
  - name: 'default'
    comment: 'Default variant'
    type: ibom
    sub_pcbs:
      - name: charger
        tlx: 175
        tly: 30
        brx: 258
        bry: 92
      - name: battery
        tlx: 10
        tly: 20
        brx: 110
        bry: 121
      - name: connector
        tlx: 100
        tly: 28
        brx: 160
        bry: 113

outputs:
  - name: 'pcb_charger'
    comment: "PCB for the charger"
    type: pcb_variant
    options:
      variant: default[charger]
      title: 'Charger'

  - name: 'pcb_battery'
    comment: "PCB for the battery"
    type: pcb_variant
    options:
      variant: default[battery]
      title: 'Battery'

  - name: 'pcb_connector'
    comment: "PCB for the connector"
    type: pcb_variant
    options:
      variant: default[connector]
      title: 'Connector'
```

So KiBot can do both things:

- Split a PCB
- Merge PCBs
