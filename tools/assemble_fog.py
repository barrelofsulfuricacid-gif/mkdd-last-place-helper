"""Reproduce the GM4E01 revision 0 particle-mist hook (keystone-engine + capstone)."""
import json,struct
from keystone import Ks,KS_ARCH_PPC,KS_MODE_PPC32,KS_MODE_BIG_ENDIAN
from capstone import Cs,CS_ARCH_PPC,CS_MODE_32,CS_MODE_BIG_ENDIAN
BASE,CONFIG,HOOK=0x80004fa0,0x80005180,0x80189ea8
SOURCE='''
stwu 1,-64(1)
mflr 0
stw 0,68(1)
stmw 25,36(1)
mr 31,3
lwz 4,-23608(13)
cmplwi 4,0
beq done
lwz 4,56(4)
cmplwi 4,0
beq done
lwz 5,8(4)
cmpwi 5,2
beq active
cmpwi 5,3
bne done
active:
lha 29,32(4)
cmpwi 29,1
blt done
cmpwi 29,4
bgt done
lwz 27,-20120(13)
cmplwi 27,0
beq done
lis 30,-32768
ori 30,30,0x5180
lwz 4,60(30)
addi 4,4,1
cmpwi 4,20
blt counter
li 4,0
counter:
stw 4,60(30)
cmpwi 4,0
bne done
li 28,0
loop:
slwi 4,28,2
add 4,27,4
lwz 26,512(4)
cmplwi 26,0
beq next
lfs 0,500(26)
stfs 0,8(1)
lfs 0,504(26)
lfs 1,0(30)
fadds 0,0,1
stfs 0,12(1)
lfs 0,508(26)
stfs 0,16(1)
mr 3,31
li 4,2255
addi 5,1,8
bl 0x801fd680
cmplwi 3,0
beq next
li 0,1
stw 0,36(3)
lfs 0,4(30)
stfs 0,40(3)
li 0,180
sth 0,82(3)
li 0,1800
sth 0,84(3)
lfs 0,8(30)
stfs 0,4(3)
lfs 0,12(30)
stfs 0,52(3)
stfs 0,56(3)
stfs 0,60(3)
lfs 0,16(30)
stfs 0,68(3)
lfs 0,20(30)
stfs 0,176(3)
stfs 0,180(3)
lwz 0,24(30)
stw 0,184(3)
lwz 0,28(30)
stw 0,264(3)
lwz 0,32(30)
stw 0,268(3)
next:
addi 28,28,1
cmpw 28,29
blt loop
done:
mr 3,31
lmw 25,36(1)
lwz 0,68(1)
mtlr 0
addi 1,1,64
b 0x801fda50
'''

def branch(pc,target,link=False):
    delta=target-pc
    assert delta%4==0 and -0x2000000<=delta<0x2000000
    return 0x48000000|(delta&0x03fffffc)|int(link)

if __name__=='__main__':
    code=bytearray(Ks(KS_ARCH_PPC,KS_MODE_PPC32|KS_MODE_BIG_ENDIAN).asm(SOURCE,BASE)[0])
    # Keystone's label resolution can mis-base numeric external branch operands.
    calls=[(i.address,i.mnemonic) for i in Cs(CS_ARCH_PPC,CS_MODE_32|CS_MODE_BIG_ENDIAN).disasm(code,BASE) if i.mnemonic in ('bl','b')]
    assert len(calls)==2 and len(code)==352
    for (pc,mnemonic),target in zip(calls,(0x801fd680,0x801fda50)):
        struct.pack_into('>I',code,pc-BASE,branch(pc,target,mnemonic=='bl'))
    print(json.dumps({'mist':[code[i:i+4].hex().upper() for i in range(0,len(code),4)],'hook':f'{branch(HOOK,BASE,True):08X}'}))
