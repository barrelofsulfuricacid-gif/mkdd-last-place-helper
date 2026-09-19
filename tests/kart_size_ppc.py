"""Read-only USA rev 0 retail verification; requires unicorn, not a live race.

node tests/kart-size.cjs /tmp/kart-size.json
python tests/kart_size_ppc.py /path/to/GM4E01.iso /tmp/kart-size.json
"""
import json,math,struct,sys
from unicorn import Uc,UC_ARCH_PPC,UC_MODE_PPC32,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn import ppc_const as p
u=Uc(UC_ARCH_PPC,UC_MODE_PPC32|UC_MODE_BIG_ENDIAN)
u.mem_map(0x80000000,0x1800000)
with open(sys.argv[1],'rb') as disc:
    h=disc.read(0x440)
    assert h[:6]==b'GM4E01' and h[7]==0 and h[0x1c:0x20]==bytes.fromhex('C2339F3D')
    doloff=struct.unpack_from('>I',h,0x420)[0];disc.seek(doloff);dol=disc.read(0x100)
    for i in range(18):
        off,addr,size=[struct.unpack_from('>I',dol,b+i*4)[0] for b in (0,0x48,0x90)]
        if size:disc.seek(doloff+off);u.mem_write(addr,disc.read(size))
W=lambda a,v:u.mem_write(a,struct.pack('>I',v))
F=lambda a,v:u.mem_write(a,struct.pack('>f',v))
R=lambda a:struct.unpack('>I',u.mem_read(a,4))[0]
RF=lambda a:struct.unpack('>f',u.mem_read(a,4))[0]
reg=lambda n:getattr(p,f'UC_PPC_REG_{n}')
f32=lambda x:struct.unpack('>f',struct.pack('>f',x))[0]
setf=lambda n,v:u.reg_write(getattr(p,f'UC_PPC_REG_FPR{n}'),struct.unpack('>Q',struct.pack('>d',v))[0])
SDA,SDA2,STACK=0x803d1420,0x803d45a0,0x817e0000
CTRL,DISP,BODY,SHADOW,DRIVER=0x81000000,0x81001000,0x81002000,0x81003000,0x81004000
SUS=[0x81100000+i*0x1000 for i in range(32)]
assert bytes(u.mem_read(0x80003f20,0x2b8))==bytes(0x2b8)
original_hooks={0x802d3dc4:0x4bfff89d,0x802d3eb0:0x807e0020,0x802d3ec4:0x4beafd45,0x8029d6c0:0xbb810020}
for a,w in original_hooks.items():assert R(a)==w,(hex(a),hex(R(a)))
walls={R(0x803636d4+i*4)+4:RF(R(0x803636d4+i*4)+4) for i in range(21)}
object_radii=[RF(0x80353a74+i*4) for i in range(21)]
assert object_radii==[75,90,75,65,75,65,90,90,75,65,75,65,75,65,75,65,65,65,90,90,100]
guards=[(a,bytes(u.mem_read(a,8))) for a in (0x80003f18,0x800041dc)]
u.reg_write(p.UC_PPC_REG_MSR,0x2000)
W(SDA-20120,CTRL);W(DISP,BODY);W(BODY+0x28,SHADOW);W(BODY+0x20,DRIVER)
for i,a in enumerate(SUS):W(CTRL+0xc0+i*4,a)
captured=[]
def copy_model(machine,address,size,user):
    assert u.reg_read(reg(3))==DRIVER
    captured.append(bytes(u.mem_read(u.reg_read(reg(4)),48)))
    u.reg_write(p.UC_PPC_REG_PC,u.reg_read(p.UC_PPC_REG_LR))
u.hook_add(UC_HOOK_CODE,copy_model,begin=0x80183c08,end=0x80183c08)
def allow_collision(machine,address,size,user):
    u.reg_write(reg(3),0);u.reg_write(p.UC_PPC_REG_PC,u.reg_read(p.UC_PPC_REG_LR))
