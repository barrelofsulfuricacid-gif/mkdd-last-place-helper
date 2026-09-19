"""Read-only retail ISO validation. Requires unicorn.

node tests/race-options.cjs /tmp/race-options.json
python tests/race_options_ppc.py /path/to/GM4E01.iso /tmp/race-options.json

Runs the fog hook and the retail material setter, plus native kart-class
initialization. The virtual getFog accessor is represented by a tiny PPC
fixture. This is not a live Dolphin gameplay or GPU rasterization test.
"""
import json, struct, sys
from unicorn import Uc, UC_ARCH_PPC, UC_MODE_PPC32, UC_MODE_BIG_ENDIAN
from unicorn import ppc_const as p

u=Uc(UC_ARCH_PPC,UC_MODE_PPC32|UC_MODE_BIG_ENDIAN)
u.mem_map(0x80000000,0x1800000)
with open(sys.argv[1],'rb') as disc:
    h=disc.read(0x440)
    assert h[:6]==b'GM4E01' and h[7]==0 and h[0x1c:0x20]==bytes.fromhex('C2339F3D')
    doloff=struct.unpack_from('>I',h,0x420)[0];disc.seek(doloff);dol=disc.read(0x100)
    for i in range(18):
        offset,addr,size=[struct.unpack_from('>I',dol,base+i*4)[0] for base in (0,0x48,0x90)]
        if size:disc.seek(doloff+offset);u.mem_write(addr,disc.read(size))
W=lambda a,v:u.mem_write(a,struct.pack('>I',v))
F=lambda a,v:u.mem_write(a,struct.pack('>f',v))
read_float=lambda a:struct.unpack('>f',u.mem_read(a,4))[0]
reg=lambda n:getattr(p,f'UC_PPC_REG_{n}')
freg=lambda n:getattr(p,f'UC_PPC_REG_FPR{n}')
setf=lambda n,v:u.reg_write(freg(n),struct.unpack('>Q',struct.pack('>d',v))[0])
getf=lambda n:struct.unpack('>d',struct.pack('>Q',u.reg_read(freg(n))))[0]
f32=lambda v:struct.unpack('>f',struct.pack('>f',v))[0]
SDA,SDA2,STACK=0x803d1420,0x803d45a0,0x817f0000
MANAGER,INFO,DRAWER,ORTHO,VTABLE,PORT,HUD=0x81000000,0x81001000,0x81002000,0x81003000,0x81004000,0x81006000,0x81007000
assert bytes(u.mem_read(0x80005000,0x12c))==bytes(0x12c)
assert bytes(u.mem_read(0x801a1e64,4)).hex()=='4bf824c5'
assert bytes(u.mem_read(0x80182490,4)).hex()=='9421ffc0'
for address,expected in ((0x80361d44,'3f666666'),(0x80361d48,'3f800000'),(0x80361d4c,'3f933333'),(0x803d1894,'43480000')):
    assert bytes(u.mem_read(address,4)).hex()==expected
guards=[(addr,bytes(u.mem_read(addr,16))) for addr in (0x80004ff0,0x80005130)]
W(MANAGER+56,INFO);W(DRAWER,ORTHO);W(ORTHO,VTABLE);W(VTABLE+20,PORT)
u.reg_write(p.UC_PPC_REG_MSR,0x2000)

def reset():
    # The hook-only and full-function checks use different stop addresses.
    u.ctl_remove_cache(0x80182490,0x80182560)
    for n in range(1,32):u.reg_write(reg(n),0xcafe0000+n)
    u.reg_write(reg(1),STACK);u.reg_write(reg(2),SDA2);u.reg_write(reg(13),SDA);u.reg_write(reg(30),DRAWER)
    W(SDA-23608,MANAGER);W(MANAGER+56,INFO)

def install(fixture):
    for line in fixture['code'].splitlines():
        address,value=[int(x,16) for x in line.split()]
        assert address&0xfe000000==0x04000000
        address=0x80000000|(address&0x1ffffff)
        assert (0x800050cc<=address<0x8000512c) or address in (0x80182490,0x80361d44,0x80361d48,0x80361d4c,0x803d1894)
        W(address,value)
    for start,end in ((0x80005000,0x80005130),(0x801a1e64,0x801a1e68),(0x80182490,0x80182494)):
        u.ctl_remove_cache(start,end)
    for address,data in guards:assert bytes(u.mem_read(address,16))==data

# Synthetic J3D model with two materials: fog-enabled and intentionally unfogged.
MODEL,TABLE,MAT,PE,VT,ACCESSOR,FOG,STOP=0x81010000,0x81011000,0x81012000,0x81013000,0x81014000,0x81015000,0x81016000,0x81017000
W(MODEL+0x60,TABLE);u.mem_write(MODEL+0x5c,struct.pack('>H',2))
for i in range(2):
    W(TABLE+i*4,MAT+i*0x100);W(MAT+i*0x100+0x34,PE+i*0x100)
    W(PE+i*0x100,VT);W(PE+i*0x100+4,FOG+i*0x100)
