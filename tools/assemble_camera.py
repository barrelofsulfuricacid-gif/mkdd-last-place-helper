"""Assemble the GM4E01 rev 0 OutView camera override (before C_MTXLookAt).

Uses each camera's target kart, its unscaled player matrix and native size.
Only normal GP/VS/Time Trial cameras reach this hook. No model hiding.
"""
import json
from keystone import Ks, KS_ARCH_PPC, KS_MODE_PPC32, KS_MODE_BIG_ENDIAN

SOURCE = '''
lwz 3, -23608(13)
cmplwi 3, 0
beq original
lwz 3, 56(3)
cmplwi 3, 0
beq original
lwz 3, 8(3)
addi 3, 3, -1
cmplwi 3, 2
bgt original
lwz 4, 0(31)
cmplwi 4, 0
beq original
lis 3, -32768
lfs 0, 0x50b0(3)
lfs 1, 0x568(4)
fmuls 0, 0, 1
lfs 1, 0x50b4(3)
fmuls 1, 1, 0
lfs 2, 0x50b8(3)
fmuls 2, 2, 0
lfs 3, 0x50bc(3)
addi 4, 4, 0x140
addi 5, 31, 0x1e8
addi 6, 31, 0x1f4
addi 7, 1, 0x80
li 8, 3
axis:
lfs 4, 4(4)
lfs 5, 8(4)
lfs 6, 12(4)
fmadds 6, 4, 1, 6
fmadds 6, 5, 2, 6
stfs 6, 0(5)
fmadds 6, 5, 3, 6
stfs 6, 0(6)
stfs 4, 0(7)
addi 4, 4, 16
addi 5, 5, 4
addi 6, 6, 4
addi 7, 7, 4
addi 8, 8, -1
cmpwi 8, 0
bne axis
original:
addi 3, 31, 0x80
b 0x802b7488
'''

if __name__ == '__main__':
    ks = Ks(KS_ARCH_PPC, KS_MODE_PPC32 | KS_MODE_BIG_ENDIAN)
    code = bytes(ks.asm(SOURCE, 0x80004fa0)[0])
    assert 0x80004fa0 + len(code) <= 0x800050b0
    print(json.dumps({'words': [code[i:i+4].hex().upper() for i in range(0, len(code), 4)],
                      'hook': bytes(ks.asm('b 0x80004fa0', 0x802b7484)[0]).hex().upper()}))
