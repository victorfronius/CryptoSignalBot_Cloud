// EW Pattern v37
// Pine Script v6 — dynamic request.security с переменным zzLen1d
// v24 + встроенный EW Orient (логика 1D волн)
// Новый фильтр: блокирует сигналы если 1D волна = 5 или C (конец движения)
// ТФ: 4H | Фильтр: EMA50/200 + волна 1D | Volume Surge | EXIT 15m

//@version=6
indicator("EW Pattern v37 [4H]", overlay=true,
     max_lines_count=500, max_labels_count=400, max_boxes_count=100)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — ZIGZAG
// ══════════════════════════════════════════════════════
var string GZZ = "ZigZag"
zzLen   = input.int(7, "Pivot Length (bars)", minval=3, maxval=30, group=GZZ)
minBars = input.int(3, "Мин. баров между пивотами", minval=1, maxval=20, group=GZZ)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — ПРАВИЛА ЭЛЛИОТТА
// ══════════════════════════════════════════════════════
var string GEW = "Правила Эллиотта"
w1MinPct = input.float(0.8,  "W1 мин. размер % от цены", minval=0.1, maxval=5.0,    step=0.1,  group=GEW)
w2Min    = input.float(38.0, "W2 откат мин %",            minval=10.0, maxval=60.0,  step=0.1,  group=GEW)
w2Max    = input.float(78.6, "W2 откат макс %",           minval=50.0, maxval=100.0, step=0.1,  group=GEW)
w4Min    = input.float(14.0, "W4 откат мин %",            minval=5.0,  maxval=40.0,  step=0.1,  group=GEW)
w4Max    = input.float(61.8, "W4 откат макс %",           minval=20.0, maxval=90.0,  step=0.1,  group=GEW)
w3Mult   = input.float(1.0,  "W3 мин. коэф. от W1",       minval=0.5,  maxval=3.0,   step=0.01, group=GEW)
slBuf    = input.float(0.3,  "SL буфер %",                minval=0.1,  maxval=2.0,   step=0.1,  group=GEW)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — VOLUME SURGE
// ══════════════════════════════════════════════════════
var string GVS = "Volume Surge"
useVol     = input.bool(true,  "Включить фильтр объёма",      group=GVS)
volPer     = input.int(20,     "Период MA объёма",             minval=5,  maxval=100, group=GVS)
volMult    = input.float(2.0,  "Множитель объёма (BTC/ETH)",   minval=1.0, maxval=5.0, step=0.1, group=GVS)
volMultAlt = input.float(1.5,  "Множитель объёма (альткоины)", minval=1.0, maxval=5.0, step=0.1, group=GVS)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — СВЕЧНЫЕ ПАТТЕРНЫ
// ══════════════════════════════════════════════════════
var string GPC = "Свечные паттерны"
showCandles = input.bool(true, "Показывать Pin Bar / Engulfing", group=GPC)
pinRatio    = input.float(0.6, "Pin Bar: мин. хвост/свеча",     minval=0.3, maxval=0.9, step=0.05, group=GPC)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — EXIT ДЕТЕКТОР
// ══════════════════════════════════════════════════════
var string GEXIT = "EXIT — детектор разворота (15m)"
useExit       = input.bool(true,  "Включить EXIT детектор",      group=GEXIT)
exitCandlePct = input.float(1.0,  "Мин. размер свечи % от цены", minval=0.3, maxval=3.0,  step=0.1,  group=GEXIT)
exitVolMult   = input.float(3.0,  "Мин. множитель объёма",       minval=1.0, maxval=10.0, step=0.1,  group=GEXIT)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — ФИЛЬТР ТРЕНДА 1D EMA
// ══════════════════════════════════════════════════════
var string GTF = "Фильтр тренда (1D EMA)"
useTF = input.bool(true, "Включить фильтр тренда 1D", group=GTF)
emaF  = input.int(50,    "EMA быстрая",               minval=10, maxval=200, group=GTF)
emaS  = input.int(200,   "EMA медленная",             minval=50, maxval=500, group=GTF)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — ORIENT (ВОЛНА 1D)
// ══════════════════════════════════════════════════════
var string GORI = "Orient — фильтр волны 1D"
useOrientFilter = input.bool(true, "Блокировать сигналы на волне 5/C (1D)", group=GORI,
     tooltip="Если на 1D последняя волна = 5 или C — сигналы в этом направлении блокируются")
showOrient1D    = input.bool(true, "Показывать разметку 1D волн",           group=GORI)
zzLen1d         = input.int(3,     "Pivot Length 1D",  minval=2, maxval=10, group=GORI)
nWaves1d        = input.int(6,     "Кол-во пивотов 1D", minval=4, maxval=12, group=GORI)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — RTM
// ══════════════════════════════════════════════════════
var string GRTM = "RTM — Read The Market"
showRTM    = input.bool(true,  "Показывать RTM зоны",        group=GRTM)
showERC    = input.bool(true,  "Показывать ERC свечи",       group=GRTM)
showFTR    = input.bool(true,  "Показывать FTR",             group=GRTM)
useRTMfilt = input.bool(true,  "RTM фильтр для W3/W5 входа", group=GRTM,
     tooltip="Сигнал W3/W5 генерируется только если цена в RTM зоне или отбилась от неё")
ercMult    = input.float(1.5,  "ERC: мин. размер × средней свечи", minval=1.0, maxval=5.0, step=0.1, group=GRTM)
rtmLookback = input.int(10,    "RTM: баров для поиска базы",  minval=3, maxval=30,  group=GRTM)
rtmZoneExt  = input.int(40,    "RTM: протяжённость зоны (баров)", minval=10, maxval=200, group=GRTM)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — LIMIT ЗОНЫ
// ══════════════════════════════════════════════════════
var string GLIM = "LIMIT зоны"
showLimitZones = input.bool(true,  "Показывать лимитные зоны",        group=GLIM)
useLimitAlert  = input.bool(true,  "Алерт при входе в лимитную зону", group=GLIM)
showFibW2      = input.bool(true,  "Fib зона W2 (38.2/50/61.8)",      group=GLIM)
showFibW4      = input.bool(true,  "Fib зона W4 (23.6/38.2/50)",      group=GLIM)
showRTMlimit   = input.bool(true,  "RTM база как лимитная зона",       group=GLIM)
fibW2Lo = input.float(38.2, "W2 нижний Fib %", minval=20.0, maxval=60.0, step=0.1, group=GLIM)
fibW2Hi = input.float(61.8, "W2 верхний Fib %", minval=40.0, maxval=80.0, step=0.1, group=GLIM)
fibW4Lo = input.float(23.6, "W4 нижний Fib %", minval=10.0, maxval=40.0, step=0.1, group=GLIM)
fibW4Hi = input.float(50.0, "W4 верхний Fib %", minval=30.0, maxval=70.0, step=0.1, group=GLIM)

// ══════════════════════════════════════════════════════
// НАСТРОЙКИ — ОТОБРАЖЕНИЕ
// ══════════════════════════════════════════════════════
var string GDISP = "Отображение"
showZZ    = input.bool(true, "Показать ZigZag",  group=GDISP)
showTP    = input.bool(true, "Показать цели",    group=GDISP)
showSL    = input.bool(true, "Показать SL",      group=GDISP)
showPanel = input.bool(true, "Показать панель",  group=GDISP)

// ══════════════════════════════════════════════════════
// ФИЛЬТР ТРЕНДА 1D EMA
// ══════════════════════════════════════════════════════
c1d   = request.security(syminfo.tickerid, "1D", close, lookahead=barmerge.lookahead_off)
e1hF  = ta.ema(c1d, emaF)
e1hS  = ta.ema(c1d, emaS)
e1hOK = not na(e1hF) and not na(e1hS)
tBull = e1hOK ? e1hF > e1hS and c1d > e1hF : true
tBear = e1hOK ? e1hF < e1hS and c1d < e1hF : true

// ══════════════════════════════════════════════════════
// ORIENT — ПИВОТЫ 1D
// ══════════════════════════════════════════════════════
// Пивоты 1D — только цены (без time[], RE10045 fix)
// bar_index используется для привязки меток
// Пивоты 1D — через request.security только high/low/time (БЕЗ ta.pivothigh)
// Это единственный способ избежать RE10045
high1d  = request.security(syminfo.tickerid, "1D", high,  lookahead=barmerge.lookahead_off)
low1d   = request.security(syminfo.tickerid, "1D", low,   lookahead=barmerge.lookahead_off)
time1d  = request.security(syminfo.tickerid, "1D", time,  lookahead=barmerge.lookahead_off)

