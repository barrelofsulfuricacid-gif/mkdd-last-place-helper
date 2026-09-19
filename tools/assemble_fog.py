"""Reproduce the retail GM4E01 rev 0 distance-fog argument hook.

Only native fog-enabled materials in GP/VS are affected. No screen overlay.
Preserves the original near/far projection parameters and function prologue.
"""
import json
from keystone import Ks, KS_ARCH_PPC, KS_MODE_PPC32, KS_MODE_BIG_ENDIAN

SOURCE='''
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

if __name__ == '__main__':
    ks=Ks(KS_ARCH_PPC, KS_MODE_PPC32 | KS_MODE_BIG_ENDIAN)
    leaf=bytes(ks.asm(SOURCE,0x800050e0)[0])
    assert len(leaf)==76
    print(json.dumps({'material':[leaf[i:i+4].hex().upper() for i in range(0,len(leaf),4)],
                     'materialHook':bytes(ks.asm('b 0x800050e0',0x80182490)[0]).hex().upper()}))
