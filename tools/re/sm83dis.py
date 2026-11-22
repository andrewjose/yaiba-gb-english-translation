# minimal SM83 disassembler: sm83dis.py rom bank cpu_addr count  (bank 0 for 0000-3FFF)
import sys
R=['b','c','d','e','h','l','(hl)','a']; RP=['bc','de','hl','sp']; RP2=['bc','de','hl','af']
CC=['nz','z','nc','c']; ALU=['add a,','adc a,','sub ','sbc a,','and ','xor ','or ','cp ']
ROT=['rlc','rrc','rl','rr','sla','sra','swap','srl']
def dis1(m,pc):
    """m(addr)->byte. returns (len, text)"""
    op=m(pc); x,y,z=op>>6,(op>>3)&7,op&7; p,q=y>>1,y&1
    n=lambda:m(pc+1); nn=lambda:m(pc+1)|m(pc+2)<<8
    if op==0xCB:
        o=m(pc+1); x2,y2,z2=o>>6,(o>>3)&7,o&7
        if x2==0: return 2,'%s %s'%(ROT[y2],R[z2])
        return 2,'%s %d,%s'%(['','bit','res','set'][x2],y2,R[z2])
    if x==0:
        if z==0:
            if y==0: return 1,'nop'
            if y==1: return 3,'ld ($%04x),sp'%nn()
            if y==2: return 2,'stop'
            if y==3: return 2,'jr $%04x'%((pc+2+((n()^0x80)-0x80))&0xffff)
            return 2,'jr %s,$%04x'%(CC[y-4],(pc+2+((n()^0x80)-0x80))&0xffff)
        if z==1: return (3,'ld %s,$%04x'%(RP[p],nn())) if q==0 else (1,'add hl,%s'%RP[p])
        if z==2:
            t=['(bc)','(de)','(hl+)','(hl-)'][p]
            return 1,('ld %s,a'%t if q==0 else 'ld a,%s'%t)
        if z==3: return 1,('inc ' if q==0 else 'dec ')+RP[p]
        if z==4: return 1,'inc '+R[y]
        if z==5: return 1,'dec '+R[y]
        if z==6: return 2,'ld %s,$%02x'%(R[y],n())
        return 1,['rlca','rrca','rla','rra','daa','cpl','scf','ccf'][y]
    if x==1:
        if op==0x76: return 1,'halt'
        return 1,'ld %s,%s'%(R[y],R[z])
    if x==2: return 1,ALU[y]+R[z]
    if z==0:
        if y<4: return 1,'ret '+CC[y]
        if y==4: return 2,'ldh ($ff%02x),a'%n()
        if y==5: return 2,'add sp,%d'%((n()^0x80)-0x80)
        if y==6: return 2,'ldh a,($ff%02x)'%n()
        return 2,'ld hl,sp%+d'%((n()^0x80)-0x80)
    if z==1:
        if q==0: return 1,'pop '+RP2[p]
        return 1,['ret','reti','jp hl','ld sp,hl'][p]
    if z==2:
        if y<4: return 3,'jp %s,$%04x'%(CC[y],nn())
        return [(1,'ld ($ff00+c),a'),(3,'ld ($%04x),a'%nn()),(1,'ld a,($ff00+c)'),(3,'ld a,($%04x)'%nn())][y-4]
    if z==3:
        if y==0: return 3,'jp $%04x'%nn()
        if y==6: return 1,'di'
        if y==7: return 1,'ei'
        return 1,'db $%02x'%op
    if z==4:
        if y<4: return 3,'call %s,$%04x'%(CC[y],nn())
        return 1,'db $%02x'%op
    if z==5:
        if q==0: return 1,'push '+RP2[p]
        if p==0: return 3,'call $%04x'%nn()
        return 1,'db $%02x'%op
    if z==6: return 2,ALU[y]+'$%02x'%n()
    return 1,'rst $%02x'%(y*8)
def mk(rom,bank):
    def m(a):
        a&=0xffff
        if a<0x4000: return rom[a]
        if a<0x8000: return rom[bank*0x4000+a-0x4000]
        return 0
    return m
def off(bank,a): return a if a<0x4000 else bank*0x4000+a-0x4000
if __name__=='__main__':
    rom=open(sys.argv[1],'rb').read(); bank=int(sys.argv[2],0); pc=int(sys.argv[3],0); cnt=int(sys.argv[4])
    m=mk(rom,bank)
    for _ in range(cnt):
        l,t=dis1(m,pc)
        print('%02x:%04x  %-9s %s'%(bank if pc>=0x4000 else 0,pc,' '.join('%02x'%m(pc+i) for i in range(l)),t))
        pc+=l
