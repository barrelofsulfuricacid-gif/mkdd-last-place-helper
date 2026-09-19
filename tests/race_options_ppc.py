"""Read-only GM4E01 rev 0 validation: mist hook fixtures and native speed setup.
node tests/race-options.cjs /tmp/race-options.json
python tests/race_options_ppc.py /path/to/GM4E01.iso /tmp/race-options.json
Requires unicorn. Particle creation/calc are call fixtures, not GPU simulation.
"""
import json,struct,sys
from unicorn import Uc,UC_ARCH_PPC,UC_MODE_PPC32,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
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
R=lambda a:struct.unpack('>I',u.mem_read(a,4))[0]
read_float=lambda a:struct.unpack('>f',u.mem_read(a,4))[0]
reg=lambda n:getattr(p,f'UC_PPC_REG_{n}')
f32=lambda v:struct.unpack('>f',struct.pack('>f',v))[0]
SDA,SDA2,STACK=0x803d1420,0x803d45a0,0x817f0000
MANAGER,INFO,CTRL,EMITTER=0x81000000,0x81001000,0x81002000,0x81003000
assert bytes(u.mem_read(0x80004fa0,0x244))==bytes(0x244)
assert R(0x80189ea8)==0x48073ba9
guards=[(a,bytes(u.mem_read(a,n))) for a,n in ((0x80004f90,16),(0x800051e4,16),(0x80182490,4),(0x801a1e64,4))]
events=[];fail=False;calc=0
def stub(machine,addr,size,user):
    global calc
    assert u.reg_read(reg(3))==MANAGER
    if addr==0x801fd680:
        assert u.reg_read(reg(4))==0x8cf
        pos=u.reg_read(reg(5));events.append(tuple(read_float(pos+4*n) for n in range(3)))
        u.reg_write(reg(3),0 if fail else EMITTER)
    else:calc+=1
    u.reg_write(p.UC_PPC_REG_PC,u.reg_read(p.UC_PPC_REG_LR))
for addr in (0x801fd680,0x801fda50):u.hook_add(UC_HOOK_CODE,stub,begin=addr,end=addr)
u.reg_write(p.UC_PPC_REG_MSR,0x2000)
def reset():
    global calc
    for n in range(1,32):u.reg_write(reg(n),0xcafe0000+n)
    u.reg_write(reg(1),STACK);u.reg_write(reg(2),SDA2);u.reg_write(reg(13),SDA);u.reg_write(reg(3),MANAGER)
    W(SDA-23608,MANAGER);W(MANAGER+56,INFO);W(SDA-20120,CTRL)
    for i in range(4):
        cam=0x81010000+i*0x1000;W(CTRL+0x200+i*4,cam)
        for n in range(3):F(cam+0x1f4+4*n,1000*i+100*n)
    u.mem_write(EMITTER,bytes([0x5a])*0x140)
    events.clear();calc=0
def install(fixture):
    W(0x80189ea8,0x48073ba9)
    for line in fixture['code'].splitlines():
        a,v=[int(x,16) for x in line.split()]
        assert a&0xfe000000==0x04000000
        a=0x80000000|(a&0x1ffffff)
        assert 0x80004fa0<=a<0x80005100 or 0x80005180<=a<=0x800051a0 or a in (0x80189ea8,0x80361d44,0x80361d48,0x80361d4c,0x803d1894)
        W(a,v)
    u.ctl_remove_cache(0x80004fa0,0x80005100);u.ctl_remove_cache(0x80189ea8,0x80189eb0)
    for a,data in guards:assert bytes(u.mem_read(a,len(data)))==data
def run():
    u.emu_start(0x80189ea8,0x80189eac,count=2000)
    assert calc==1 and u.reg_read(reg(1))==STACK
    for n in range(14,32):assert u.reg_read(reg(n))==0xcafe0000+n
fixtures=json.load(open(sys.argv[2],encoding='utf8'))
mist_cases=speed_cases=0
for fixture in fixtures:
    install(fixture)
    if 'fog' in fixture:
        fog=fixture['fog']
        for mode in range(9):
            for count in range(6):
                for fail in (False,True):
                    for frame in range(20):
                        reset();W(INFO+8,mode);u.mem_write(INFO+32,struct.pack('>h',count));W(0x800051bc,frame)
                        run();active=fog>0 and mode in (2,3) and 1<=count<=4 and frame==19
                        assert events==([(i*1000.,i*1000.+400.,i*1000.+200.) for i in range(count)] if active else [])
                        if active and not fail:
                            assert R(EMITTER+36)==1 and read_float(EMITTER+40)==2
                            assert int.from_bytes(u.mem_read(EMITTER+82,2),'big')==180
                            assert int.from_bytes(u.mem_read(EMITTER+84,2),'big')==1800
                            assert read_float(EMITTER+176)==read_float(EMITTER+180)==180
                            assert R(EMITTER+184)==R(0x80005198)
                        else:assert bytes(u.mem_read(EMITTER,0x140))==bytes([0x5a])*0x140
                        mist_cases+=1
        for missing in ('manager','info','ctrl','camera'):
            reset();W(INFO+8,2);u.mem_write(INFO+32,struct.pack('>h',1));W(0x800051bc,19)
            W({'manager':SDA-23608,'info':MANAGER+56,'ctrl':SDA-20120,'camera':CTRL+0x200}[missing],0)
            run();assert not events;mist_cases+=1
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
print(json.dumps({'status':'passed','mist_hook_fixture_cases':mist_cases,'native_speed_cases':speed_cases,'GPU_rasterization':'not simulated'},indent=2))
