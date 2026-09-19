"""Read-only USA rev 0 hook/geometry checks, not a live gameplay/render test.

node tests/first-person.cjs /tmp/camera.json
python tests/first_person_ppc.py /path/to/GM4E01.iso /tmp/camera.json
"""
import json, math, random, struct, sys
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
V=lambda a:struct.unpack('>fff',u.mem_read(a,12))
reg=lambda n:getattr(p,f'UC_PPC_REG_{n}')
SDA,SDA2,STACK=0x803d1420,0x803d45a0,0x817f0000
MANAGER,INFO=0x81000000,0x81001000
assert bytes(u.mem_read(0x80004fa0,0x120))==bytes(0x120),'Cave must be retail zero padding'
assert bytes(u.mem_read(0x802b7484,20)).hex()=='387f0080389f01e838a1008038df01f44bdf28d9'
guards=[(a,bytes(u.mem_read(a,16))) for a in (0x80004f90,0x800050c0)]
u.reg_write(p.UC_PPC_REG_MSR,0x2000)
fixtures=json.load(open(sys.argv[2],encoding='utf8'))
rng=random.Random(1959)
count=0

def run(camera):
    for n in range(1,32):u.reg_write(reg(n),0xcafe0000+n)
    u.reg_write(reg(1),STACK);u.reg_write(reg(2),SDA2);u.reg_write(reg(13),SDA);u.reg_write(reg(31),camera)
    u.reg_write(p.UC_PPC_REG_LR,0x81234560);u.reg_write(p.UC_PPC_REG_CTR,12345)
    u.emu_start(0x802b7484,0x802b7494,count=200)
    assert u.reg_read(p.UC_PPC_REG_PC)==0x802b7494
    assert [u.reg_read(reg(n)) for n in (3,4,5,6)]==[camera+0x80,camera+0x1e8,STACK+0x80,camera+0x1f4]
    assert u.reg_read(reg(1))==STACK and u.reg_read(reg(2))==SDA2 and u.reg_read(reg(13))==SDA
    assert u.reg_read(p.UC_PPC_REG_LR)==0x81234560 and u.reg_read(p.UC_PPC_REG_CTR)==12345
    for n in range(14,32):assert u.reg_read(reg(n))==(camera if n==31 else 0xcafe0000+n)

for fixture in fixtures:
    for line in fixture['code'].splitlines():
        a,v=[int(x,16) for x in line.split()];assert a&0xfe000000==0x04000000
        a=0x80000000|(a&0x1ffffff)
        assert 0x80004fa0<=a<0x800050c0 or a==0x802b7484
        W(a,v)
    u.ctl_remove_cache(0x80004fa0,0x800050c0)
    u.ctl_remove_cache(0x802b7484,0x802b7498)
    for a,data in guards:assert bytes(u.mem_read(a,16))==data
    # Distinct viewport target pointers: no assumption that player 1 is the target.
    for viewport in range(4):
        camera=0x81100000+viewport*0x1000;body=0x81200000+(3-viewport)*0x1000
        for mode in range(9):
            for pose in range(20):
                u.mem_write(camera,bytes(0x294));W(camera,body)
                W(SDA-23608,MANAGER);W(MANAGER+56,INFO);W(INFO+8,mode)
                yaw,pitch,roll=[rng.uniform(-math.pi,math.pi) for _ in range(3)]
                cy,sy,cp,sp,cr,sr=math.cos(yaw),math.sin(yaw),math.cos(pitch),math.sin(pitch),math.cos(roll),math.sin(roll)
                # Ry * Rx * Rz; orthonormal columns: right, up, forward.
                rows=[[cy*cr+sy*sp*sr,-cy*sr+sy*sp*cr,sy*cp],
                      [cp*sr,cp*cr,-sp],[-sy*cr+cy*sp*sr,sy*sr+cy*sp*cr,cy*cp]]
                position=[rng.uniform(-10000,10000) for _ in range(3)]
                native_size=[.3,1,1.5][pose%3];F(body+0x568,native_size)
                for axis,row in enumerate(rows):
                    for col,value in enumerate(row+[position[axis]]):F(body+0x140+axis*16+col*4,value)
                before=bytes(u.mem_read(body,0x600));run(camera)
                assert bytes(u.mem_read(body,0x600))==before
                if mode in (1,2,3):
                    size=max(.01,fixture['kartSize'] if fixture['kartSize'] is not None else 1)*native_size
                    eye=V(camera+0x1e8);look=V(camera+0x1f4);up=V(STACK+0x80)
                    for axis in range(3):
                        expected=position[axis]+rows[axis][1]*90*size+rows[axis][2]*120*size
                        assert math.isclose(eye[axis],expected,abs_tol=.006)
                        assert math.isclose(look[axis]-eye[axis],rows[axis][2]*1000,abs_tol=.004)
                        assert math.isclose(up[axis],rows[axis][1],abs_tol=1e-6)
                    # Only eye and target fields of this camera may change.
                    assert bytes(u.mem_read(camera+4,0x1e4))==bytes(0x1e4)
                    assert bytes(u.mem_read(camera+0x200,0x94))==bytes(0x94)
                else:
                    assert bytes(u.mem_read(camera+4,0x290))==bytes(0x290)
                count+=1
        for missing in ('manager','info','body'):
            W(SDA-23608,MANAGER);W(MANAGER+56,INFO);W(INFO+8,2);W(camera,body)
            W({'manager':SDA-23608,'info':MANAGER+56,'body':camera}[missing],0)
            before=bytes(u.mem_read(camera,0x294));run(camera)
            assert bytes(u.mem_read(camera,0x294))==before
            count+=1
print(f'First person: {count} retail hook cases passed (scope, pose, native/custom size, 4 target cameras, null guards, memory and registers).')
