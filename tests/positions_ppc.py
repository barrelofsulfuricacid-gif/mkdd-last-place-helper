"""Execute generated patches with the user's retail ISO and native RNG.

pip install unicorn
node tests/positions.cjs /path/to/fixtures.json
python tests/positions_ppc.py /path/to/GM4E01.iso /path/to/fixtures.json
No game bytes are stored in this repository or written to the ISO.
"""
import json
import struct
import sys
from collections import Counter
from unicorn import Uc, UC_ARCH_PPC, UC_MODE_PPC32, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import ppc_const as ppc

BASE, HOOK, TABLE = 0x80005420, 0x8020CBC8, 0x80004D20
with open(sys.argv[1], 'rb') as disc:
    header = disc.read(0x440)
    assert header[:6] == b'GM4E01' and header[7] == 0
    assert header[0x1c:0x20] == bytes.fromhex('C2339F3D')
    doloff = struct.unpack_from('>I', header, 0x420)[0]
    disc.seek(doloff)
    dol = disc.read(0x100)
    sections = []
    for i in range(18):
        offset, addr, size = [struct.unpack_from('>I', dol, base+4*i)[0] for base in (0, 0x48, 0x90)]
        if size:
            disc.seek(doloff+offset)
            sections.append((addr, disc.read(size)))

machine = Uc(UC_ARCH_PPC, UC_MODE_PPC32 | UC_MODE_BIG_ENDIAN)
machine.mem_map(0x80000000, 0x1800000)
for address, data in sections:
    machine.mem_write(address, data)
assert bytes(machine.mem_read(BASE, 188)) == bytes(188)
assert bytes(machine.mem_read(TABLE, 640)) == bytes(640)
assert bytes(machine.mem_read(HOOK, 4)) == bytes.fromhex('BB410028')
guards = [(addr, bytes(machine.mem_read(addr, 16))) for addr in (BASE-16, BASE+188, TABLE-16, TABLE+640)]
W = lambda a,v: machine.mem_write(a, struct.pack('>I', v))
H = lambda a,v: machine.mem_write(a, struct.pack('>H', v))
SDA, SDA2, STACK = 0x803D1420, 0x803D45A0, 0x817F0000
MANAGER, INFO, RNG, SENTINEL = 0x81000000, 0x81001000, 0x81002000, 0x81005000
W(SDA-23608, MANAGER); W(MANAGER+56, INFO); W(0x803532D0, RNG); W(RNG, 123456789)
machine.reg_write(ppc.UC_PPC_REG_MSR, 0x2000)

def install(fixture):
    for line in fixture['code'].splitlines():
        address, value = [int(x,16) for x in line.split()]
        assert address & 0xfe000000 == 0x04000000
        address = 0x80000000 | (address & 0x1ffffff)
        assert BASE <= address < BASE+188 or TABLE <= address < TABLE+640 or address == HOOK
        W(address, value)
    machine.ctl_remove_cache(BASE, BASE+188)
    machine.ctl_remove_cache(HOOK, HOOK+4)
    for address, data in guards:
        assert bytes(machine.mem_read(address, 16)) == data

def execute(mode=3, count=8, rank=1, original=3, humans=2):
    W(INFO+8, mode); H(INFO+28, count); H(INFO+30, humans); W(STACK+0x44, SENTINEL)
    for reg in range(26,32): W(STACK+40+4*(reg-26), 0xCAFE0000+reg)
    for reg,val in ((1,STACK),(2,SDA2),(13,SDA),(3,original),(29,(rank-1)&0xffffffff)):
        machine.reg_write(getattr(ppc,f'UC_PPC_REG_{reg}'), val)
    machine.emu_start(HOOK, SENTINEL, count=1000)
    assert machine.reg_read(ppc.UC_PPC_REG_PC) == SENTINEL
    assert machine.reg_read(ppc.UC_PPC_REG_1) == STACK+64
    assert machine.reg_read(ppc.UC_PPC_REG_2) == SDA2
    assert machine.reg_read(ppc.UC_PPC_REG_13) == SDA
    for reg in range(26,32):
        assert machine.reg_read(getattr(ppc,f'UC_PPC_REG_{reg}')) == 0xCAFE0000+reg
    return machine.reg_read(ppc.UC_PPC_REG_3)

fixtures = json.load(open(sys.argv[2], encoding='utf8'))
forced_ticket = 0
def force_rng(u, address, size, user):
    assert forced_ticket <= u.reg_read(ppc.UC_PPC_REG_4)
    u.reg_write(ppc.UC_PPC_REG_3, forced_ticket)
    u.reg_write(ppc.UC_PPC_REG_PC, u.reg_read(ppc.UC_PPC_REG_LR))

hook = machine.hook_add(UC_HOOK_CODE, force_rng, begin=0x801ED138, end=0x801ED138)
ticket_checks = 0
for fixture in fixtures:
    install(fixture)
    for rank, distribution in enumerate(fixture['distributions'], 1):
        expected = [item['id'] for item in distribution for _ in range(item['weight'])]
        for forced_ticket,item in enumerate(expected):
            assert execute(rank=rank) == item, (fixture['name'], rank, forced_ticket)
            ticket_checks += 1
        if not expected:
            assert execute(rank=rank, original=15) == 15

forced_ticket = 0
scope_checks = 0
for fixture in fixtures[:2]:
    install(fixture)
    for mode in range(9):
        for count in range(2,9):
            for rank in range(1,count+1):
                for humans in (0,1,2,4):
                    for original in (0,3,12,21):
                        distribution=fixture['distributions'][rank-1]
                        active=mode in (2,3) and humans>=2 and bool(distribution)
                        expected=distribution[0]['id'] if active else original
                        assert execute(mode,count,rank,original,humans) == expected
                        scope_checks += 1
    for rank in (0,9,65535):
        assert execute(rank=rank, original=15) == 15
machine.hook_del(hook)

native_reports=[]
for fixture in fixtures[2:4]:
    install(fixture)
    # Native RNG runs across all positions; per-position routing was exhaustively
    # tested above. Aggregate samples check the shared weighted sampler.
    samples=60000
    counts=Counter(execute(rank=1+i%8) for i in range(samples))
    for item in fixture['distributions'][0]:
        assert abs(counts[item['id']]/samples-item['probability']) < 0.008
    native_reports.append({'fixture':fixture['name'],'draws':samples,'counts':dict(counts)})
print(json.dumps({'status':'passed','exhaustive_tickets':ticket_checks,'scope_register_cases':scope_checks,
                  'native_rng':native_reports,'guard_checks':'passed','live_multiplayer':'not performed'},indent=2))
