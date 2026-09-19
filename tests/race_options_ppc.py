"""Read-only retail ISO validation. Requires unicorn.

node tests/race-options.cjs /tmp/race-options.json
python tests/race_options_ppc.py /path/to/GM4E01.iso /tmp/race-options.json

Runs the new hooks, native J2DFillBox/color/vertex code, and native kart-class
initialization. GPU entry points and the paired-single identity helper are
stubbed; actual native FIFO vertex/color stores are captured. This is not a
live Dolphin gameplay or GPU rasterization test.
"""
import json, struct, sys
from unicorn import Uc, UC_ARCH_PPC, UC_MODE_PPC32, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import ppc_const as p

u=Uc(UC_ARCH_PPC,UC_MODE_PPC32|UC_MODE_BIG_ENDIAN)
u.mem_map(0x80000000,0x1800000);u.mem_map(0xcc008000,0x1000)
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
    for n in range(1,32):u.reg_write(reg(n),0xcafe0000+n)
    u.reg_write(reg(1),STACK);u.reg_write(reg(2),SDA2);u.reg_write(reg(13),SDA);u.reg_write(reg(30),DRAWER)
    W(SDA-23608,MANAGER);W(MANAGER+56,INFO)

def install(fixture):
    for line in fixture['code'].splitlines():
        address,value=[int(x,16) for x in line.split()]
        assert address&0xfe000000==0x04000000
        address=0x80000000|(address&0x1ffffff)
        assert (0x80005000<=address<0x8000512c) or address in (0x801a1e64,0x80182490,0x80361d44,0x80361d48,0x80361d4c,0x803d1894)
        W(address,value)
    for start,end in ((0x80005000,0x80005130),(0x801a1e64,0x801a1e68),(0x80182490,0x80182494)):
        u.ctl_remove_cache(start,end)
    for address,data in guards:assert bytes(u.mem_read(address,16))==data

events=[];fifo=[]
def returned():u.reg_write(p.UC_PPC_REG_PC,u.reg_read(p.UC_PPC_REG_LR))
def stub(machine,address,size,user):
    if address==PORT:
        assert u.reg_read(reg(3))==ORTHO
        events.append(('port',));returned()
    elif address==0x80124328:
        assert u.reg_read(reg(3))==HUD
        events.append(('hud',));returned()
    elif address==0x800a9714: # Paired-single helper only; unrelated to fog logic.
        addr=u.reg_read(reg(3))
        for i in range(12):F(addr+i*4,1.0 if i in (0,5,10) else 0.0)
        returned()
    elif address==0x800c1104:
        events.append(('blend',*[u.reg_read(reg(i)) for i in (3,4,5,6)]));returned()
    else:returned()
for target in (PORT,0x80124328,0x800a9714,0x800c1104,0x800c20d8,0x800bca50,0x800bdec4,0x800be01c):
    u.hook_add(UC_HOOK_CODE,stub,begin=target,end=target)
def capture(machine,access,address,size,value,user):
    if address==0xcc008000:fifo.append(value&0xffffffff)
u.hook_add(UC_HOOK_MEM_WRITE,capture,begin=0xcc008000,end=0xcc008003)

fixtures=json.load(open(sys.argv[2],encoding='utf8'))
material_cases=draw_cases=speed_cases=0
for fixture in fixtures:
    install(fixture)
    if 'fog' in fixture:
        fog=fixture['fog']
        for mode in range(9):
            active=mode in (2,3);reset();W(INFO+8,mode)
            u.reg_write(reg(3),HUD);events.clear();fifo.clear()
            u.emu_start(0x801a1e64,0x801a1e68,count=10000)
            assert u.reg_read(p.UC_PPC_REG_PC)==0x801a1e68
            assert u.reg_read(reg(1))==STACK
            for n in range(14,32):assert u.reg_read(reg(n))==(DRAWER if n==30 else 0xcafe0000+n)
            assert events[-1]==('hud',)
            if active:
                assert events[0]==('port',) and len(fifo)==16
                vertices=[tuple(struct.unpack('>f',struct.pack('>I',v))[0] for v in fifo[i:i+3]) for i in range(0,16,4)]
                assert vertices==[(0.,0.,0.),(1280.,0.,0.),(1280.,1280.,0.),(0.,1280.,0.)]
                alpha=int(255*(fog/100)**2+0.5)
                assert fifo[3::4]==[0xf0f2f400|alpha]*4
                if fog==100:
                    assert ('blend',0,1,0,15) in events,'Whiteout must replace destination pixels, not blend them through'
                elif alpha<255:assert ('blend',1,4,5,15) in events
            else:assert not fifo and events==[('hud',)]
            draw_cases+=1
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
print(json.dumps({'status':'passed','native_fog_draw_cases':draw_cases,'fog_material_scope_cases':material_cases,
                  'native_speed_cases':speed_cases,'whiteout':'opaque native quad covers full race viewport',
                  'native_GPU_rasterization':'not run','live_Dolphin_gameplay':'not run'},indent=2))