u.hook_add(UC_HOOK_CODE,allow_collision,begin=0x802c5e50,end=0x802c5e50)
def stop_collision(machine,address,size,user):u.emu_stop()
for a in (0x8029c64c,0x8029ca24):u.hook_add(UC_HOOK_CODE,stop_collision,begin=a,end=a)
def reset():
    for n in range(1,32):u.reg_write(reg(n),0xcafe0000+n)
    for n,v in ((1,STACK),(2,SDA2),(13,SDA),(3,DISP),(30,BODY)):u.reg_write(reg(n),v)
def run(start,end):
    u.emu_start(start,end,count=10000)
    assert u.reg_read(p.UC_PPC_REG_PC)==end,hex(u.reg_read(p.UC_PPC_REG_PC))
def close(actual,expected):assert math.isclose(actual,expected,rel_tol=3e-6,abs_tol=3e-4),(actual,expected)
def matrix(a):return list(struct.unpack('>12f',u.mem_read(a,48)))
def install(fixture):
    # Removing an option means a fresh game, not leaving old hooks installed.
    for a,w in original_hooks.items():W(a,w)
    for a,v in walls.items():F(a,v)
    for i,v in enumerate(object_radii):F(0x80353a74+i*4,v)
    for line in fixture['code'].splitlines():
        a,w=[int(x,16) for x in line.split()];assert a&0xfe000000==0x04000000
        a=0x80000000|(a&0x1ffffff)
        assert 0x80003f20<=a<=0x800041d4 or a in original_hooks or a in walls or 0x80353a74<=a<0x80353ac8,hex(a)
        W(a,w)
    u.ctl_remove_cache(0x80003f20,0x800041d8)
    for a in original_hooks:u.ctl_remove_cache(a,a+4)
    for a,data in guards:assert bytes(u.mem_read(a,8))==data

