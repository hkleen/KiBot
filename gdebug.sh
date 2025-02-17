#!/bin/bash
whoami
ls ~
ls -la /root/.config/blender/4.2/extensions/blender_org/
cat /root/.config/blender/4.2/extensions/blender_org/.blender_ext/index.json
ln -s /root/.config/blender/4.2/extensions/blender_org/pcb3d_importer /bin/4.2/extensions/system/
ls -la /bin/4.2/extensions/system/
blender --online-mode --command extension list