W(VT+0x30,ACCESSOR)
W(ACCESSOR,0x80630004);W(ACCESSOR+4,0x4e800020) # lwz r3,4(r3); blr
u.mem_write(0x81008000,bytes.fromhex('11223344'))

fixtures=json.load(open(sys.argv[2],encoding='utf8'))
material_cases=native_material_cases=speed_cases=0
for fixture in fixtures:
    install(fixture)
    if 'fog' in fixture:
        fog=fixture['fog']
        for mode in range(9):
            active=mode in (2,3);reset();W(INFO+8,mode)
            # The material hook must preserve native args outside GP/VS.
            reset();W(INFO+8,mode);u.reg_write(reg(4),5);u.reg_write(reg(5),0x81008000)
            for n,value in enumerate((123.,456.,10.,200000.),1):setf(n,value)
            u.emu_start(0x80182490,0x80182494,count=100)
            assert u.reg_read(reg(1))==STACK-64
            assert getf(3)==10. and getf(4)==200000.
            if active:
                assert u.reg_read(reg(4))==(0 if fog==0 else 2)
                assert u.reg_read(reg(5))==0x800050d8
                assert getf(1)==read_float(0x800050d0) and getf(2)==read_float(0x800050d4)
            else:
                assert (u.reg_read(reg(4)),u.reg_read(reg(5)),getf(1),getf(2))==(5,0x81008000,123.,456.)
            material_cases+=1
            # Execute the complete native setter, including actual material stores.
            reset();W(INFO+8,mode);u.reg_write(reg(3),MODEL)
            u.reg_write(reg(4),5);u.reg_write(reg(5),0x81008000)
            for n,value in enumerate((123.,456.,10.,200000.),1):setf(n,value)
            for n in range(28,32):setf(n,n+0.5)
            u.mem_write(FOG,b'\x02'+bytes(23));u.mem_write(FOG+0x100,bytes(24))
            u.reg_write(p.UC_PPC_REG_LR,STOP)
            u.emu_start(0x80182490,STOP,count=1000)
            assert u.reg_read(p.UC_PPC_REG_PC)==STOP and u.reg_read(reg(1))==STACK
            for n in range(14,32):assert u.reg_read(reg(n))==(DRAWER if n==30 else 0xcafe0000+n)
            for n in range(28,32):assert getf(n)==n+0.5
            assert bytes(u.mem_read(FOG+0x100,24))==bytes(24),'Do not force fog onto intentionally unfogged materials'
            expected_type=(0 if fog==0 else 2) if active else 5
            assert u.mem_read(FOG,1)[0]==expected_type
            start,end=(read_float(0x800050d0),read_float(0x800050d4)) if active else (123.,456.)
            assert (read_float(FOG+4),read_float(FOG+8),read_float(FOG+12),read_float(FOG+16))==(start,end,10.,200000.)
            assert bytes(u.mem_read(FOG+20,4))==bytes.fromhex('f0f2f4ff' if active else '11223344')
            assert bytes(u.mem_read(0x801a1e64,4)).hex()=='4bf824c5','HUD draw remains original'
            native_material_cases+=1

        for missing in ('manager','info'):
            reset();W(SDA-23608 if missing=='manager' else MANAGER+56,0)
            u.reg_write(reg(4),5);setf(1,123.)
            u.emu_start(0x80182490,0x80182494,count=100)
            assert u.reg_read(reg(4))==5 and getf(1)==123.
            material_cases+=1
    else:
        for kart_class in range(3):
            for setting in (40.,80.,100.,160.,200.):
                reset();u.reg_write(reg(3),0x80361d44);u.reg_write(reg(0),kart_class*4)
                u.reg_write(reg(5),0x81009000);u.reg_write(reg(29),0x8100a000)
                for i in range(4):F(0x81009050+i*4,setting+i)
                u.emu_start(0x8029d230,0x8029d270,count=100)
                multiplier=read_float(0x80361d44+kart_class*4)
                for i in range(4):assert read_float(0x8100a3f0+i*4)==f32((setting+i)*multiplier)
                assert read_float(0x803d1894)==f32(200*(fixture['speedCC']/150))
                speed_cases+=1
print(json.dumps({'status':'passed','native_fog_material_cases':native_material_cases,'fog_material_scope_cases':material_cases,
                  'native_speed_cases':speed_cases,'fog':'distance-only; no overlay; clear foreground',
                  'native_GPU_rasterization':'not run','live_Dolphin_gameplay':'not run'},indent=2))