fixtures=json.load(open(sys.argv[2],encoding='utf8'))
display_cases=physics_cases=collision_cases=native_init_cases=0
for fixture in fixtures:
    install(fixture);size=f32(fixture['kartSize']);phys=f32(max(.01,size)) if fixture['scalePhysics'] else 1
    # Exercise every slider setting; rotate through all eight kart slots and
    # native scale states. Wider coverage for both endpoints and normal size.
    slots=range(8) if size in (0,1,100) else (int(round(size*10))%8,)
    for slot in slots:
        reset();u.mem_write(BODY+0x5b3,bytes([slot]));native=.5 if slot%2 else 1
        F(BODY+0x568,native)
        addresses=[BODY+0x1a0]+[SUS[slot*4+i]+off for i in range(4) for off in (0x158,0x1e8,0x248)]
        stock={}
        for index,a in enumerate(addresses):
            values=[.5,0,-.75,100+index*7,0,1.25,.125,-30+index*3,1.5,-.25,0,200-index*5]
            u.mem_write(a,struct.pack('>12f',*values));stock[a]=values
        run(0x802d3dc4,0x802d3dc8)
        assert u.reg_read(reg(1))==STACK
        for n in range(14,32):assert u.reg_read(reg(n))==(BODY if n==30 else 0xcafe0000+n)
        pivot=stock[BODY+0x1a0]
        for a in addresses:
            for i,actual in enumerate(matrix(a)):
                original=stock[a][i]
                expected=pivot[i]+(original-pivot[i])*size if i%4==3 else f32(original*native)*size
                close(actual,expected)
        assert RF(BODY+0x568)==native
        # Copying the rendered body to the final driver must precede restoring
        # its separate physical matrix, including when visual size is exactly 0.
        visual=bytes(u.mem_read(BODY+0x1a0,48));u.mem_write(STACK+0x20,visual)
        F(SHADOW+0xa8,native);F(SHADOW+0xac,native)
        run(0x802d3eb0,0x802d3eb4)
        close(RF(SHADOW+0xa8),native*size);close(RF(SHADOW+0xac),native*size)
        u.reg_write(reg(3),DRIVER);u.reg_write(reg(4),STACK+0x20);captured.clear()
        run(0x802d3ec4,0x802d3ec8);assert captured==[visual]
        for i,actual in enumerate(matrix(BODY+0x1a0)):
            close(actual,pivot[i] if i%4==3 else f32(pivot[i]*native)*phys)
        assert u.reg_read(reg(1))==STACK
        display_cases+=1
    if fixture['scalePhysics']:
        for a,v in walls.items():close(RF(a),v*phys)
        for i,v in enumerate(object_radii):close(RF(0x80353a74+i*4),v*phys)
        # These are native initialized fields; run the actual injected hook
        # with varied inertia/dimension values and verify its epilogue replay.
        for kart in range(21) if size in (0,1,100) else (int(round(size*10))%21,):
            reset();u.reg_write(reg(29),BODY)
            initial={0x3a4:1.25+kart,0x230:3+kart,0x234:5+kart,0x238:7+kart,0x320:40+kart,0x324:30+kart,0x328:60+kart,0x3a8:90}
            for off,v in initial.items():F(BODY+off,v)
            for n in range(28,32):W(STACK+32+(n-28)*4,0xdead0000+n)
            run(0x8029d6c0,0x8029d6c4)
            p2=f32(phys*phys);p3=f32(p2*phys);p5=f32(p2*p3)
            for off,v in initial.items():
                expected=f32(v*(p3 if off==0x3a4 else p5 if 0x230<=off<=0x238 else phys))
                close(RF(BODY+off),expected);assert RF(BODY+off)>0
            for n in range(28,32):assert u.reg_read(reg(n))==0xdead0000+n
            physics_cases+=1
        # Native kart-to-kart broad phase: a separated pair must cross its
        # actual size-dependent threshold on each axis, in both directions.
        other=0x81005000
        for axis in range(3):
            for direction in (-1,1):
                for factor in (.99,1.01):
                    reset();u.reg_write(reg(3),BODY);u.reg_write(reg(4),BODY);u.reg_write(reg(5),other)
                    for a in (BODY,other):
                        for off in (0x248,0x24c,0x250):F(a+off,0)
                        F(a+0x3a8,90*phys)
                    F(other+0x248+axis*4,180*phys*factor*direction)
                    u.emu_start(0x8029c57c,0x8029ca28,count=200)
                    assert u.reg_read(p.UC_PPC_REG_PC)==(0x8029c64c if factor<1 else 0x8029ca24)
                    collision_cases+=1
        if fixture['kartSize'] in (0,.1,.5,1,2,10,100):
            # Native mass/dimension/radius initialization from all 21 retail
            # kart parameter records, followed by the real physics hook.
            for kart in range(21):
                reset();u.reg_write(reg(29),BODY);W(BODY+0x5a8,kart)
                u.reg_write(reg(3),0x80361df8);u.reg_write(reg(4),0x80361da4)
                setf(3,12);setf(4,4);setf(6,8)
                run(0x8029d330,0x8029d690)
                values={off:RF(BODY+off) for off in (0x3a4,0x230,0x234,0x238,0x320,0x324,0x328,0x3a8)}
                assert all(math.isfinite(v) and v>0 for v in values.values())
                assert values[0x3a8]==90
                for n in range(28,32):W(STACK+32+(n-28)*4,0xdead0000+n)
                run(0x8029d6c0,0x8029d6c4)
                for off,v in values.items():
                    power=3 if off==0x3a4 else 5 if 0x230<=off<=0x238 else 1
                    close(RF(BODY+off),v*phys**power)
                native_init_cases+=1
print(json.dumps(dict(status='passed',displayCases=display_cases,physicsCases=physics_cases,sliderSettings=1001,
                     collisionThresholdCases=collision_cases,nativeKartInitializations=native_init_cases,
                     scope='Native display routine and injected physics paths; no live Dolphin race or GPU rasterization')))