// Определяем пивоты вручную — сравниваем с соседними барами 1D
// Используем фиксированное окно 3 бара (надёжно без RE10045)
high1d_1 = request.security(syminfo.tickerid, "1D", high[1],  lookahead=barmerge.lookahead_off)
high1d_2 = request.security(syminfo.tickerid, "1D", high[2],  lookahead=barmerge.lookahead_off)
low1d_1  = request.security(syminfo.tickerid, "1D", low[1],   lookahead=barmerge.lookahead_off)
low1d_2  = request.security(syminfo.tickerid, "1D", low[2],   lookahead=barmerge.lookahead_off)

// Пивот хай: high[1] > high[0] и high[1] > high[2]
isPivH1d = not na(high1d) and not na(high1d_1) and not na(high1d_2) and
           high1d_1 > high1d and high1d_1 > high1d_2

// Пивот лоу: low[1] < low[0] и low[1] < low[2]
isPivL1d = not na(low1d) and not na(low1d_1) and not na(low1d_2) and
           low1d_1 < low1d and low1d_1 < low1d_2

var float[] o_pH  = array.new_float(0)
var int[]   o_bH  = array.new_int(0)
var float[] o_pL  = array.new_float(0)
var int[]   o_bL  = array.new_int(0)

if isPivH1d
    _sz   = array.size(o_pH)
    _addH = _sz == 0
    if not _addH
        _addH := array.get(o_pH, _sz-1) != high1d_1
    if _addH
        array.push(o_pH, high1d_1)
        array.push(o_bH, bar_index)
        if array.size(o_pH) > 50
            array.shift(o_pH)
            array.shift(o_bH)

if isPivL1d
    _szL  = array.size(o_pL)
    _addL = _szL == 0
    if not _addL
        _addL := array.get(o_pL, _szL-1) != low1d_1
    if _addL
        array.push(o_pL, low1d_1)
        array.push(o_bL, bar_index)
        if array.size(o_pL) > 50
            array.shift(o_pL)
            array.shift(o_bL)

// ── Слияние High/Low пивотов 1D (по bar_index) ──
f_merge(hP, hB, lP, lB) =>
    nh = array.size(hB)
    nl = array.size(lB)
    if nh == 0 and nl == 0
        [array.new_float(0), array.new_int(0), array.new_bool(0)]
    else
        var float[] rP = array.new_float(0)
        var int[]   rT = array.new_int(0)
        var bool[]  rH = array.new_bool(0)
        array.clear(rP)
        array.clear(rT)
        array.clear(rH)
        ih = 0
        il = 0
        while ih < nh or il < nl
            takeH = false
            if ih < nh and il < nl
                takeH := array.get(hB, ih) <= array.get(lB, il)
            else if ih < nh
                takeH := true
            else
                takeH := false
            if takeH
                array.push(rP, array.get(hP, ih))
                array.push(rT, array.get(hB, ih))
                array.push(rH, true)
                ih += 1
            else
                array.push(rP, array.get(lP, il))
                array.push(rT, array.get(lB, il))
                array.push(rH, false)
                il += 1
        [rP, rT, rH]

// ── Fib вспомогательные функции для Orient ──
f_ori_retrace(wStart, wEnd, retEnd) =>
    wSize = math.abs(wEnd - wStart)
    rSize = math.abs(retEnd - wEnd)
    wSize > 0 ? rSize / wSize * 100.0 : 0.0

f_ori_ratio(aStart, aEnd, bStart, bEnd) =>
    sA = math.abs(aEnd - aStart)
    sB = math.abs(bEnd - bStart)
    sA > 0 ? sB / sA * 100.0 : 0.0

// ── Определение текущей волны на 1D с Fib валидацией ──
// Таблица Вознего: W2 38-78.6%, W3 50-450%, W4 14-61.8%, W5 25-300%, C 62-262%
f_get_wave1d(pp1d, ph1d) =>
    n1d      = array.size(pp1d)
    wave     = "—"
    waveFib  = true
    isBull1d = false

    if n1d < 2 or array.size(ph1d) < n1d
        [wave, waveFib, isBull1d]
    else
        lastIsH  = array.get(ph1d, n1d - 1)
        isBull1d := not lastIsH

        if n1d >= 6 and array.size(ph1d) >= n1d
            p0 = array.get(pp1d, n1d-6)
            p1 = array.get(pp1d, n1d-5)
            p2 = array.get(pp1d, n1d-4)
            p3 = array.get(pp1d, n1d-3)
            p4 = array.get(pp1d, n1d-2)
            p5 = array.get(pp1d, n1d-1)
            g0 = array.get(ph1d, n1d-6)
            g5 = array.get(ph1d, n1d-1)

            if isBull1d
                if not g0 and g5
                    wave := "5"
                    w2ret = f_ori_retrace(p0, p1, p2)
                    w3rat = f_ori_ratio(p0, p1, p2, p3)
                    w4ret = f_ori_retrace(p2, p3, p4)
                    w5rat = f_ori_ratio(p0, p1, p4, p5)
                    fibOk = w2ret >= 38.0 and w2ret <= 78.6 and p2 > p0
                    fibOk := fibOk and w3rat >= 50.0 and w3rat <= 450.0
                    fibOk := fibOk and w4ret >= 14.0 and w4ret <= 61.8 and p4 > p1
                    fibOk := fibOk and w5rat >= 25.0 and w5rat <= 300.0
                    waveFib := fibOk
                else if not g0 and not g5
                    wave := "4"
                    w2ret = f_ori_retrace(p0, p1, p2)
                    w3rat = f_ori_ratio(p0, p1, p2, p3)
                    w4ret = f_ori_retrace(p2, p3, p4)
                    fibOk = w2ret >= 38.0 and w2ret <= 78.6 and p2 > p0
                    fibOk := fibOk and w3rat >= 50.0 and w3rat <= 450.0
                    fibOk := fibOk and w4ret >= 14.0 and w4ret <= 61.8 and p4 > p1
                    waveFib := fibOk
            else
                if g0 and not g5
                    wave := "5"
                    w2ret = f_ori_retrace(p0, p1, p2)
                    w3rat = f_ori_ratio(p0, p1, p2, p3)
                    w4ret = f_ori_retrace(p2, p3, p4)
                    w5rat = f_ori_ratio(p0, p1, p4, p5)
                    fibOk = w2ret >= 38.0 and w2ret <= 78.6 and p2 < p0
                    fibOk := fibOk and w3rat >= 50.0 and w3rat <= 450.0
                    fibOk := fibOk and w4ret >= 14.0 and w4ret <= 61.8 and p4 < p1
                    fibOk := fibOk and w5rat >= 25.0 and w5rat <= 300.0
                    waveFib := fibOk
                else if g0 and g5
                    wave := "4"
                    w2ret = f_ori_retrace(p0, p1, p2)
                    w3rat = f_ori_ratio(p0, p1, p2, p3)
                    w4ret = f_ori_retrace(p2, p3, p4)
                    fibOk = w2ret >= 38.0 and w2ret <= 78.6 and p2 < p0
                    fibOk := fibOk and w3rat >= 50.0 and w3rat <= 450.0
                    fibOk := fibOk and w4ret >= 14.0 and w4ret <= 61.8 and p4 < p1
                    waveFib := fibOk

        else if n1d >= 4 and array.size(ph1d) >= n1d
            pA  = array.get(pp1d, n1d-3)
            pB  = array.get(pp1d, n1d-2)
            pC  = array.get(pp1d, n1d-1)
            gC  = array.get(ph1d, n1d-1)
            if isBull1d and not gC
                wave    := "C"
                cRat     = f_ori_ratio(pA, pB, pB, pC)
                waveFib := cRat >= 62.0 and cRat <= 262.0
            else if not isBull1d and gC
                wave    := "C"
                cRat     = f_ori_ratio(pA, pB, pB, pC)
                waveFib := cRat >= 62.0 and cRat <= 262.0
            else
                wave := "B"

        else if n1d >= 2
            wave := "1"

        [wave, waveFib, isBull1d]

// ══════════════════════════════════════════════════════
// ORIENT — вычисляем волну 1D (каждый бар)
// ══════════════════════════════════════════════════════
var string wave1d    = "—"
var bool   orient1dBull = true
var bool   orient1dBear = true

// Пересчёт волны только на последнем баре (barstate.islast)
// Для фильтра используем var переменные которые обновляются ниже

