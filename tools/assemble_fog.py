"""Reproduce the retail GM4E01 rev 0 fog overlay hook (keystone-engine).

Hook RaceDrawer::drawPostScene's J2DManager::draw call. Draw a neutral fog
veil after all 3D scene passes and before the HUD, then tail-call the original
HUD routine. GP/VS only; r30 is the native RaceDrawer pointer at this call.
The veil reaches alpha 255 at 100%, covering sky and non-fogged materials.
The original ortho port is restored before drawing, covering every viewport.
"""
import json
from keystone import Ks, KS_ARCH_PPC, KS_MODE_PPC32, KS_MODE_BIG_ENDIAN

SOURCE = '''
stwu 1, -48(1)
mflr 0
stw 0, 52(1)
stw 3, 8(1)
lwz 4, -23608(13)
lwz 4, 56(4)
lwz 4, 8(4)
cmpwi 4, 2
beq draw
cmpwi 4, 3
bne done
draw:
lwz 3, 0(30)
lwz 12, 0(3)
lwz 12, 20(12)
mtctr 12
bctrl
lis 4, -32768
ori 4, 4, 0x50c0
lfs 1, 0(4)
lfs 2, 0(4)
lfs 3, 4(4)
lfs 4, 4(4)
addi 3, 4, 8
bl 0x800273cc
done:
lwz 3, 8(1)
lwz 0, 52(1)
mtlr 0
addi 1, 1, 48
b 0x80124328
'''

if __name__ == '__main__':
    ks=Ks(KS_ARCH_PPC, KS_MODE_PPC32 | KS_MODE_BIG_ENDIAN)
    code=bytes(ks.asm(SOURCE,0x80005000)[0])
    assert len(code)<=0xc0
    material='''
lwz 6, -23608(13)
cmplwi 6, 0
beq original
lwz 6, 56(6)
cmplwi 6, 0
beq original
lwz 6, 8(6)
cmpwi 6, 2
beq custom
cmpwi 6, 3
bne original
custom:
lis 6, -32768
ori 6, 6, 0x50c0
lwz 4, 12(6)
lfs 1, 16(6)
lfs 2, 20(6)
addi 5, 6, 24
original:
stwu 1, -64(1)
b 0x80182494
'''
    leaf=bytes(ks.asm(material,0x800050e0)[0])
    assert 0x800050e0+len(leaf)<=0x800051e4
    words=lambda data:[data[i:i+4].hex().upper() for i in range(0,len(data),4)]
    print(json.dumps({'words':words(code),'material':words(leaf),
                     'hook':bytes(ks.asm('bl 0x80005000',0x801a1e64)[0]).hex().upper(),
                     'materialHook':bytes(ks.asm('b 0x800050e0',0x80182490)[0]).hex().upper()}))
