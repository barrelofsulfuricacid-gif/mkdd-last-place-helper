"""Reproduce USA GM4E01 rev 0 kart scaling (keystone-engine).

Preserve native display scaling, then scale all 13 display matrices about the
body center. Wheel translations must scale too, not just each mesh's axes.
Restore a separate body matrix for ground contacts after copying the render
matrix to the models. Optional physics scaling adjusts native initialized
mass, inertia, dimensions and kart radius. Lightning state stays unchanged.
"""
import json
from keystone import Ks, KS_ARCH_PPC, KS_MODE_PPC32, KS_MODE_BIG_ENDIAN

SOURCE = '''
stwu 1, -32(1)
mflr 0
stw 0, 36(1)
lwz 8, 0(3)
stw 8, 8(1)
bl 0x802d3660
lwz 8, 8(1)
addi 5, 8, 0x19c
addi 6, 1, 0x6c
li 0, 12
mtctr 0
save:
lwzu 7, 4(5)
stwu 7, 4(6)
bdnz save
lis 5, -32768
lfs 1, 0x41d0(5)
addi 4, 8, 0x1a0
mr 3, 4
bl matrix
lbz 0, 0x5b3(8)
slwi 0, 0, 4
lwz 12, -20120(13)
addi 12, 12, 0xc0
add 12, 12, 0
li 11, 4
wheel:
lwz 9, 0(12)
addi 3, 9, 0x158
bl matrix
addi 3, 9, 0x1e8
bl matrix
addi 3, 9, 0x248
bl matrix
addi 12, 12, 4
addi 11, 11, -1
cmpwi 11, 0
bne wheel
lwz 0, 36(1)
mtlr 0
addi 1, 1, 32
blr
matrix:
mr 5, 3
mr 6, 4
li 0, 3
mtctr 0
row:
lfs 0, 0(5)
fmuls 0, 0, 1
stfs 0, 0(5)
lfs 0, 4(5)
fmuls 0, 0, 1
stfs 0, 4(5)
lfs 0, 8(5)
fmuls 0, 0, 1
stfs 0, 8(5)
lfs 0, 12(5)
lfs 2, 12(6)
fsubs 0, 0, 2
fmuls 0, 0, 1
fadds 0, 0, 2
stfs 0, 12(5)
addi 5, 5, 16
addi 6, 6, 16
bdnz row
blr
'''
SHADOW = '''
lis 4, -32768
lfs 1, 0x41d0(4)
lwz 3, 0x28(30)
lfs 0, 0xa8(3)
fmuls 0, 0, 1
stfs 0, 0xa8(3)
lfs 0, 0xac(3)
fmuls 0, 0, 1
stfs 0, 0xac(3)
lwz 3, 0x20(30)
b 0x802d3eb4
'''
# The caller's 0x50..0x7f scratch matrix is dead after its pose calculations.
# Restore the stock body matrix after copying the visual matrix to both drivers.
# The ground-contact path then sees the physical multiplier (1 when disabled).
RESTORE = '''
stwu 1, -16(1)
mflr 0
stw 0, 20(1)
bl 0x80183c08
lis 3, -32768
lfs 1, 0x41d4(3)
addi 3, 1, 0x60
addi 4, 30, 0x1a0
li 0, 3
mtctr 0
row:
lfs 0, 0(3)
fmuls 0, 0, 1
stfs 0, 0(4)
lfs 0, 4(3)
fmuls 0, 0, 1
stfs 0, 4(4)
lfs 0, 8(3)
fmuls 0, 0, 1
stfs 0, 8(4)
lwz 0, 12(3)
stw 0, 12(4)
addi 3, 3, 16
addi 4, 4, 16
bdnz row
lwz 0, 20(1)
mtlr 0
addi 1, 1, 16
blr
'''
# Run once after native body initialization, not every frame (no compounding).
PHYSICS = '''
lis 3, -32768
lfs 1, 0x41d4(3)
fmuls 2, 1, 1
fmuls 3, 2, 1
fmuls 2, 2, 3
lfs 0, 0x3a4(29)
fmuls 0, 0, 3
stfs 0, 0x3a4(29)
'''
for offset in (0x230, 0x234, 0x238):
    PHYSICS += f'lfs 0, {offset}(29)\nfmuls 0, 0, 2\nstfs 0, {offset}(29)\n'
for offset in (0x320, 0x324, 0x328, 0x3a8):
    PHYSICS += f'lfs 0, {offset}(29)\nfmuls 0, 0, 1\nstfs 0, {offset}(29)\n'
PHYSICS += 'lmw 28, 32(1)\nb 0x8029d6c4\n'
ks = Ks(KS_ARCH_PPC, KS_MODE_PPC32 | KS_MODE_BIG_ENDIAN)
def words(source, address):
    data = bytes(ks.asm(source, address)[0])
    return [data[i:i+4].hex().upper() for i in range(0, len(data), 4)]

if __name__ == '__main__':
    segments = [(0x80003f20,SOURCE,0x80004040), (0x80004040,SHADOW,0x80004080),
                (0x80004080,RESTORE,0x80004100), (0x80004100,PHYSICS,0x800041d0)]
    for address,source,end in segments:
        data=words(source,address)
        assert address+len(data)*4<=end
        print(hex(address),json.dumps(data))
    for address,asm in [(0x802d3dc4,'bl 0x80003f20'),(0x802d3eb0,'b 0x80004040'),
                        (0x802d3ec4,'bl 0x80004080'),(0x8029d6c0,'b 0x80004100')]:
        print(hex(address),words(asm,address))
