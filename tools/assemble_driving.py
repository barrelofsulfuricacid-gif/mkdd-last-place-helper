"""Assemble the GM4E01 revision 0 race HUD and terrain-rescue hooks.

The standalone page embeds these words so offline generation needs no assembler.
Run with keystone-engine to reproduce the templates printed below.
"""
import json
from keystone import Ks, KS_ARCH_PPC, KS_MODE_BIG_ENDIAN, KS_MODE_PPC32

# DoRescueCrl, just after the game opens the lap checker's warp. The rank is
# sampled once. 254 is outside the native phase-2 timer range of 0..100.
RESCUE_SELECT = """
lbz 0, 0x75(30)
cmplwi 0, 4
beq original
lwz 5, -0x5c38(13)
lwz 6, 0x38(5)
lwz 7, 8(6)
addi 7, 7, -1
cmplwi 7, 2
bgt original
lbz 7, 0x5b3(31)
cmplwi 7, 7
bgt original
slwi 7, 7, 2
add 5, 5, 7
lwz 5, 0x48(5)
cmplwi 5, 0
beq original
lwz 5, 0x88(5)
addi 5, 5, -1
cmplwi 5, 7
bgt original
lis 7, -32768
lwz 7, 0x42dc(7)
srw 7, 7, 5
andi. 7, 7, 1
beq original
li 5, 2
stb 5, 0x76(30)
li 5, 254
stb 5, 0x77(30)
b 0x802c0744
original:
b 0x802bfce4
"""

# Give the race checker a frame to record the old sector. On the next
# update enter the normal relocation/AI/warp-end path, skipping both wipes.
RESCUE_WARP = """
lbz 3, 0x77(30)
cmplwi 3, 254
bne original
b 0x802c033c
original:
b 0x802c0028
"""

# SetPose(1) has already chosen a checkpoint or the game's fallback.
# Remove its 1800-unit lift and leave 30 units for suspension to settle.
RESCUE_HEIGHT = """
lbz 0, 0x77(30)
cmplwi 0, 254
bne original
lfs 1, 0x54(1)
lfs 0, -0x27cc(2)
fsubs 1, 1, 0
lfs 0, -0x277c(2)
fadds 1, 1, 0
stfs 1, 0x54(1)
original:
lwz 3, -0x4e98(13)
b 0x802becf8
"""

# The following tick can run the stock drop/ground-contact logic immediately.
RESCUE_DROP = """
lbz 0, 0x77(30)
cmplwi 0, 254
li 0, 0
bne original
li 0, 10
original:
b 0x802c059c
"""

# Optional downward tilt. r3 still holds 0x80000000 in the camera axis loop.
CAMERA_TILT = """
fmadds 6, 5, 3, 6
lfs 7, 0x4c68(3)
fmadds 6, 4, 7, 6
b 0x800052a8
"""

# Race2D::draw has just installed its orthographic projection. Transform
# each normal camera's native viewport into that HUD coordinate system.
# Draw two flat boxes, then replay the displaced GXClearVtxDesc call.
DRIFT_HUD = """
stwu 1, -0x50(1)
mflr 0
stw 0, 0x54(1)
stmw 25, 0x34(1)
lwz 3, -0x5c38(13)
lwz 3, 0x38(3)
lwz 4, 8(3)
addi 4, 4, -1
cmplwi 4, 2
bgt done
lha 29, 0x20(3)
addi 4, 29, -1
cmplwi 4, 3
bgt done
lwz 28, -0x4e98(13)
cmplwi 28, 0
beq done
addi 28, 28, 0x200
lwz 27, 0x1b4(15)
lis 26, -32768
addi 26, 26, 0x4c20
lis 0, 0x4330
stw 0, 0x10(1)
camera:
lwz 8, 0(28)
cmplwi 8, 0
beq next
lbz 0, 0xe1(8)
cmpwi 0, 0
bne next
lwz 3, 0(8)
cmplwi 3, 0
beq next
lwz 0, 0x574(3)
andi. 0, 0, 3
beq next
lbz 0, 0x5c7(3)
cmplwi 0, 2
bgt next
slwi 25, 0, 3
add 25, 26, 25
li 5, 0
axis:
add 6, 8, 5
lwz 0, 0xf4(6)
stw 0, 0x14(1)
lfd 0, 0x10(1)
lfd 1, 0(26)
fsub 0, 0, 1
lfs 1, 0x140(6)
add 7, 26, 5
lfs 2, 8(7)
fmadds 0, 1, 2, 0
add 7, 27, 5
lfs 1, 4(7)
lfs 2, 12(7)
fsubs 0, 0, 1
fsubs 2, 2, 1
fdivs 0, 0, 2
lfs 1, 0xbc(7)
lfs 2, 0xc4(7)
fsubs 2, 2, 1
fmadds 0, 0, 2, 1
addi 7, 1, 0x18
stfsx 0, 7, 5
addi 5, 5, 4
cmpwi 5, 8
blt axis
lfs 1, 0x18(1)
lfs 0, 0x10(26)
fsubs 1, 1, 0
stfs 1, 0x18(1)
lfs 2, 0x1c(1)
lfs 3, 0x14(26)
lfs 4, 0x18(26)
addi 3, 26, 0x1c
bl 0x800273cc
lfs 0, 0x20(26)
lfs 1, 0x18(1)
lfs 2, 0x1c(1)
fadds 1, 1, 0
fadds 2, 2, 0
lfs 3, 0x28(25)
lfs 4, 0x24(26)
addi 3, 25, 0x2c
bl 0x800273cc
next:
addi 28, 28, 4
addi 29, 29, -1
cmpwi 29, 0
bne camera
done:
lmw 25, 0x34(1)
lwz 0, 0x54(1)
mtlr 0
addi 1, 1, 0x50
b 0x800bca18
"""

# Keystone treats some absolute PPC targets as signed immediates. Encode
# external branches from their final address after local labels are resolved.
def assemble(base, source):
    ks = Ks(KS_ARCH_PPC, KS_MODE_PPC32 | KS_MODE_BIG_ENDIAN)
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    external = {}
    offset = 0
    for i, line in enumerate(lines):
        if line.startswith(('b 0x', 'bl 0x')):
            op, target = line.split()
            delta = int(target, 16) - (base + offset)
            assert delta % 4 == 0 and -0x2000000 <= delta < 0x2000000
            external[offset] = 0x48000000 | (delta & 0x03fffffc) | int(op == 'bl')
            lines[i] = 'nop'
        if not line.endswith(':'):
            offset += 4
    code = bytearray(ks.asm('\n'.join(lines), base)[0])
    for offset, word in external.items():
        code[offset:offset + 4] = word.to_bytes(4, 'big')
    return [code[i:i+4].hex().upper() for i in range(0, len(code), 4)]

if __name__ == '__main__':
    for name, base, end, source in [
        ('RESCUE_SELECT', 0x80004220, 0x800042dc, RESCUE_SELECT),
        ('RESCUE_WARP', 0x80004320, 0x80004340, RESCUE_WARP),
        ('RESCUE_HEIGHT', 0x80004340, 0x80004380, RESCUE_HEIGHT),
        ('RESCUE_DROP', 0x80004380, 0x800043e4, RESCUE_DROP),
        ('CAMERA_TILT', 0x80004c70, 0x80004ce4, CAMERA_TILT),
        ('DRIFT_HUD', 0x80004a20, 0x80004be4, DRIFT_HUD),
    ]:
        words = assemble(base, source)
        assert base + 4 * len(words) <= end
        print(f'  const {name}={json.dumps(words, separators=(",", ":"))};')