// ══════════════════════════════════════════════════════
// 15M ДАННЫЕ ДЛЯ EXIT
// ══════════════════════════════════════════════════════
close15  = request.security(syminfo.tickerid, "15", close,  lookahead=barmerge.lookahead_off)
open15   = request.security(syminfo.tickerid, "15", open,   lookahead=barmerge.lookahead_off)
vol15    = request.security(syminfo.tickerid, "15", volume, lookahead=barmerge.lookahead_off)
volMA15  = request.security(syminfo.tickerid, "15", ta.sma(volume, 20), lookahead=barmerge.lookahead_off)
cPct15   = math.abs(close15 - open15) / open15 * 100
bull15   = close15 > open15 and cPct15 >= exitCandlePct and vol15 > volMA15 * exitVolMult
bear15   = close15 < open15 and cPct15 >= exitCandlePct and vol15 > volMA15 * exitVolMult
exitLong  = useExit and bull15
exitShort = useExit and bear15

// ══════════════════════════════════════════════════════
// VOLUME SURGE
// ══════════════════════════════════════════════════════
volMA  = ta.sma(volume, volPer)
_isBig = syminfo.ticker == "BTCUSDT.P" or syminfo.ticker == "ETHUSDT.P" or
         syminfo.ticker == "BTCUSDT"   or syminfo.ticker == "ETHUSDT"
_vMult = _isBig ? volMult : volMultAlt
vSurge = volume > volMA * _vMult
fVol   = useVol ? vSurge : true

// ══════════════════════════════════════════════════════
// СВЕЧНЫЕ ПАТТЕРНЫ
// ══════════════════════════════════════════════════════
pinBull() =>
    r = high - low
    r > 0 and (math.min(open, close) - low) >= r * pinRatio and close > open

pinBear() =>
    r = high - low
    r > 0 and (high - math.max(open, close)) >= r * pinRatio and close < open

engBull() =>
    close > open and close[1] < open[1] and open <= close[1] and close >= open[1]

engBear() =>
    close < open and close[1] > open[1] and open >= close[1] and close <= open[1]

// ══════════════════════════════════════════════════════
// RTM — ERC ДЕТЕКТОР
// ══════════════════════════════════════════════════════
avgCandle = ta.sma(high - low, 20)
candleSize = high - low
bodySize   = math.abs(close - open)
bodyPct    = candleSize > 0 ? bodySize / candleSize : 0

ercBull = close > open and bodyPct >= 0.7 and candleSize >= avgCandle * ercMult
ercBear = close < open and bodyPct >= 0.7 and candleSize >= avgCandle * ercMult

plotshape(showERC and ercBull, title="ERC Bull", style=shape.diamond,
     location=location.belowbar, color=color.new(color.lime, 20), size=size.tiny, text="ERC")
plotshape(showERC and ercBear, title="ERC Bear", style=shape.diamond,
     location=location.abovebar, color=color.new(color.red, 20),  size=size.tiny, text="ERC")

// ══════════════════════════════════════════════════════
// RTM — ЗОНЫ RBR / DBD / RBD / DBR
// ══════════════════════════════════════════════════════
isBase(idx) =>
    (high[idx] - low[idx]) < avgCandle * 0.5

f_findBase(lookback) =>
    found    = false
    baseHigh = float(na)
    baseLow  = float(na)
    for i = 1 to lookback
        if isBase(i) and not isBase(i+1)
            found    := true
            baseHigh := high[i]
            baseLow  := low[i]
            break
    [found, baseHigh, baseLow]

[baseFound, baseH, baseL] = f_findBase(rtmLookback)

prevBull = close[rtmLookback+1] > open[rtmLookback+1]
prevBear = close[rtmLookback+1] < open[rtmLookback+1]
curBull  = close > open
curBear  = close < open

isRBR = baseFound and prevBull and curBull
isDBD = baseFound and prevBear and curBear
isRBD = baseFound and prevBull and curBear
isDBR = baseFound and prevBear and curBull

var box[] rtmBoxes = array.new_box(0)

if showRTM and barstate.islast
    for b in rtmBoxes
        box.delete(b)
    array.clear(rtmBoxes)

if showRTM and baseFound
    _clr    = isRBR ? color.new(color.lime,75)   : isDBD ? color.new(color.red,75)    :
              isRBD ? color.new(color.orange,75) : color.new(color.aqua,75)
    _lbl    = isRBR ? "RBR" : isDBD ? "DBD" : isRBD ? "RBD" : isDBR ? "DBR" : ""
    _txtClr = isRBR ? color.lime : isDBD ? color.red : isRBD ? color.orange : color.aqua
    if _lbl != ""
        bx = box.new(bar_index - rtmLookback, baseH, bar_index + rtmZoneExt, baseL,
             border_color=color.new(_txtClr, 40), bgcolor=_clr,
             text=_lbl, text_color=_txtClr, text_size=size.small, xloc=xloc.bar_index)
        array.push(rtmBoxes, bx)

// ══════════════════════════════════════════════════════
// RTM — FTR ДЕТЕКТОР
// ══════════════════════════════════════════════════════
ftrZoneTop = baseFound ? baseH : float(na)
ftrZoneBot = baseFound ? baseL : float(na)

ftrBull = showFTR and baseFound and
     low  <= ftrZoneBot * 1.005 and low  >= ftrZoneBot * 0.995 and close > ftrZoneBot
ftrBear = showFTR and baseFound and
     high >= ftrZoneTop * 0.995 and high <= ftrZoneTop * 1.005 and close < ftrZoneTop

plotshape(ftrBull, title="FTR Bull", style=shape.labelup,   location=location.belowbar,
     color=color.new(color.aqua,30),   textcolor=color.white, size=size.small, text="FTR↑")
plotshape(ftrBear, title="FTR Bear", style=shape.labeldown, location=location.abovebar,
     color=color.new(color.orange,30), textcolor=color.white, size=size.small, text="FTR↓")

// ══════════════════════════════════════════════════════
// RTM ФИЛЬТР
// ══════════════════════════════════════════════════════
rtmBullOK = not useRTMfilt or (isRBR or isDBR or ftrBull or ercBull or ercBull[1] or ercBull[2])
rtmBearOK = not useRTMfilt or (isDBD or isRBD or ftrBear or ercBear or ercBear[1] or ercBear[2])

// ══════════════════════════════════════════════════════
// ЗИГЗАГ 4H
// ══════════════════════════════════════════════════════
var float[] pp = array.new_float(0)
var int[]   pb = array.new_int(0)
var bool[]  ph = array.new_bool(0)
MAX_PV = 40

pvH = ta.pivothigh(high, zzLen, zzLen)
pvL = ta.pivotlow(low,  zzLen, zzLen)

if not na(pvH)
    _b   = bar_index - zzLen
    _sz  = array.size(ph)
    _lH  = _sz > 0 ? array.get(ph, _sz-1) : false
    _lB  = _sz > 0 ? array.get(pb, _sz-1) : 0
    if _sz > 0 and _lH
        if pvH > array.get(pp, _sz-1)
            array.set(pp, _sz-1, pvH)
            array.set(pb, _sz-1, _b)
    else if _b - _lB >= minBars
        array.push(pp, pvH)
        array.push(pb, _b)
        array.push(ph, true)
        if array.size(pp) > MAX_PV
            array.shift(pp)
            array.shift(pb)
            array.shift(ph)

if not na(pvL)
    _b2  = bar_index - zzLen
    _sz2 = array.size(ph)
    _lH2 = _sz2 > 0 ? array.get(ph, _sz2-1) : true
    _lB2 = _sz2 > 0 ? array.get(pb, _sz2-1) : 0
    if _sz2 > 0 and not _lH2
        if pvL < array.get(pp, _sz2-1)
            array.set(pp, _sz2-1, pvL)
            array.set(pb, _sz2-1, _b2)
    else if _b2 - _lB2 >= minBars
        array.push(pp, pvL)
        array.push(pb, _b2)
        array.push(ph, false)
        if array.size(pp) > MAX_PV
            array.shift(pp)
            array.shift(pb)
            array.shift(ph)

// ══════════════════════════════════════════════════════
// РИСОВАНИЕ ЗИГЗАГА
// ══════════════════════════════════════════════════════
var line[] zzLines = array.new_line(0)

if showZZ and barstate.islast
    for ln in zzLines
        line.delete(ln)
    array.clear(zzLines)
    _n = array.size(pp)
    if _n >= 2
        _s = math.max(0, _n - 25)
        for i = _s to _n - 2
            _b1 = array.get(pb, i)
            _b2 = array.get(pb, i+1)
            if bar_index - _b1 < 300 and bar_index - _b2 < 300
                array.push(zzLines, line.new(_b1, array.get(pp,i), _b2, array.get(pp,i+1),
                     color=color.new(color.gray,50), width=1, xloc=xloc.bar_index))

