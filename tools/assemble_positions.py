"""Print the per-position template. Requires keystone-engine (development only).

USA GM4E01 rev 0: hook SlotItem's shared epilogue, where r29 is rank - 1.
Keep code in [0x80005420,0x800054e4); use zero padding after the exception
stub's rfi for eight 80-byte tables in [0x80004d20,0x80004fa0).
These ranges and the original hook must be checked against the retail DOL.
Each table: u16 total, u16 padding, 19 (u16 exclusive limit, u8 item, u8 pad).
Zero total means return the stock selection. r28 is preserved by both native
RNG calls; the original lmw restores r26..r31 before returning to the caller.
"""
import json
from keystone import Ks, KS_ARCH_PPC, KS_MODE_PPC32, KS_MODE_BIG_ENDIAN

SOURCE = """
lwz 4, -23608(13)
lwz 4, 56(4)
lwz 5, 8(4)
cmpwi 5, 2
beq race
cmpwi 5, 3
bne done
race:
lha 5, 30(4)
cmpwi 5, 2
blt done
cmplwi 29, 7
bgt done
mulli 5, 29, 80
lis 28, -32768
ori 28, 28, 0x4d20
add 28, 28, 5
lhz 4, 0(28)
cmpwi 4, 0
beq done
li 3, 0
bl 0x801ed474
lhz 4, 0(28)
addi 4, 4, -1
bl 0x801ed138
addi 4, 28, 4
loop:
lhz 5, 0(4)
cmplw 3, 5
blt picked
addi 4, 4, 4
b loop
picked:
lbz 3, 2(4)
done:
lmw 26, 40(1)
b 0x8020cbcc
"""

if __name__ == '__main__':
    ks = Ks(KS_ARCH_PPC, KS_MODE_PPC32 | KS_MODE_BIG_ENDIAN)
    code = bytes(ks.asm(SOURCE, 0x80005420)[0])
    assert len(code) <= 188
    print(json.dumps([code[i:i+4].hex().upper() for i in range(0, len(code), 4)]))
