; Kenyuu Densetsu Yaiba (GB) - English VWF engine
; Assembled with rgbasm and overlaid on the expanded (512 KB) ROM by tools/build.py (rgblink -O).
;
; Message format (far data, bank $10-$17):  ASCII $20-$7E = glyphs, $FF = new line,
; $FE = page break (wait for A, clear box), $00 = end of message.
; Bank-1 stub (what the game's pointers/immediates point at):
;   [original header bytes][far bank][far lo][far hi][flags]    flags bit0 = reset tile allocator
; The printers return HL = stub+2, so the callers' "inc hl / ld a,(hl+) / cp $FF" page check
; reads the flags byte (never $FF) and ends the message.

DEF wBuf        EQU $D900   ; 16 bytes: left tile rows 0-7, right tile rows 0-7 (1bpp)
DEF wDst        EQU $D910   ; 2  VRAM address of the left tile ($9000 + code*16)
DEF wMap        EQU $D912   ; 2  BG map cell of the left tile
DEF wCode       EQU $D914   ; 1  tile code of the left tile
DEF wMap2       EQU $D915   ; 2  BG map cell of the right tile (== wMap at a box's right edge)
DEF wCode2      EQU $D917   ; 1
DEF wPenX       EQU $D918   ; pen x inside the left tile (may be >= 8 until the next glyph)
DEF wCol        EQU $D919   ; tile column of the left tile in the current line
DEF wLine       EQU $D91A
DEF wFarBank    EQU $D91B
DEF wText       EQU $D91C   ; 2  far text pointer
DEF wBoxW       EQU $D91E   ; box width in tiles (map2 clamp)
DEF wLineStart  EQU $D91F   ; tile code of column 0 of the current line
DEF wOrg        EQU $D920   ; 2  BG map address of line 0, column 0
DEF wMode       EQU $D922   ; 0 = dialogue box (fixed grid), 1 = rival scene (packed tiles)
DEF wNextTile   EQU $D923   ; rival: next free tile code
DEF wStride     EQU $D924   ; BG map bytes per line ($20 box, $40 rival)
DEF wMaxTile    EQU $D925   ; highest tile code mapped so far (rival packing)
DEF wStub       EQU $D926   ; 2  stub+2 (returned in HL)
DEF wClr1       EQU $D928   ; 2  VRAM scripts that clear the box (game's own, bank 1)
DEF wClr2       EQU $D92A   ; 2
DEF wLineCur    EQU $D92C   ; 2  BG map address of column 0 of the current line
DEF wTmp        EQU $D92E
DEF wChar       EQU $D92F

DEF hBank       EQU $FFC7   ; game's current-ROM-bank shadow (VBlank restores from it)
DEF hHeld       EQU $FFFA   ; joypad held
DEF wFlags      EQU $D81F   ; bit 6 = run the text VBlank writer ($0CDE)

DEF MARGIN      EQU 1       ; left margin in pixels
DEF BOX_DELAY   EQU 2       ; frames per character in dialogue boxes (A held: 1)
DEF RIVAL_DELAY EQU 4       ; frames per character in the rival/ending scene
DEF CANVAS0     EQU $0A     ; first canvas tile code (01-03,08,09 are box-frame tiles in the ending scene)

DEF wNameBuf    EQU $D930   ; up to 104 bytes: name tiles (1bpp) staged from bank $17

; bank $17 data written by tools/build.py (keep in sync with build.py)
DEF DATA_BANK   EQU $17
DEF CRAWL_PAGE  EQU $5000   ; 128 tiles 2bpp: intro crawl font page (precomposed lines)
DEF SWORD_TILES EQU $5800   ; 6 x 40 bytes: sword names, 5 tiles 1bpp each, index = sword id
DEF ORB_TILES   EQU $5900   ; 10 x 104 bytes: orb name (6 tiles) + move name (7 tiles), index = 1:$7301 record
DEF SS_SWORD0   EQU $6E     ; reserved sword-select codes (VRAM $9000 + code*16)
DEF SS_ORB0     EQU $73     ; orb name 73-78, move name 79-7F (contiguous with orb)

; ---------------------------------------------------------------- hooks
SECTION "hook crawl font", ROM0[$0309]
    call CrawlFont              ; was call $0A13 (intro crawl scene)

SECTION "hook sword name", ROM0[$0752]
    call SwordNameHook          ; was call $0A48 (queue sword record script)

SECTION "hook orb name", ROM0[$07C1]
    call OrbNameHook            ; was call $0A48 (queue orb record script)

SECTION "hook vblank writer", ROM0[$0CDE]
    jp VwfVBlank

SECTION "hook printer box", ROMX[$4324], BANK[1]
    jp VwfPrintBox

SECTION "hook printer rival", ROMX[$41F0], BANK[1]
    jp VwfPrintRival

; ---------------------------------------------------------------- bank 0 (3E76-3FFF)
SECTION "vwf bank0", ROM0[$3E76]
; VBlank: copy the 2-tile buffer (1bpp -> 2bpp, both planes) and map the two cells.
VwfVBlank::
    ld hl, wDst
    ld a, [hl+]
    ld e, a
    ld d, [hl]
    ld hl, wBuf
    ld b, 16
.copy
    ld a, [hl+]
    ld [de], a
    inc de
    ld [de], a
    inc de
    dec b
    jr nz, .copy
    ld hl, wMap
    ld a, [hl+]
    ld e, a
    ld a, [hl+]
    ld d, a
    ld a, [hl+]
    ld [de], a
    ld a, [hl+]
    ld e, a
    ld a, [hl+]
    ld d, a
    ld a, [hl]
    ld [de], a
    ld hl, wFlags
    res 6, [hl]
    xor a
    ret

; A = next far text byte; advances wText. Preserves BC, DE, HL.
FarByte::
    push hl
    ld hl, wText
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    di
    ld a, [wFarBank]
    ld [$2100], a
    ld a, [hl+]
    ld [wTmp], a
    ldh a, [hBank]
    ld [$2100], a
    ei
    ld a, l
    ld [wText], a
    ld a, h
    ld [wText+1], a
    ld a, [wTmp]
    pop hl
    ret

; Intro crawl: load the precomposed 128-tile page instead of the font (same copy as $0A13, LCD off)
CrawlFont::
    ld a, DATA_BANK
    call $09A0
    ld hl, CRAWL_PAGE
    ld de, $9000
    ld bc, $0800
    jp $3DB5

; HL = sword record script (bank 1); upload the sword name tiles, then queue the script
SwordNameHook::
    push hl
    ld a, [$D861]
    ld e, a
    ld d, 0
    ld hl, $D869
    add hl, de
    ld a, [hl]                  ; sword id 1-5
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl                  ; *8
    ld d, h
    ld e, l
    add hl, hl
    add hl, hl                  ; *32
    add hl, de                  ; *40
    ld de, SWORD_TILES
    add hl, de
    ld c, 40
    ld de, $9000 + SS_SWORD0 * 16
    call NameUpload
    pop hl
    jp $0A48

; HL = orb record script; record index = (sword-1)*2 + $D861 (as bank0 $079C)
OrbNameHook::
    push hl
    ld a, [$D818]
    ld e, a
    ld d, 0
    ld hl, $D869
    add hl, de
    ld a, [hl]
    dec a
    add a
    ld e, a
    ld a, [$D861]
    add e
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl                  ; *8
    ld d, h
    ld e, l
    add hl, hl
    add hl, hl                  ; *32
    ld b, h
    ld c, l
    add hl, hl                  ; *64
    add hl, bc                  ; *96
    add hl, de                  ; *104
    ld de, ORB_TILES
    add hl, de
    ld c, 104
    ld de, $9000 + SS_ORB0 * 16
    call NameUpload
    pop hl
    jp $0A48

; HL = source in DATA_BANK, DE = VRAM tile address, C = bytes (1bpp, multiple of 8).
; Stages through WRAM in 8-byte chunks (interrupts off only per chunk), then writes each byte
; twice (2bpp) only while STAT reports mode 0/1, so it is safe with the LCD on.
NameUpload:
    push de
    ld de, wNameBuf
    ld b, c
.chunk
    di
    ld a, DATA_BANK
    ld [$2100], a
    push bc
    ld c, 8
.cp
    ld a, [hl+]
    ld [de], a
    inc de
    dec c
    jr nz, .cp
    pop bc
    ldh a, [hBank]
    ld [$2100], a
    ei
    ld a, b
    sub 8
    ld b, a
    jr nz, .chunk
    pop de
    ld hl, wNameBuf
.lp
    ld b, [hl]
    inc hl
.w
    di
    ldh a, [$FF41]
    and 2
    jr z, .ok
    ei
    jr .w
.ok
    ld a, b
    ld [de], a
    inc de
    ld [de], a
    ei
    inc de
    dec c
    jr nz, .lp
    ret

; ---------------------------------------------------------------- bank 1 code (77F0-7BFF)
SECTION "vwf bank1", ROMX[$77F0], BANK[1]

; replaces 1:$4324. HL = stub, DE = glyph row of line 1 in the original layout
; ($9923 chapter_end 14x8 box, $9947 chapter_intro/powerup 12x8 box)
VwfPrintBox::
    xor a
    ld [wMode], a
    ld a, $20
    ld [wStride], a
    ld a, e
    sub $20                     ; English uses the dakuten row too: line 0 = DE - $20
    ld [wOrg], a
    ld a, d
    sbc 0
    ld [wOrg+1], a
    ld a, e
    cp $23
    jr nz, .narrow
    ld a, 14
    ld bc, $7123
    ld de, $7168
    jr .geo
.narrow
    ld a, 12
    ld bc, $71AD
    ld de, $71EA
.geo
    ld [wBoxW], a
    ld a, c
    ld [wClr1], a
    ld a, b
    ld [wClr1+1], a
    ld a, e
    ld [wClr2], a
    ld a, d
    ld [wClr2+1], a
    call ReadStub
.page
    call PageInit
.loop
    ; typewriter delay: BOX_DELAY frames, 1 frame while A is held
    ld b, BOX_DELAY
.wait
    rst $10
    ldh a, [hHeld]
    and 1
    jr nz, .go
    dec b
    jr nz, .wait
.go
    call FarByte
    and a
    jr z, .end
    cp $FF
    jr z, .nl
    cp $FE
    jr z, .pagebreak
    call DrawChar
    ld a, [wChar]
    cp $20
    jr z, .loop
    ld a, $8E                   ; per-character blip, as the original printer
    call $3DCE
    jr .loop
.nl
    call NewLine
    jr .loop
.pagebreak
    call $0A0B                  ; wait for A
    ld hl, wClr1
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    call $0A48                  ; VBlank VRAM script: clear rows 0-3 of the box
    rst $08
    ld hl, wClr2
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    call $0A48                  ; rows 4-7
    rst $08
    rst $08
    jr .page
.end
    call $0A0B                  ; wait for A (as the original)
    jr RetStub

; replaces 1:$41F0 (rival / ending scene, BG $9C00, no A speed-up, 2-row line spacing)
VwfPrintRival::
    ld a, 1
    ld [wMode], a
    ld a, $40
    ld [wStride], a
    ld a, e
    ld [wOrg], a
    ld a, d
    ld [wOrg+1], a
    ld a, 32
    ld [wBoxW], a
    call ReadStub
    bit 0, a
    jr z, .keep
    ld a, CANVAS0
    ld [wNextTile], a
.keep
    call PageInit
.loop
    ld b, RIVAL_DELAY
.wait
    rst $08
    xor a
    ld [$D867], a               ; as the original printer
    dec b
    jr nz, .wait
    call FarByte
    and a
    jr z, .end
    cp $FF
    jr z, .nl
    cp $FE
    jr z, .loop                 ; no pages here
    call DrawChar
    jr .loop
.nl
    call NewLine
    jr .loop
.end
    ld a, [wMaxTile]
    inc a
    ld [wNextTile], a
    ; fall through
RetStub:
    ld hl, wStub
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    ret

; HL = stub -> wFarBank/wText, wStub = stub+2; returns A = flags
ReadStub:
    ld a, [hl+]
    ld [wFarBank], a
    ld a, [hl+]
    ld [wText], a
    ld a, [hl]
    ld [wText+1], a
    ld a, l
    ld [wStub], a
    ld a, h
    ld [wStub+1], a
    inc hl
    ld a, [hl]
    ret

PageInit:
    xor a
    ld [wLine], a
    ld a, [wOrg]
    ld [wLineCur], a
    ld a, [wOrg+1]
    ld [wLineCur+1], a
    ld a, [wMode]
    and a
    ld a, CANVAS0
    jr z, .box
    ld a, [wNextTile]
    call RingWrap
.box
    ld [wLineStart], a
    ld [wMaxTile], a
    ; fall through
LineInit:
    ld a, MARGIN
    ld [wPenX], a
    xor a
    ld [wCol], a
    ld hl, wBuf
    ld b, 16
.clr
    ld [hl+], a
    dec b
    jr nz, .clr
    ret

NewLine:
    ld hl, wLine
    inc [hl]
    ld a, [wStride]
    ld hl, wLineCur
    add [hl]
    ld [hl+], a
    jr nc, .nc
    inc [hl]
.nc
    ld a, [wMode]
    and a
    jr z, .box
    ld a, [wMaxTile]
    inc a
    call RingWrap
    ld [wLineStart], a
    jr LineInit

.box
    ld a, [wBoxW]
    ld hl, wLineStart
    add [hl]
    ld [hl], a
    jr LineInit

; rival scene tile ring: a line needs up to 17 contiguous codes; restart at CANVAS0 when they
; would run past $7F (the lines that used the old codes have scrolled out of the 3-line box)
RingWrap:
    cp $80-17
    ret c
    ld a, CANVAS0
    ret

; A = ASCII char. Composes the glyph into wBuf and queues the VBlank copy.
DrawChar:
    ld [wChar], a
    sub $20
    cp 95
    jr c, .ok
    xor a                       ; unknown -> space
.ok
    ld c, a                     ; c = glyph index
    ; normalize: while penX >= 8 shift the buffer one tile left
.norm
    ld a, [wPenX]
    cp 8
    jr c, .normed
    sub 8
    ld [wPenX], a
    ld hl, wCol
    inc [hl]
    ld hl, wBuf
    ld de, wBuf+8
    ld b, 8
.sh
    ld a, [de]
    ld [hl+], a
    xor a
    ld [de], a
    inc de
    dec b
    jr nz, .sh
    jr .norm
.normed
    ; advance width
    ld hl, VwfWidths
    ld b, 0
    add hl, bc
    ld a, [hl]
    ld [wTmp], a
    ld a, c
    and a
    jr z, .advance              ; space: no ink, no VRAM write
    ; glyph rows: VwfFont + idx*8
    ld l, c
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl
    ld de, VwfFont
    add hl, de
    ld de, wBuf
    ld b, 8
.row
    push bc
    ld a, [wPenX]
    ld b, a
    ld a, [hl+]
    ld c, 0
    inc b
    jr .shtest
.shr
    srl a
    rr c
.shtest
    dec b
    jr nz, .shr
    push hl
    ld h, d
    ld l, e
    or [hl]
    ld [hl], a
    ld a, l
    add 8
    ld l, a
    ld a, c
    or [hl]
    ld [hl], a
    pop hl
    inc de
    pop bc
    dec b
    jr nz, .row
    call QueueFlush
.advance
    ld a, [wTmp]
    ld hl, wPenX
    add [hl]
    ld [hl], a
    ret

; set wDst/wMap/wCode/wMap2/wCode2 for the current column and raise the VBlank flag
QueueFlush:
    ld a, [wCol]
    ld c, a
    ld a, [wLineStart]
    add c
    ld [wCode], a
    ld b, a                     ; b = code
    ; dst = $9000 + code*16
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld a, h
    add $90
    ld [wDst+1], a
    ld a, l
    ld [wDst], a
    ; map = wLineCur + col
    ld a, [wLineCur]
    add c
    ld [wMap], a
    ld e, a
    ld a, [wLineCur+1]
    adc 0
    ld [wMap+1], a
    ld d, a
    ; right cell unless col+1 == box width
    ld a, [wBoxW]
    dec a
    cp c
    jr z, .edge
    inc de
    inc b
.edge
    ld a, e
    ld [wMap2], a
    ld a, d
    ld [wMap2+1], a
    ld a, b
    ld [wCode2], a
    ld hl, wMaxTile
    cp [hl]
    jr c, .nomax
    ld [hl], a
.nomax
    ld hl, wFlags
    set 6, [hl]
    ret

SECTION "vwf font", ROMX[$7C40], BANK[1]
VwfFont::
    INCBIN "vwf.bin"     ; font dir passed with rgbasm -I
VwfWidths::
    INCBIN "widths.bin"
