"""Execute the generated GM4E01 rescue and drift HUD hooks against a retail ISO.

node tests/driving.cjs driving.json
python tests/driving_ppc.py GM4E01.iso driving.json
The HUD test intercepts J2DFillBox at its boundary and inspects its arguments.
"""
import itertools
import json
import math
import struct
import sys
from unicorn import Uc, UC_ARCH_PPC, UC_MODE_BIG_ENDIAN, UC_MODE_PPC32, UC_HOOK_CODE
from unicorn import ppc_const as p

u = Uc(UC_ARCH_PPC, UC_MODE_PPC32 | UC_MODE_BIG_ENDIAN)
u.mem_map(0x80000000, 0x1800000)
with open(sys.argv[1], 'rb') as iso:
    header = iso.read(0x440)
    assert header[:8] == b'GM4E01\0\0' and header[0x1c:0x20] == bytes.fromhex('c2339f3d')
    dol = struct.unpack_from('>I', header, 0x420)[0]
    iso.seek(dol)
    sections = iso.read(0x100)
    for i in range(18):
        offset, addr, size = (struct.unpack_from('>I', sections, n + 4*i)[0] for n in (0, 0x48, 0x90))
        if size:
            iso.seek(dol + offset)
            u.mem_write(addr, iso.read(size))

hooks = {0x802bfce0: '881e0075', 0x802c0024: '887e0077', 0x802becf4: '806db168',
         0x802c0598: '38000000', 0x80145dc8: '4bf76c51'}
with open(sys.argv[2], encoding='utf8') as file:
    fixture = json.load(file)
for line in (fixture['rescue'] + '\n' + fixture['hud']).splitlines():
    address, word = line.split()
    assert address.startswith('04')
    a = 0x80000000 | (int(address, 16) & 0x1ffffff)
    assert u.mem_read(a, 4).hex() == hooks.get(a, '00000000')
    u.mem_write(a, bytes.fromhex(word))

def word(a, value):
    u.mem_write(a, struct.pack('>I', value))

def single(a, value):
    u.mem_write(a, struct.pack('>f', value))

def reg(n, value):
    u.reg_write(getattr(p, f'UC_PPC_REG_{n}'), value)

def fpr(n):
    raw = u.reg_read(getattr(p, f'UC_PPC_REG_FPR{n}'))
    return struct.unpack('>d', raw.to_bytes(8,'big'))[0]

mgr, info, checker, rescue, body = (0x81100000 + i*0x2000 for i in range(5))
stack, sda = 0x81700000, 0x803d1420
reg(1, stack)
reg(2, 0x803d45a0)
reg(13, sda)
reg(30, rescue)
reg(31, body)
u.reg_write(p.UC_PPC_REG_MSR, 0x2000)
word(sda-0x5c38, mgr)
word(mgr+0x38, info)
word(mgr+0x48+3*4, checker)
u.mem_write(body+0x5b3, b'\x03')

def run_until(start, stops, limit=200):
    def until(cpu, pc, size, data):
        if pc in stops:
            cpu.emu_stop()
    hook = u.hook_add(UC_HOOK_CODE, until)
    try:
        u.emu_start(start, 0, count=limit)
    finally:
        u.hook_del(hook)
    pc = u.reg_read(p.UC_PPC_REG_PC)
    assert pc in stops, hex(pc)
    return pc

cases = 0
for mode, kind, rank in itertools.product(range(6), range(7), range(10)):
    word(info+8, mode)
    word(checker+0x88, rank)
    u.mem_write(rescue+0x75, bytes([kind,1,0]))
    pc = run_until(0x802bfce0, {0x802bfce4, 0x802c0744})
    fast = mode in (1,2,3) and kind != 4 and rank in (1,3,6,8)
    assert (pc == 0x802c0744) == fast
    assert u.mem_read(rescue+0x76,2) == (bytes([2,254]) if fast else bytes([1,0]))
    cases += 1

# Passing through the original branches preserves timers and height. A fast
# fall continues into native checkpoint relocation and landing on the next tick.
for timer in (0,1,99,100,254):
    u.mem_write(rescue+0x77, bytes([timer]))
    pc = run_until(0x802c0024, {0x802c0028,0x802c033c})
    assert (pc == 0x802c033c) == (timer == 254)
    single(stack+0x54, 1935)
    run_until(0x802becf4, {0x802becf8})
    assert struct.unpack('>f',u.mem_read(stack+0x54,4))[0] == (165 if timer == 254 else 1935)
    run_until(0x802c0598, {0x802c05a0})
    assert u.mem_read(rescue+0x77,1)[0] == (10 if timer == 254 else 0)

ctrl, racehud, graph = 0x81200000, 0x81202000, 0x81204000
word(sda-0x4e98, ctrl)
word(racehud+0x1b4, graph)
reg(15, racehud)
for off, val in [(4,0),(8,0),(12,608),(16,448),(0xbc,-4),(0xc0,8),(0xc4,604),(0xc8,456)]:
    single(graph+off, val)
# The function following the displaced call starts native HUD setup.
# Return from both graphics backend calls without executing GPU I/O.
for address in (0x800273cc,0x800bca18):
    word(address,0x4e800020)
boxes = []
def capture(cpu, pc, size, data):
    color = u.mem_read(u.reg_read(p.UC_PPC_REG_3),4).hex()
    boxes.append((color, *(fpr(i) for i in range(1,5))))
u.hook_add(UC_HOOK_CODE, capture, begin=0x800273cc, end=0x800273cc)
colors = ('ffde48ff','ff882dff','39baffff')
for count, mode, phase in itertools.product(range(1,5), (1,2,3,4), range(7)):
    word(info+8,mode)
    u.mem_write(info+32,struct.pack('>h',count))
    expected = []
    for i in range(count):
        cam = 0x81300000 + i*0x1000
        target = 0x81400000 + (3-i)*0x1000
        word(ctrl+0x200+i*4,cam)
        word(cam, target)
        state = (phase+i)%7
        u.mem_write(cam+0xe1,bytes([3 if state==4 else 0]))
        if state==5:word(cam,0)
        word(target+0x574, 0 if state==3 else 1+(i%2))
        u.mem_write(target+0x5c7,bytes([8 if state==6 else state%3]))
        width,height = (608 if count<=2 else 303),(448 if count==1 else 223)
        left,top = (305*(i%2) if count>2 else 0),(225*(i//2 if count>2 else i))
        word(cam+0xf4,left)
        word(cam+0xf8,top)
        single(cam+0x140,width)
        single(cam+0x144,height)
        if mode<=3 and state<3:
            x,y=left+width*.5-4-17,top+height*.83+8
            expected.extend([('18202cff',x,y,34,8),(colors[state],x+2,y+2,10*(state+1),4)])
    boxes.clear()
    for n in range(25,32):reg(n,0xcafe0000+n)
    u.emu_start(0x80145dc8,0x80145dcc,count=2000)
    assert u.reg_read(p.UC_PPC_REG_PC)==0x80145dcc
    assert len(boxes)==len(expected), (boxes,expected)
    for got,want in zip(boxes,expected):
        assert got[0]==want[0] and all(math.isclose(a,b,abs_tol=.0001) for a,b in zip(got[1:],want[1:])), (got,want)
    assert u.reg_read(p.UC_PPC_REG_1)==stack
    for n in range(25,32):
        assert u.reg_read(getattr(p,f'UC_PPC_REG_{n}'))==0xcafe0000+n
    cases+=1
print(f'{cases} retail rescue selection and viewport HUD cases passed, plus native timer and height paths.')