// ══════════════════════════════════════════════════════
// ПРОВЕРКА ПАТТЕРНОВ 4H
// ══════════════════════════════════════════════════════
chkBull(float p0, float p1, float p2, float p3, float p4) =>
    w1 = p1-p0
    w2 = p1-p2
    w3 = p3-p2
    w4 = p3-p4
    ok = w1>0 and w2>0 and w3>0 and w4>0
    ok := ok and w1 >= p0*w1MinPct/100
    ok := ok and (w2/w1*100) >= w2Min and (w2/w1*100) <= w2Max
    ok := ok and (w4/w3*100) >= w4Min and (w4/w3*100) <= w4Max
    ok := ok and w3 >= w1*w3Mult
    ok := ok and p4 > p1 and p3 > p1
    [ok, w1, w3]

chkBear(float p0, float p1, float p2, float p3, float p4) =>
    w1 = p0-p1
    w2 = p2-p1
    w3 = p2-p3
    w4 = p4-p3
    ok = w1>0 and w2>0 and w3>0 and w4>0
    ok := ok and w1 >= p0*w1MinPct/100
    ok := ok and (w2/w1*100) >= w2Min and (w2/w1*100) <= w2Max
    ok := ok and (w4/w3*100) >= w4Min and (w4/w3*100) <= w4Max
    ok := ok and w3 >= w1*w3Mult
    ok := ok and p4 < p1 and p3 < p1
    [ok, w1, w3]

// ══════════════════════════════════════════════════════
// ORIENT — ВЫЧИСЛЕНИЕ ВОЛНЫ 1D + ФИЛЬТР
// ══════════════════════════════════════════════════════
// Мержим пивоты 1D
[pp1d, pt1d, ph1d] = f_merge(o_pH, o_bH, o_pL, o_bL)

// Защита от несовпадения размеров массивов
sz_pp = array.size(pp1d)
if sz_pp == 0 or array.size(ph1d) != sz_pp
    pp1d := array.copy(o_pH)
    pt1d := array.copy(o_bH)
    ph1d := array.new_bool(array.size(o_pH), true)

// Определяем текущую волну
[_wave1d, _waveFib1d, _isBull1d] = f_get_wave1d(pp1d, ph1d)
wave1d       := _wave1d
orient1dBull := _isBull1d
var bool wave1dFibOk = true
wave1dFibOk  := _waveFib1d

// ── ORIENT ФИЛЬТР ──
// Блокируем LONG если 1D на волне 5 (бычий) или C (бычий) — конец роста
// Блокируем SHORT если 1D на волне 5 (медвежий) или C (медвежий) — конец падения
// Блокируем только если волна 5/C И Fib подтверждён
wave1d_is_end     = wave1d == "5" or wave1d == "C"
wave1d_blockLong  = useOrientFilter and wave1d_is_end and wave1dFibOk and orient1dBull
wave1d_blockShort = useOrientFilter and wave1d_is_end and wave1dFibOk and not orient1dBull

// Итоговые фильтры с Orient
fBull = (useTF ? tBull : true) and not wave1d_blockLong
fBear = (useTF ? tBear : true) and not wave1d_blockShort

// ══════════════════════════════════════════════════════
// ORIENT — РИСОВАНИЕ ВОЛН 1D
// ══════════════════════════════════════════════════════
var line[]  ori1dLines  = array.new_line(0)
var label[] ori1dLabels = array.new_label(0)

if showOrient1D and barstate.islast
    for ln in ori1dLines
        line.delete(ln)
    array.clear(ori1dLines)
    for lb in ori1dLabels
        label.delete(lb)
    array.clear(ori1dLabels)

    n1d = array.size(pp1d)
    nShow = math.min(n1d, nWaves1d)
    st1d  = n1d - nShow

    for i = st1d to n1d - 1
        p0  = array.get(pp1d, i)
        t0  = array.get(pt1d, i)
        isH = array.get(ph1d, i)
        pos = n1d - i

        // Линия
        if i > st1d
            p_prev = array.get(pp1d, i-1)
            t_prev = array.get(pt1d, i-1)
            array.push(ori1dLines, line.new(t_prev, p_prev, t0, p0,
                 color=color.new(color.orange, 20), width=2, xloc=xloc.bar_index))

        // Метки
        lbl1d = ""
        clr1d = color.orange
        if nShow >= 6
            if orient1dBull
                lbl1d := pos == 6 ? "0D" : pos == 5 ? "1D" : pos == 4 ? "2D" :
                         pos == 3 ? "3D" : pos == 2 ? "4D" : pos == 1 ? wave1d + "D" : ""
            else
                lbl1d := pos == 6 ? "0D" : pos == 5 ? "1D" : pos == 4 ? "2D" :
                         pos == 3 ? "3D" : pos == 2 ? "4D" : pos == 1 ? wave1d + "D" : ""
        else if nShow >= 3
            lbl1d := pos == 3 ? "AD" : pos == 2 ? "BD" : pos == 1 ? wave1d + "D" : ""

        // Цвет последней волны — красный если 5 или C (блокирующая)
        if pos == 1
            clr1d := (wave1d == "5" or wave1d == "C") ? color.red : color.orange

        if lbl1d != ""
            st2 = isH ? label.style_label_down : label.style_label_up
            array.push(ori1dLabels, label.new(t0, p0, lbl1d,
                 color=color.new(clr1d, 55), textcolor=clr1d,
                 style=st2, size=size.small, xloc=xloc.bar_index))

// ══════════════════════════════════════════════════════
// СИГНАЛЫ
// ══════════════════════════════════════════════════════
var bool  sigBull   = false
var bool  sigBear   = false
var bool  sigBullW3 = false
var bool  sigBearW3 = false

var float vSLBull  = na, var float vTP1Bull = na
var float vTP2Bull = na, var float vTP3Bull = na
var float vSLBear  = na, var float vTP1Bear = na
var float vTP2Bear = na, var float vTP3Bear = na
var float vSLBW3   = na, var float vTP1BW3  = na, var float vTP2BW3 = na
var float vSLRW3   = na, var float vTP1RW3  = na, var float vTP2RW3 = na

var int lastB1 = -1, var int lastS1 = -1
var int lastB2 = -1, var int lastS2 = -1
var string statusText = "Ожидание..."

sigBull   := false
sigBear   := false
sigBullW3 := false
sigBearW3 := false

var line[]  ewL  = array.new_line(0)
var label[] ewLb = array.new_label(0)

clearEW() =>
    for l in ewL
        line.delete(l)
    for l in ewLb
        label.delete(l)
    array.clear(ewL)
    array.clear(ewLb)

n = array.size(pp)

// ══════════════════════════════════════════════════════
// LIMIT ЗОНЫ — переменные
// ══════════════════════════════════════════════════════
var float limW2BullHi = na, var float limW2BullLo = na
var float limW2BearHi = na, var float limW2BearLo = na
var float limW4BullHi = na, var float limW4BullLo = na
var float limW4BearHi = na, var float limW4BearLo = na

var float limW2BullSL = na, var float limW2BearSL = na
var float limW4BullSL = na, var float limW4BearSL = na

var float limW2BullTP1 = na, var float limW2BullTP2 = na
var float limW2BearTP1 = na, var float limW2BearTP2 = na
var float limW4BullTP1 = na, var float limW4BullTP2 = na
var float limW4BearTP1 = na, var float limW4BearTP2 = na

var bool limW2BullActive = false, var bool limW2BearActive = false
var bool limW4BullActive = false, var bool limW4BearActive = false
var bool limRTMBullActive = false, var bool limRTMBearActive = false

var int limW2BullAlertBar = -1, var int limW2BearAlertBar = -1
var int limW4BullAlertBar = -1, var int limW4BearAlertBar = -1
var int limRTMBullAlertBar = -1, var int limRTMBearAlertBar = -1

var box[] limBoxes = array.new_box(0)

clearLimBoxes() =>
    for b in limBoxes
        box.delete(b)
    array.clear(limBoxes)

// ══════════════════════════════════════════════════════
// W5 BULL
// ══════════════════════════════════════════════════════
if n >= 5 and fBull and fVol and rtmBullOK
    _i = n-1
    q0=array.get(pp,_i-4), q1=array.get(pp,_i-3), q2=array.get(pp,_i-2)
    q3=array.get(pp,_i-1), q4=array.get(pp,_i)
    c0=array.get(pb,_i-4), c1=array.get(pb,_i-3), c2=array.get(pb,_i-2)
    c3=array.get(pb,_i-1), c4=array.get(pb,_i)
    g0=array.get(ph,_i-4), g1=array.get(ph,_i-3), g2=array.get(ph,_i-2)
    g3=array.get(ph,_i-1), g4=array.get(ph,_i)
    if not g0 and g1 and not g2 and g3 and not g4
        [ok, w1, w3] = chkBull(q0,q1,q2,q3,q4)
        if ok and c4 != lastB1
            sigBull := true
            lastB1  := c4
            _rtmTag = isRBR ? " [RBR]" : isDBR ? " [DBR]" : ftrBull ? " [FTR]" : ercBull or ercBull[1] ? " [ERC]" : ""
            statusText := "✅ BULL W5" + _rtmTag + " | " + syminfo.ticker
            _buf = q4 * slBuf / 100
            vSLBull  := q4 - _buf
            vTP1Bull := q4 + w1 * 1.0
            vTP2Bull := q4 + w1 * 1.618
            vTP3Bull := q4 + w1 * 2.618
            _w3size = q3 - q2
            limW4BullHi := q3 - _w3size * (fibW4Lo / 100)
            limW4BullLo := q3 - _w3size * (fibW4Hi / 100)
            limW4BullSL := q2 - q2 * slBuf / 100
            limW4BullTP1 := q4 + w1 * 1.618
            limW4BullTP2 := q4 + w1 * 2.618
            limW4BullActive := true
            if barstate.islast
                clearEW()
                bR = c4 + 60
                array.push(ewL, line.new(c0,q0,c1,q1,color=color.new(#2196F3,0),width=2,xloc=xloc.bar_index))
                array.push(ewL, line.new(c1,q1,c2,q2,color=color.new(#FF9800,0),width=2,xloc=xloc.bar_index))
                array.push(ewL, line.new(c2,q2,c3,q3,color=color.new(#2196F3,0),width=2,xloc=xloc.bar_index))
                array.push(ewL, line.new(c3,q3,c4,q4,color=color.new(#FF9800,0),width=2,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c0,q0,"W0",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_up,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c1,q1,"W1",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_down,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c2,q2,"W2",color=color.new(#FF9800,70),textcolor=color.white,style=label.style_label_up,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c3,q3,"W3",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_down,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c4,q4,"W4↑"+_rtmTag,color=color.new(#00E676,70),textcolor=color.white,style=label.style_label_up,size=size.normal,xloc=xloc.bar_index))
                if showSL
                    array.push(ewL,line.new(c4,vSLBull,bR,vSLBull,color=color.new(#F44336,20),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vSLBull,"SL "+str.tostring(vSLBull,format.mintick),color=color.new(#F44336,70),textcolor=#F44336,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))
                if showTP
                    array.push(ewL,line.new(c4,vTP1Bull,bR,vTP1Bull,color=color.new(#00BCD4,40),style=line.style_dashed,width=1,xloc=xloc.bar_index))
                    array.push(ewL,line.new(c4,vTP2Bull,bR,vTP2Bull,color=color.new(#00BCD4,20),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewL,line.new(c4,vTP3Bull,bR,vTP3Bull,color=color.new(#00BCD4,10),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP1Bull,"TP1\n"+str.tostring(vTP1Bull,format.mintick),color=color.new(#00BCD4,75),textcolor=#00BCD4,style=label.style_label_left,size=size.tiny,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP2Bull,"TP2\n"+str.tostring(vTP2Bull,format.mintick),color=color.new(#00BCD4,55),textcolor=#00BCD4,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP3Bull,"TP3\n"+str.tostring(vTP3Bull,format.mintick),color=color.new(#00BCD4,40),textcolor=#00BCD4,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))

// ══════════════════════════════════════════════════════
// W5 BEAR
// ══════════════════════════════════════════════════════
if n >= 5 and fBear and fVol and rtmBearOK
    _i = n-1
    q0=array.get(pp,_i-4), q1=array.get(pp,_i-3), q2=array.get(pp,_i-2)
    q3=array.get(pp,_i-1), q4=array.get(pp,_i)
    c0=array.get(pb,_i-4), c1=array.get(pb,_i-3), c2=array.get(pb,_i-2)
    c3=array.get(pb,_i-1), c4=array.get(pb,_i)
    g0=array.get(ph,_i-4), g1=array.get(ph,_i-3), g2=array.get(ph,_i-2)
    g3=array.get(ph,_i-1), g4=array.get(ph,_i)
    if g0 and not g1 and g2 and not g3 and g4
        [ok, w1, w3] = chkBear(q0,q1,q2,q3,q4)
        if ok and c4 != lastS1
            sigBear := true
            lastS1  := c4
            _rtmTag = isDBD ? " [DBD]" : isRBD ? " [RBD]" : ftrBear ? " [FTR]" : ercBear or ercBear[1] ? " [ERC]" : ""
            statusText := "✅ BEAR W5" + _rtmTag + " | " + syminfo.ticker
            _buf = q4 * slBuf / 100
            vSLBear  := q4 + _buf
            vTP1Bear := q4 - w1 * 1.0
            vTP2Bear := q4 - w1 * 1.618
            vTP3Bear := q4 - w1 * 2.618
            _w3size = q2 - q3
            limW4BearHi := q3 + _w3size * (fibW4Lo / 100)
            limW4BearLo := q3 + _w3size * (fibW4Hi / 100)
            limW4BearSL := q2 + q2 * slBuf / 100
            limW4BearTP1 := q4 - w1 * 1.618
            limW4BearTP2 := q4 - w1 * 2.618
            limW4BearActive := true
            if barstate.islast
                clearEW()
                bR = c4 + 60
                array.push(ewL,line.new(c0,q0,c1,q1,color=color.new(#2196F3,0),width=2,xloc=xloc.bar_index))
                array.push(ewL,line.new(c1,q1,c2,q2,color=color.new(#FF9800,0),width=2,xloc=xloc.bar_index))
                array.push(ewL,line.new(c2,q2,c3,q3,color=color.new(#2196F3,0),width=2,xloc=xloc.bar_index))
                array.push(ewL,line.new(c3,q3,c4,q4,color=color.new(#FF9800,0),width=2,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c0,q0,"W0",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_down,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c1,q1,"W1",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_up,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c2,q2,"W2",color=color.new(#FF9800,70),textcolor=color.white,style=label.style_label_down,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c3,q3,"W3",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_up,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c4,q4,"W4↓"+_rtmTag,color=color.new(#FF5252,70),textcolor=color.white,style=label.style_label_down,size=size.normal,xloc=xloc.bar_index))
                if showSL
                    array.push(ewL,line.new(c4,vSLBear,bR,vSLBear,color=color.new(#F44336,20),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vSLBear,"SL "+str.tostring(vSLBear,format.mintick),color=color.new(#F44336,70),textcolor=#F44336,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))
                if showTP
                    array.push(ewL,line.new(c4,vTP1Bear,bR,vTP1Bear,color=color.new(#00BCD4,40),style=line.style_dashed,width=1,xloc=xloc.bar_index))
                    array.push(ewL,line.new(c4,vTP2Bear,bR,vTP2Bear,color=color.new(#00BCD4,20),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewL,line.new(c4,vTP3Bear,bR,vTP3Bear,color=color.new(#00BCD4,10),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP1Bear,"TP1\n"+str.tostring(vTP1Bear,format.mintick),color=color.new(#00BCD4,75),textcolor=#00BCD4,style=label.style_label_left,size=size.tiny,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP2Bear,"TP2\n"+str.tostring(vTP2Bear,format.mintick),color=color.new(#00BCD4,55),textcolor=#00BCD4,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP3Bear,"TP3\n"+str.tostring(vTP3Bear,format.mintick),color=color.new(#00BCD4,40),textcolor=#00BCD4,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))

// ══════════════════════════════════════════════════════
// W3 BULL
// ══════════════════════════════════════════════════════
if n >= 3 and not sigBull and fBull and fVol and rtmBullOK
    _i = n-1
    q0=array.get(pp,_i-2), q1=array.get(pp,_i-1), q2=array.get(pp,_i)
    c0=array.get(pb,_i-2), c1=array.get(pb,_i-1), c2=array.get(pb,_i)
    g0=array.get(ph,_i-2), g1=array.get(ph,_i-1), g2=array.get(ph,_i)
    if not g0 and g1 and not g2
        w1b = q1-q0
        w2b = q1-q2
        ok3 = w1b >= q0*w1MinPct/100 and w2b > 0 and q2 > q0
        ok3 := ok3 and (w2b/w1b*100) >= w2Min and (w2b/w1b*100) <= w2Max
        if ok3 and c2 != lastB2
            sigBullW3 := true
            lastB2    := c2
            _rtmTag = isRBR ? " [RBR]" : isDBR ? " [DBR]" : ftrBull ? " [FTR]" : ercBull or ercBull[1] ? " [ERC]" : ""
            statusText := "⚡ BULL W3" + _rtmTag + " | " + syminfo.ticker
            _buf3 = q0 * slBuf / 100
            vSLBW3  := q0 - _buf3
            vTP1BW3 := q2 + w1b * 1.618
            vTP2BW3 := q2 + w1b * 2.618
            limW2BullHi  := q1 - w1b * (fibW2Lo / 100)
            limW2BullLo  := q1 - w1b * (fibW2Hi / 100)
            limW2BullSL  := q0 - _buf3
            limW2BullTP1 := q2 + w1b * 1.618
            limW2BullTP2 := q2 + w1b * 2.618
            limW2BullActive := true
            if barstate.islast
                clearEW()
                bR = c2 + 60
                array.push(ewL,line.new(c0,q0,c1,q1,color=color.new(#2196F3,0),width=2,xloc=xloc.bar_index))
                array.push(ewL,line.new(c1,q1,c2,q2,color=color.new(#FF9800,0),width=2,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c0,q0,"W0",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_up,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c1,q1,"W1",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_down,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c2,q2,"W2→W3↑"+_rtmTag,color=color.new(#00E676,70),textcolor=color.white,style=label.style_label_up,size=size.normal,xloc=xloc.bar_index))
                if showSL
                    array.push(ewL,line.new(c2,vSLBW3,bR,vSLBW3,color=color.new(#F44336,20),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vSLBW3,"SL "+str.tostring(vSLBW3,format.mintick),color=color.new(#F44336,70),textcolor=#F44336,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))
                if showTP
                    array.push(ewL,line.new(c2,vTP1BW3,bR,vTP1BW3,color=color.new(#00BCD4,40),style=line.style_dashed,width=1,xloc=xloc.bar_index))
                    array.push(ewL,line.new(c2,vTP2BW3,bR,vTP2BW3,color=color.new(#00BCD4,20),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP1BW3,"1.618\n"+str.tostring(vTP1BW3,format.mintick),color=color.new(#00BCD4,75),textcolor=#00BCD4,style=label.style_label_left,size=size.tiny,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP2BW3,"2.618\n"+str.tostring(vTP2BW3,format.mintick),color=color.new(#00BCD4,55),textcolor=#00BCD4,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))

// ══════════════════════════════════════════════════════
// W3 BEAR
// ══════════════════════════════════════════════════════
if n >= 3 and not sigBear and fBear and fVol and rtmBearOK
    _i = n-1
    q0=array.get(pp,_i-2), q1=array.get(pp,_i-1), q2=array.get(pp,_i)
    c0=array.get(pb,_i-2), c1=array.get(pb,_i-1), c2=array.get(pb,_i)
    g0=array.get(ph,_i-2), g1=array.get(ph,_i-1), g2=array.get(ph,_i)
    if g0 and not g1 and g2
        w1b = q0-q1
        w2b = q2-q1
        ok3 = w1b >= q0*w1MinPct/100 and w2b > 0 and q2 < q0
        ok3 := ok3 and (w2b/w1b*100) >= w2Min and (w2b/w1b*100) <= w2Max
        if ok3 and c2 != lastS2
            sigBearW3 := true
            lastS2    := c2
            _rtmTag = isDBD ? " [DBD]" : isRBD ? " [RBD]" : ftrBear ? " [FTR]" : ercBear or ercBear[1] ? " [ERC]" : ""
            statusText := "⚡ BEAR W3" + _rtmTag + " | " + syminfo.ticker
            _buf3 = q0 * slBuf / 100
            vSLRW3  := q0 + _buf3
            vTP1RW3 := q2 - w1b * 1.618
            vTP2RW3 := q2 - w1b * 2.618
            limW2BearHi  := q1 + w1b * (fibW2Lo / 100)
            limW2BearLo  := q1 + w1b * (fibW2Hi / 100)
            limW2BearSL  := q0 + _buf3
            limW2BearTP1 := q2 - w1b * 1.618
            limW2BearTP2 := q2 - w1b * 2.618
            limW2BearActive := true
            if barstate.islast
                clearEW()
                bR = c2 + 60
                array.push(ewL,line.new(c0,q0,c1,q1,color=color.new(#2196F3,0),width=2,xloc=xloc.bar_index))
                array.push(ewL,line.new(c1,q1,c2,q2,color=color.new(#FF9800,0),width=2,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c0,q0,"W0",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_down,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c1,q1,"W1",color=color.new(#2196F3,70),textcolor=#2196F3,style=label.style_label_up,size=size.small,xloc=xloc.bar_index))
                array.push(ewLb,label.new(c2,q2,"W2→W3↓"+_rtmTag,color=color.new(#FF5252,70),textcolor=color.white,style=label.style_label_down,size=size.normal,xloc=xloc.bar_index))
                if showSL
                    array.push(ewL,line.new(c2,vSLRW3,bR,vSLRW3,color=color.new(#F44336,20),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vSLRW3,"SL "+str.tostring(vSLRW3,format.mintick),color=color.new(#F44336,70),textcolor=#F44336,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))
                if showTP
                    array.push(ewL,line.new(c2,vTP1RW3,bR,vTP1RW3,color=color.new(#00BCD4,40),style=line.style_dashed,width=1,xloc=xloc.bar_index))
                    array.push(ewL,line.new(c2,vTP2RW3,bR,vTP2RW3,color=color.new(#00BCD4,20),style=line.style_dashed,width=2,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP1RW3,"1.618\n"+str.tostring(vTP1RW3,format.mintick),color=color.new(#00BCD4,75),textcolor=#00BCD4,style=label.style_label_left,size=size.tiny,xloc=xloc.bar_index))
                    array.push(ewLb,label.new(bR,vTP2RW3,"2.618\n"+str.tostring(vTP2RW3,format.mintick),color=color.new(#00BCD4,55),textcolor=#00BCD4,style=label.style_label_left,size=size.small,xloc=xloc.bar_index))

if barstate.islast and not sigBull and not sigBear and not sigBullW3 and not sigBearW3
    clearEW()
    statusText := "Паттерн не найден (пивотов: " + str.tostring(n) + ")"

// ══════════════════════════════════════════════════════
// LIMIT ЗОНЫ — РИСОВАНИЕ
// ══════════════════════════════════════════════════════
inZone(float zHi, float zLo) =>
    not na(zHi) and not na(zLo) and low <= zHi and high >= zLo

if showLimitZones and barstate.islast
    clearLimBoxes()
    _ext = bar_index + 80

    if showFibW2 and limW2BullActive and not na(limW2BullHi) and not na(limW2BullLo)
        array.push(limBoxes, box.new(bar_index-50, limW2BullHi, _ext, limW2BullLo,
             border_color=color.new(color.lime,20), bgcolor=color.new(color.lime,88),
             text="LIMIT LONG W2\n"+str.tostring(limW2BullLo,format.mintick)+"–"+str.tostring(limW2BullHi,format.mintick),
             text_color=color.lime, text_size=size.small, xloc=xloc.bar_index))

    if showFibW2 and limW2BearActive and not na(limW2BearHi) and not na(limW2BearLo)
        array.push(limBoxes, box.new(bar_index-50, limW2BearHi, _ext, limW2BearLo,
             border_color=color.new(color.red,20), bgcolor=color.new(color.red,88),
             text="LIMIT SHORT W2\n"+str.tostring(limW2BearLo,format.mintick)+"–"+str.tostring(limW2BearHi,format.mintick),
             text_color=color.red, text_size=size.small, xloc=xloc.bar_index))

    if showFibW4 and limW4BullActive and not na(limW4BullHi) and not na(limW4BullLo)
        array.push(limBoxes, box.new(bar_index-50, limW4BullHi, _ext, limW4BullLo,
             border_color=color.new(color.aqua,20), bgcolor=color.new(color.aqua,88),
             text="LIMIT LONG W4\n"+str.tostring(limW4BullLo,format.mintick)+"–"+str.tostring(limW4BullHi,format.mintick),
             text_color=color.aqua, text_size=size.small, xloc=xloc.bar_index))

    if showFibW4 and limW4BearActive and not na(limW4BearHi) and not na(limW4BearLo)
        array.push(limBoxes, box.new(bar_index-50, limW4BearHi, _ext, limW4BearLo,
             border_color=color.new(color.orange,20), bgcolor=color.new(color.orange,88),
             text="LIMIT SHORT W4\n"+str.tostring(limW4BearLo,format.mintick)+"–"+str.tostring(limW4BearHi,format.mintick),
             text_color=color.orange, text_size=size.small, xloc=xloc.bar_index))

    if showRTMlimit and baseFound and (isRBR or isDBR) and fBull
        array.push(limBoxes, box.new(bar_index-rtmLookback, baseH, _ext, baseL,
             border_color=color.new(#00BCD4,30), bgcolor=color.new(#00BCD4,85),
             text="LIMIT LONG RTM\n"+str.tostring(baseL,format.mintick)+"–"+str.tostring(baseH,format.mintick),
             text_color=#00BCD4, text_size=size.small, xloc=xloc.bar_index))

    if showRTMlimit and baseFound and (isDBD or isRBD) and fBear
        array.push(limBoxes, box.new(bar_index-rtmLookback, baseH, _ext, baseL,
             border_color=color.new(#CE93D8,30), bgcolor=color.new(#CE93D8,85),
             text="LIMIT SHORT RTM\n"+str.tostring(baseL,format.mintick)+"–"+str.tostring(baseH,format.mintick),
             text_color=#CE93D8, text_size=size.small, xloc=xloc.bar_index))

// ══════════════════════════════════════════════════════
// LIMIT АЛЕРТЫ — ТРИГГЕРЫ
// ══════════════════════════════════════════════════════
limW2BullHit  = useLimitAlert and showFibW2 and limW2BullActive and inZone(limW2BullHi, limW2BullLo) and bar_index != limW2BullAlertBar
limW2BearHit  = useLimitAlert and showFibW2 and limW2BearActive and inZone(limW2BearHi, limW2BearLo) and bar_index != limW2BearAlertBar
limW4BullHit  = useLimitAlert and showFibW4 and limW4BullActive and inZone(limW4BullHi, limW4BullLo) and bar_index != limW4BullAlertBar
limW4BearHit  = useLimitAlert and showFibW4 and limW4BearActive and inZone(limW4BearHi, limW4BearLo) and bar_index != limW4BearAlertBar
limRTMBullHit = useLimitAlert and showRTMlimit and baseFound and (isRBR or isDBR) and fBull and inZone(baseH, baseL) and bar_index != limRTMBullAlertBar
limRTMBearHit = useLimitAlert and showRTMlimit and baseFound and (isDBD or isRBD) and fBear and inZone(baseH, baseL) and bar_index != limRTMBearAlertBar

if limW2BullHit
    limW2BullAlertBar := bar_index
if limW2BearHit
    limW2BearAlertBar := bar_index
if limW4BullHit
    limW4BullAlertBar := bar_index
if limW4BearHit
    limW4BearAlertBar := bar_index
if limRTMBullHit
    limRTMBullAlertBar := bar_index
if limRTMBearHit
    limRTMBearAlertBar := bar_index

// ── Визуальные метки ──
plotshape(limW2BullHit,  title="LIM LONG W2",   style=shape.triangleup,   location=location.belowbar, color=color.new(color.lime,0),   size=size.small, text="LIM↑W2")
plotshape(limW2BearHit,  title="LIM SHORT W2",  style=shape.triangledown, location=location.abovebar, color=color.new(color.red,0),    size=size.small, text="LIM↓W2")
plotshape(limW4BullHit,  title="LIM LONG W4",   style=shape.triangleup,   location=location.belowbar, color=color.new(color.aqua,0),   size=size.small, text="LIM↑W4")
plotshape(limW4BearHit,  title="LIM SHORT W4",  style=shape.triangledown, location=location.abovebar, color=color.new(color.orange,0), size=size.small, text="LIM↓W4")
plotshape(limRTMBullHit, title="LIM LONG RTM",  style=shape.triangleup,   location=location.belowbar, color=color.new(#00BCD4,0),      size=size.small, text="LIM↑RTM")
plotshape(limRTMBearHit, title="LIM SHORT RTM", style=shape.triangledown, location=location.abovebar, color=color.new(#CE93D8,0),      size=size.small, text="LIM↓RTM")

// ══════════════════════════════════════════════════════
// СТРЕЛКИ СИГНАЛОВ
// ══════════════════════════════════════════════════════
plotshape(sigBull,   title="BULL W5", style=shape.triangleup,   location=location.belowbar, color=color.new(color.lime,0),   size=size.normal, text="W5↑")
plotshape(sigBear,   title="BEAR W5", style=shape.triangledown, location=location.abovebar, color=color.new(color.red,0),    size=size.normal, text="W5↓")
plotshape(sigBullW3, title="BULL W3", style=shape.triangleup,   location=location.belowbar, color=color.new(color.aqua,0),   size=size.small,  text="W3↑")
plotshape(sigBearW3, title="BEAR W3", style=shape.triangledown, location=location.abovebar, color=color.new(color.orange,0), size=size.small,  text="W3↓")

plotshape(showCandles and pinBull() and (sigBull or sigBullW3), title="Pin↑", style=shape.labelup,   location=location.belowbar, color=color.new(color.lime,40),   size=size.tiny, text="📍", offset=-1)
plotshape(showCandles and pinBear() and (sigBear or sigBearW3), title="Pin↓", style=shape.labeldown, location=location.abovebar, color=color.new(color.red,40),    size=size.tiny, text="📍", offset=-1)
plotshape(showCandles and engBull() and (sigBull or sigBullW3), title="Eng↑", style=shape.labelup,   location=location.belowbar, color=color.new(color.green,40),  size=size.tiny, text="⚡", offset=-1)
plotshape(showCandles and engBear() and (sigBear or sigBearW3), title="Eng↓", style=shape.labeldown, location=location.abovebar, color=color.new(color.maroon,40), size=size.tiny, text="⚡", offset=-1)

// ══════════════════════════════════════════════════════
// EXIT СТРЕЛКИ
// ══════════════════════════════════════════════════════
plotshape(exitLong,  title="EXIT Long",  style=shape.xcross, location=location.belowbar, color=color.new(color.yellow,0), size=size.small, text="EXIT↑")
plotshape(exitShort, title="EXIT Short", style=shape.xcross, location=location.abovebar, color=color.new(color.yellow,0), size=size.small, text="EXIT↓")

// ══════════════════════════════════════════════════════
// АЛЕРТЫ
// ══════════════════════════════════════════════════════
if sigBull and not na(vSLBull)
    alert('{"symbol":"' + syminfo.ticker + '","action":"LONG","signal":"EW Bull W5","tf":240,"order_type":"MARKET","sl":' + str.tostring(vSLBull,"#.########") + ',"tp1":' + str.tostring(vTP1Bull,"#.########") + ',"tp2":' + str.tostring(vTP2Bull,"#.########") + ',"tp3":' + str.tostring(vTP3Bull,"#.########") + '}', alert.freq_once_per_bar_close)

if sigBear and not na(vSLBear)
    alert('{"symbol":"' + syminfo.ticker + '","action":"SHORT","signal":"EW Bear W5","tf":240,"order_type":"MARKET","sl":' + str.tostring(vSLBear,"#.########") + ',"tp1":' + str.tostring(vTP1Bear,"#.########") + ',"tp2":' + str.tostring(vTP2Bear,"#.########") + ',"tp3":' + str.tostring(vTP3Bear,"#.########") + '}', alert.freq_once_per_bar_close)

if sigBullW3 and not na(vSLBW3)
    alert('{"symbol":"' + syminfo.ticker + '","action":"LONG","signal":"EW Bull W3","tf":240,"order_type":"MARKET","sl":' + str.tostring(vSLBW3,"#.########") + ',"tp1":' + str.tostring(vTP1BW3,"#.########") + ',"tp2":' + str.tostring(vTP2BW3,"#.########") + '}', alert.freq_once_per_bar_close)

if sigBearW3 and not na(vSLRW3)
    alert('{"symbol":"' + syminfo.ticker + '","action":"SHORT","signal":"EW Bear W3","tf":240,"order_type":"MARKET","sl":' + str.tostring(vSLRW3,"#.########") + ',"tp1":' + str.tostring(vTP1RW3,"#.########") + ',"tp2":' + str.tostring(vTP2RW3,"#.########") + '}', alert.freq_once_per_bar_close)

if exitLong
    alert('{"symbol":"' + syminfo.ticker + '","action":"EXIT_LONG","signal":"EXIT Bull 15m","tf":240}', alert.freq_once_per_bar_close)

if exitShort
    alert('{"symbol":"' + syminfo.ticker + '","action":"EXIT_SHORT","signal":"EXIT Bear 15m","tf":240}', alert.freq_once_per_bar_close)

if limW2BullHit and not na(limW2BullSL) and not na(limW2BullTP1)
    alert('{"symbol":"' + syminfo.ticker + '","action":"LONG","signal":"LIMIT Bull W2","tf":240,"order_type":"LIMIT","limit_price":' + str.tostring(limW2BullLo,"#.########") + ',"zone_hi":' + str.tostring(limW2BullHi,"#.########") + ',"zone_lo":' + str.tostring(limW2BullLo,"#.########") + ',"sl":' + str.tostring(limW2BullSL,"#.########") + ',"tp1":' + str.tostring(limW2BullTP1,"#.########") + ',"tp2":' + str.tostring(limW2BullTP2,"#.########") + '}', alert.freq_once_per_bar_close)

if limW2BearHit and not na(limW2BearSL) and not na(limW2BearTP1)
    alert('{"symbol":"' + syminfo.ticker + '","action":"SHORT","signal":"LIMIT Bear W2","tf":240,"order_type":"LIMIT","limit_price":' + str.tostring(limW2BearHi,"#.########") + ',"zone_hi":' + str.tostring(limW2BearHi,"#.########") + ',"zone_lo":' + str.tostring(limW2BearLo,"#.########") + ',"sl":' + str.tostring(limW2BearSL,"#.########") + ',"tp1":' + str.tostring(limW2BearTP1,"#.########") + ',"tp2":' + str.tostring(limW2BearTP2,"#.########") + '}', alert.freq_once_per_bar_close)

if limW4BullHit and not na(limW4BullSL) and not na(limW4BullTP1)
    alert('{"symbol":"' + syminfo.ticker + '","action":"LONG","signal":"LIMIT Bull W4","tf":240,"order_type":"LIMIT","limit_price":' + str.tostring(limW4BullLo,"#.########") + ',"zone_hi":' + str.tostring(limW4BullHi,"#.########") + ',"zone_lo":' + str.tostring(limW4BullLo,"#.########") + ',"sl":' + str.tostring(limW4BullSL,"#.########") + ',"tp1":' + str.tostring(limW4BullTP1,"#.########") + ',"tp2":' + str.tostring(limW4BullTP2,"#.########") + '}', alert.freq_once_per_bar_close)

if limW4BearHit and not na(limW4BearSL) and not na(limW4BearTP1)
    alert('{"symbol":"' + syminfo.ticker + '","action":"SHORT","signal":"LIMIT Bear W4","tf":240,"order_type":"LIMIT","limit_price":' + str.tostring(limW4BearHi,"#.########") + ',"zone_hi":' + str.tostring(limW4BearHi,"#.########") + ',"zone_lo":' + str.tostring(limW4BearLo,"#.########") + ',"sl":' + str.tostring(limW4BearSL,"#.########") + ',"tp1":' + str.tostring(limW4BearTP1,"#.########") + ',"tp2":' + str.tostring(limW4BearTP2,"#.########") + '}', alert.freq_once_per_bar_close)

if limRTMBullHit and baseFound and not na(baseH) and not na(baseL)
    alert('{"symbol":"' + syminfo.ticker + '","action":"LONG","signal":"LIMIT Bull RTM","tf":240,"order_type":"LIMIT","limit_price":' + str.tostring((baseH+baseL)/2,"#.########") + ',"zone_hi":' + str.tostring(baseH,"#.########") + ',"zone_lo":' + str.tostring(baseL,"#.########") + ',"sl":' + str.tostring(baseL*(1-slBuf/100),"#.########") + '}', alert.freq_once_per_bar_close)

if limRTMBearHit and baseFound and not na(baseH) and not na(baseL)
    alert('{"symbol":"' + syminfo.ticker + '","action":"SHORT","signal":"LIMIT Bear RTM","tf":240,"order_type":"LIMIT","limit_price":' + str.tostring((baseH+baseL)/2,"#.########") + ',"zone_hi":' + str.tostring(baseH,"#.########") + ',"zone_lo":' + str.tostring(baseL,"#.########") + ',"sl":' + str.tostring(baseH*(1+slBuf/100),"#.########") + '}', alert.freq_once_per_bar_close)

// ══════════════════════════════════════════════════════
// ПАНЕЛЬ СТАТУСА
// ══════════════════════════════════════════════════════
var table panel = na
if barstate.islast and showPanel
    table.delete(panel)
    panel := table.new(position.top_right, 2, 11,
         bgcolor=color.new(color.navy,75), border_width=1,
         border_color=color.new(color.gray,60))

    tc = sigBull or sigBullW3 ? color.lime : sigBear or sigBearW3 ? color.red : color.gray
    pc = sigBull or sigBullW3 ? color.new(color.lime,80) : sigBear or sigBearW3 ? color.new(color.red,80) : color.new(color.gray,80)

    table.cell(panel,0,0,"Статус",    text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,0,statusText,  text_color=tc,          bgcolor=pc,                       text_size=size.small)
    table.cell(panel,0,1,"Тренд 1D",  text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,1,useTF ? (tBull ? "▲ BULL" : "▼ BEAR") : "ВЫКЛ",
         text_color=useTF?(tBull?color.lime:color.red):color.gray,
         bgcolor=color.new(color.navy,60), text_size=size.small)

    // Строка волны 1D — ключевая новинка v25
    _wClr     = (wave1d == "5" or wave1d == "C") ? color.red : wave1d == "—" ? color.gray : color.lime
    _wFibStr  = wave1d == "—" ? "" : wave1dFibOk ? " ✓" : " ?"
    _wBlocked = wave1d_blockLong ? " ⛔LONG" : wave1d_blockShort ? " ⛔SHORT" : ""
    table.cell(panel,0,2,"Волна 1D",  text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,2,wave1d + "D" + _wFibStr + _wBlocked, text_color=_wClr, bgcolor=color.new(color.navy,60), text_size=size.small)

    table.cell(panel,0,3,"Volume",    text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,3,useVol ? (vSurge ? "🔥 SURGE" : "обычный") : "ВЫКЛ",
         text_color=useVol?(vSurge?color.yellow:color.gray):color.gray,
         bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,0,4,"Пивотов",   text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,4,str.tostring(n), text_color=color.white, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,0,5,"Задержка",  text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,5,str.tostring(zzLen)+"б (4H)", text_color=color.orange, bgcolor=color.new(color.navy,60), text_size=size.small)

    _rtmZone = isRBR ? "RBR" : isDBD ? "DBD" : isRBD ? "RBD" : isDBR ? "DBR" : "—"
    _rtmClr  = isRBR or isDBR ? color.lime : isDBD or isRBD ? color.red : color.gray
    table.cell(panel,0,6,"RTM зона",  text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,6,_rtmZone,    text_color=_rtmClr,    bgcolor=color.new(color.navy,60), text_size=size.small)

    _ercStr = ercBull ? "ERC↑" : ercBear ? "ERC↓" : ftrBull ? "FTR↑" : ftrBear ? "FTR↓" : "—"
    _ercClr = ercBull or ftrBull ? color.lime : ercBear or ftrBear ? color.red : color.gray
    table.cell(panel,0,7,"ERC/FTR",   text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,7,_ercStr,     text_color=_ercClr,    bgcolor=color.new(color.navy,60), text_size=size.small)

    _limLong     = limW2BullActive or limW4BullActive ? "✅ LONG"  : "—"
    _limShort    = limW2BearActive or limW4BearActive ? "✅ SHORT" : "—"
    _limLongClr  = limW2BullActive or limW4BullActive ? color.lime : color.gray
    _limShortClr = limW2BearActive or limW4BearActive ? color.red  : color.gray
    table.cell(panel,0,8,"Limit Long",  text_color=color.gray,   bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,8,_limLong,      text_color=_limLongClr,  bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,0,9,"Limit Short", text_color=color.gray,   bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,9,_limShort,     text_color=_limShortClr, bgcolor=color.new(color.navy,60), text_size=size.small)

    // Orient статус
    _oriClr = useOrientFilter ? color.lime : color.gray
    table.cell(panel,0,10,"Orient",    text_color=color.gray, bgcolor=color.new(color.navy,60), text_size=size.small)
    table.cell(panel,1,10,useOrientFilter ? "✅ ON" : "ВЫКЛ", text_color=_oriClr, bgcolor=color.new(color.navy,60), text_size=size.small)

// EMA визуализация
plot(useTF ? e1hF : na, title="EMA50 1D",  color=color.new(color.yellow,40), linewidth=1)
plot(useTF ? e1hS : na, title="EMA200 1D", color=color.new(color.white,40),  linewidth=1)
