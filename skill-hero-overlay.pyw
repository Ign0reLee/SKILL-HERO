#!/usr/bin/env python3
# Skill Hero — Claude Desktop 오버레이.
# Claude Desktop 앱 위에 '항상 위 + 투명배경 + 클릭통과' 창으로 떠서, 채팅 위에서 용사들이
# 클로드 모양 적과 싸운다. skill-hero-state.json 을 읽어 실시간 연동(없으면 데모 자동전투).
# 의존성 0 (파이썬 표준 tkinter). 실행:  pythonw skill-hero-overlay.pyw   (또는 더블클릭)
import sys, os, json, math, random, re

# 상태 파일은 훅과 공유하는 공용 경로(플러그인 설치 위치와 무관). SKILL_HERO_STATE 로 덮어쓰기 가능.
STATE = os.environ.get("SKILL_HERO_STATE") or os.path.join(os.path.expanduser("~"), ".claude", "skill-hero-state.json")
# SSH/원격: 로컬에서 오버레이를 띄우고 포워딩된 URL로 상태를 읽을 수 있음 (예: http://localhost:8777/skill-hero-state.json)
STATE_URL = os.environ.get("SKILL_HERO_STATE_URL")
TRANSP = "#010101"          # 이 색은 투명 처리(클릭 통과)
AW, AH = 720, 180           # 전장(이동 가능, 캐릭터만) 창 크기

COL = {"K":"#ffd9a0","E":"#26203a","W":"#f8fafc","B":"#7c4a21","Y":"#fde047",
       "C":"#d97757","c":"#b45c3a","L":"#3a4252","O":"#26201a"}
SPR = {
 "knight":["  MMMM  "," MmmmmmM"," MKKKKKM"," KEKKKEK"," KKKKKKK","  SBBS  "," SBBBBS "," bBBBBb ","  BBBB  ","  L  L  ","  L  L  ","  O  O  "],
 "archer":["   MM   ","  MMMm  "," MMKKm  "," MKEKKm ","  KKKK  ","  SBBS  "," BBBBBB "," bBBBBb ","  BBBB  ","  L  L  ","  L L   ","  O  O  "],
 "mage":  ["   M    ","  MMM   "," MMMMM  ","  KEK   ","  KKK   ","  SBS   "," SBBBS  "," BBBBB  "," bBBBb  "," BBBBB  "," BBBBB  ","  OOO   "]}
ICONS = {
 "sword":["   X   ","   X   ","   X   ","   X   ","  WXW  ","   B   ","   B   "],
 "bow":  ["  X "," XS "," X S"," X=A"," X S"," XS ","  X "],
 "staff":["  XXX  "," XYYYX ","  XXX  ","   B   ","   B   ","   B   ","   B   "],
 "shield":[" XXXXX ","XWXXXWX","XXXXXXX","XXXXXXX"," XXXXX ","  XXX  ","   X   "],
 "armor":[" X   X "," XXXXX ","XXXXXXX","XXXXXXX","XXXXXXX"," XXXXX ","  XXX  "]}
CLAUDE_G = ["..CCCCCCCCCCCC..","..CCCCCCCCCCCC..","..CCCCCCCCCCCC..","..CCWCCCCCCWCC..","..CCWCCCCCCWCC..","..CCWCCCCCCWCC..",
 "CCCCCCCCCCCCCCCC","CCCCCCCCCCCCCCCC","CCCCCCCCCCCCCCCC","..CCCCCCCCCCCC..","..CCCCCCCCCCCC..","...C.C....C.C...","...C.C....C.C...","...C.C....C.C..."]
SKINS = ["#ffd9a0","#f1bd92","#e0a878","#c69a6a","#b07a4e"]
CLASSES = {
 "knight":{"melee":True,"weapon":"sword","trim":"#c8d2dc","body":[("#3b82f6","#1e40af"),("#ef4444","#991b1b"),("#22c55e","#15803d"),("#eab308","#a16207")],"hat":[("#c8d2dc","#7f8c99"),("#e5b7a0","#a06a52")]},
 "archer":{"melee":False,"weapon":"bow","trim":"#7c4a21","body":[("#16a34a","#14532d"),("#65a30d","#3f6212"),("#0d9488","#115e59"),("#b45309","#78350f")],"hat":[("#15803d","#0f5132"),("#4d7c0f","#365314")]},
 "mage":  {"melee":False,"weapon":"staff","trim":"#fde047","body":[("#7c3aed","#5b21b6"),("#2563eb","#1e3a8a"),("#db2777","#9d174d"),("#0891b2","#155e75")],"hat":[("#7c3aed","#4c1d95"),("#1d4ed8","#1e3a8a")]}}
CKEYS = ["knight","archer","mage"]
CLSKO = {"knight":"기사","archer":"궁수","mage":"법사"}
# 스킬 id -> (아이콘, 색, 표시명, ATK)
CAT = {"autopilot":("sword","#60a5fa","Autopilot",14),"ultrawork":("sword","#f472b6","Ultrawork",16),
 "ralph":("staff","#a78bfa","Ralph",10),"ralplan":("staff","#fbbf24","Ralplan",9),
 "team":("staff","#34d399","Team",8),"deep-research":("staff","#c084fc","Research",11),
 "review":("shield","#22d3ee","Review",6),"verify":("armor","#4ade80","Verify",7)}
WPOS = {"sword":(35,8),"staff":(38,2),"bow":(33,15)}

def shade(hexc, f):
    n = int(hexc[1:], 16)
    return "#%02x%02x%02x" % (int(((n>>16)&255)*f), int(((n>>8)&255)*f), int((n&255)*f))
def classFor(name, i):
    n = str(name or "").lower()
    if re.search(r"verif|review|plan|research|writ|scien|arch|analy|critic|doc|secur", n): return "mage"
    if re.search(r"explor|scout|trac|debug|search|qa|test", n): return "archer"
    if re.search(r"exec|main|team|git|simpl|build|design", n): return "knight"
    return CKEYS[i % 3]

# ---------- state ----------
PW, ROWH = 150, 22            # 고정 창(메뉴+장비) 폭 / 행 높이
SKILL_LIST = ["autopilot","ultrawork","ralph","ralplan","team","deep-research","review","verify"]
heroes, proj, pops = [], [], []
enemy = {"hp":0,"hpMax":100,"alive":False,"hit":0,"dead":0,"x":772,"y":104}
phase, label, mode = "idle", "대기 중...", "demo"
t, banner, bannerTxt = 0, 0, ""
di = dt = 0
dEntered = False
dragging = None               # 드래그 중인 스킬 id
curx = cury = 0               # 커서 위치
moving = False; mox = moy = 0 # 전장 창 이동 상태
mmoving = False; mmx = mmy = 0 # 메뉴 창 이동 상태

def makeHero(i, cls=None):
    cls = cls or CKEYS[i % 3]; c = CLASSES[cls]
    body = random.choice(c["body"]); hat = random.choice(c["hat"]); skin = random.choice(SKINS)
    return {"slot":i,"cls":cls,"melee":c["melee"],"x":0,"y":96,"bob":i*9,"atkT":0,"eq":[],"pending":None,
        "name":(["MAIN","EXEC","TEAM","SCOUT"][i] if i < 4 else "A%d"%(i+1)),
        "pal":{"M":hat[0],"m":hat[1],"K":skin,"E":COL["E"],"B":body[0],"b":body[1],"S":c["trim"],"L":COL["L"],"O":COL["O"]},
        "wcol":("#e3e9f0" if cls=="knight" else hat[0])}
def layout():  # 전장 창 안에서 근접=앞(적 가까이), 원거리=뒤(왼쪽)
    mi = ri = 0
    for h in heroes:
        if h["melee"]: h["x"] = AW-300 + mi*78; h["y"] = AH-66; mi += 1
        else:          h["x"] = 60    + ri*82; h["y"] = AH-92; ri += 1
def setHeroes(n):
    n = max(1, min(4, n))
    while len(heroes) < n: heroes.append(makeHero(len(heroes)))
    del heroes[n:]; layout()
def spawnEnemy(hp=100):
    enemy.update(hpMax=hp, hp=hp, alive=True, dead=0, hit=0); proj.clear()
def lastBy(h, types):
    r = None
    for sid in h["eq"]:
        if CAT[sid][0] in types: r = sid
    return r
def nearest_hero(x):
    best, bd = None, 1e9
    for h in heroes:
        d = abs(h["x"] + 20 - x)
        if d < bd: bd, best = d, h
    return best
def equip(h, sid):
    if h and sid in CAT and sid not in h["eq"]:
        h["eq"].append(sid)
        pops.append({"x":h["x"]+20,"y":h["y"]-6,"txt":"장착! "+CAT[sid][2],"col":CAT[sid][1],"life":34,"vy":-0.6,"big":False})

# ---------- combat ----------
def attack(h, sid):
    if not enemy["alive"] or h["atkT"] > 0: return
    h["atkT"] = 12
    s = {"nm":CAT[sid][2],"at":CAT[sid][3],"col":CAT[sid][1]} if sid else {"nm":"공격","at":6,"col":"#fff"}
    if h["melee"]: h["pending"] = s
    else: proj.append({"x":h["x"]+40,"y":h["y"]+30,"s":s,"col":s["col"],"mage":h["cls"]=="mage","life":0})
def applyHit(s):
    if not enemy["alive"]: return
    enemy["hp"] = max(0, enemy["hp"] - s["at"]); enemy["hit"] = 6
    pops.append({"x":enemy["x"]+random.randint(-16,16),"y":enemy["y"]-18,"txt":"-%d"%s["at"],"col":"#ffd166","life":30,"vy":-0.7,"big":False})
    pops.append({"x":enemy["x"],"y":enemy["y"]-40,"txt":s["nm"],"col":s["col"],"life":30,"vy":-0.7,"big":False})
    if enemy["hp"] <= 0 and enemy["dead"] == 0: victory()
def victory():
    global banner, bannerTxt
    enemy["dead"] = 1; banner = 120; bannerTxt = "CLEAR!"
    pops.append({"x":enemy["x"],"y":enemy["y"]-54,"txt":"★ 결함 처치 ★","col":"#46e0a0","life":54,"vy":-0.6,"big":True})
def finish():
    for h in heroes:
        sid = h["eq"][-1] if h["eq"] else None
        s = {"nm":CAT[sid][2],"at":max(40,CAT[sid][3]),"col":CAT[sid][1]} if sid else {"nm":"FINISH","at":40,"col":"#fff"}
        h["atkT"] = 12
        if h["melee"]: h["pending"] = s
        else: proj.append({"x":h["x"]+40,"y":h["y"]+30,"s":s,"col":s["col"],"mage":h["cls"]=="mage","life":0})
def updateProj():
    for p in proj:
        dx = enemy["x"]-p["x"]; dy = enemy["y"]-p["y"]; d = math.hypot(dx, dy) or 1
        p["x"] += dx/d*10; p["y"] += dy/d*10; p["life"] += 1
        if d < 10:
            p["hit"] = True
            if p["s"]: applyHit(p["s"])
            else: enemy["hit"] = 4; spark()         # 코스메틱(앰비언트) 명중 = 불꽃만
    proj[:] = [p for p in proj if not p.get("hit") and p["life"] < 70]
def spark():  # 작은 타격 불꽃 (HP 변화 없음)
    pops.append({"x":enemy["x"]+random.randint(-18,18),"y":enemy["y"]+random.randint(-12,12),
                 "txt":random.choice(["✦","✧","＊"]),"col":"#ffe7c2","life":11,"vy":-0.3,"big":False})
def ambientAttack():  # 작업 중 끊임없이 싸우는 연출 (실제 HP는 안 깎음)
    idle = [h for h in heroes if h["atkT"] == 0]
    if not idle: return
    h = random.choice(idle); h["atkT"] = 12
    if h["melee"]: h["pending"] = {"cosmetic": True}
    else:
        col = CAT[h["eq"][-1]][1] if h["eq"] else "#cbd5e1"
        proj.append({"x":h["x"]+40,"y":h["y"]+30,"s":None,"col":col,"mage":h["cls"]=="mage","life":0})

DSEQ = [("idle","대기 중...",40,None,False),
        ("thinking","사고 중 (Thinking)",90,"spawn",False),
        ("tool","도구 실행 (Tool Use)",150,None,True),
        ("baking","빌드 중 (Baking)",120,None,True),
        ("done","결함 처치 완료!",120,"finish",False)]
def demo():
    global di, dt, dEntered, phase, label
    p, l, dur, onk, atk = DSEQ[di]
    if not dEntered:
        phase, label = p, l
        if onk == "spawn": setHeroes(3); spawnEnemy(120)
        elif onk == "finish": finish()
        dEntered = True
    if atk and enemy["alive"] and t % 26 == 0:
        h = random.choice(heroes); attack(h, random.choice(h["eq"]) if h["eq"] else None)
    dt += 1
    if dt >= dur: dt = 0; di = (di+1) % len(DSEQ); dEntered = False

def update():
    global t, banner
    t += 1
    for h in heroes:
        if h["atkT"] > 0:
            h["atkT"] -= 1
            if h["atkT"] == 6 and h["melee"] and h["pending"]:
                if h["pending"].get("cosmetic"): enemy["hit"] = 4; spark()
                else: applyHit(h["pending"])
                h["pending"] = None
    updateProj()
    if enemy["hit"] > 0: enemy["hit"] -= 1
    if enemy["dead"] > 0:
        enemy["dead"] += 1
        if enemy["dead"] > 26: enemy["alive"] = False; enemy["dead"] = 0; proj.clear()
    for p in pops: p["y"] += p["vy"]; p["life"] -= 1
    pops[:] = [p for p in pops if p["life"] > 0]
    if banner > 0: banner -= 1
    if mode == "demo": demo()
    elif enemy["alive"] and not enemy["dead"] and phase in ("thinking","tool","baking") and t % 14 == 0:
        ambientAttack()   # LIVE: 작업 중 끊임없이 교전

# ---------- live link ----------
def read_state():
    try:
        if STATE_URL:                       # 원격: 포워딩된 서버에서 가져오기
            import urllib.request
            with urllib.request.urlopen(STATE_URL, timeout=1) as r:
                return json.loads(r.read().decode("utf-8"))
        with open(STATE, encoding="utf-8") as f: return json.load(f)
    except Exception:
        return None
def syncAgents(lst):
    names = [(a.get("name") if isinstance(a, dict) and a.get("name") else "A%d"%(i+1)) for i, a in enumerate(lst)]
    n = max(1, min(4, len(names))); old = list(heroes); heroes.clear()
    for i in range(n):
        cls = classFor(names[i], i); prev = old[i] if i < len(old) else None
        if prev and prev["cls"] == cls: h = prev
        else:
            h = makeHero(i, cls)
            if prev: h["eq"] = prev["eq"]
        h["name"] = str(names[i]).upper()[:6]; h["slot"] = i; heroes.append(h)
    layout()
def apply_state(st):
    global phase, label
    if not isinstance(st, dict): return
    ag = st.get("agents")
    if isinstance(ag, list): syncAgents(ag)
    elif isinstance(ag, int): setHeroes(ag)   # agents 없으면 현 인원 유지(부분 업데이트 안전)
    sk = st.get("skills")
    if isinstance(sk, list):
        for h in heroes:
            for sid in sk:
                if sid in CAT and sid not in h["eq"]: h["eq"].append(sid)
    phase = st.get("phase", "thinking")
    lmap = {"thinking":"사고 중 (Thinking)","tool":"도구 실행 (Tool Use)","baking":"빌드 중 (Baking)","done":"결함 처치 완료!","idle":"대기 중..."}
    label = st.get("label") or lmap.get(phase, phase)
    hp = st.get("hp"); hp = max(0, min(100, hp)) if isinstance(hp, (int, float)) else None
    if phase == "idle": enemy["alive"] = False; return
    if not enemy["alive"] and phase != "done": spawnEnemy(100)
    if hp is not None and enemy["alive"]:
        if hp < enemy["hp"]:
            h = random.choice(heroes); sid = h["eq"][-1] if h["eq"] else None
            dmg = enemy["hp"] - hp; enemy["hp"] = hp; enemy["hit"] = 6
            if h["atkT"] == 0: h["atkT"] = 12
            if not h["melee"]:
                proj.append({"x":h["x"]+40,"y":h["y"]+30,"s":None,"col":(CAT[sid][1] if sid else "#fff"),"mage":h["cls"]=="mage","life":0})
            pops.append({"x":enemy["x"],"y":enemy["y"]-18,"txt":"-%d"%dmg,"col":"#ffd166","life":30,"vy":-0.7,"big":False})
            if sid: pops.append({"x":enemy["x"],"y":enemy["y"]-40,"txt":CAT[sid][2],"col":CAT[sid][1],"life":30,"vy":-0.7,"big":False})
        else:
            enemy["hp"] = hp
    if phase == "done" and enemy["alive"] and enemy["dead"] == 0:
        enemy["hp"] = 0; finish()

# ---------- rendering ----------
def dots(cv, grid, ox, oy, cell, pal):
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == " " or ch == ".": continue
            col = pal.get(ch)
            if not col: continue
            X = ox + x*cell; Y = oy + y*cell
            cv.create_rectangle(X, Y, X+cell, Y+cell, fill=col, width=0)
def draw_claude(cv):
    EC = 6; g = CLAUDE_G; Wc = len(g[0]); Hc = len(g)
    wob = 0 if enemy["dead"] else round(math.sin(t/16)*1.5)
    ox = enemy["x"] - Wc*EC//2; oy = enemy["y"] - Hc*EC//2 + wob
    for y, row in enumerate(g):
        for x, ch in enumerate(row):
            if ch == ".": continue
            if ch == "W": col = COL["W"]
            elif enemy["hit"] > 0 and t % 2 == 0: col = "#ffd9c9"
            else: col = COL["C"]
            X = ox + x*EC; Y = oy + y*EC
            if enemy["dead"]:
                d = enemy["dead"]; Y += int(d*d*0.16); X += (-1 if x < Wc/2 else 1)*int(d*0.5)
            cv.create_rectangle(X, Y, X+EC, Y+EC, fill=col, width=0)
def draw_hero(cv, h):
    HC = 5; bob = round(math.sin((t + h["bob"])/10)*1.5)
    hx = h["x"]; hy = h["y"] + bob
    if h["atkT"] > 0 and h["melee"]:
        hx += round(math.sin((12 - h["atkT"])/12*math.pi)*16)
    cx = hx + 20; cy = hy + 30
    armor = lastBy(h, ("armor",)); pal = dict(h["pal"])
    if armor:
        ac = CAT[armor][1]; pal.update(B=ac, b=shade(ac, 0.6), M=ac, m=shade(ac, 0.55))
    dots(cv, SPR[h["cls"]], hx, hy, HC, pal)
    wp = lastBy(h, ("sword","staff","bow"))
    wtype = CAT[wp][0] if wp else CLASSES[h["cls"]]["weapon"]
    wcol = CAT[wp][1] if wp else h["wcol"]; wo = WPOS.get(wtype, (35, 8))
    dots(cv, ICONS[wtype], hx+wo[0], hy+wo[1], 4,
         {"X":wcol,"W":COL["W"],"B":COL["B"],"Y":pal["B"],"S":"#cbd5e1","=":COL["B"],"A":COL["W"]})
    sh = lastBy(h, ("shield",))
    if sh: dots(cv, ICONS["shield"], hx-12, hy+24, 3, {"X":CAT[sh][1],"W":COL["W"]})
    n = len(h["eq"])
    for i, sid in enumerate(h["eq"]):
        ang = t/45 + i*(2*math.pi/n)
        ex = round(cx + math.cos(ang)*28); ey = round(cy - 14 + math.sin(ang)*15)
        cv.create_rectangle(ex-3, ey-3, ex+3, ey+3, fill="#0b1020", width=0)
        cv.create_rectangle(ex-2, ey-2, ex+2, ey+2, fill=CAT[sid][1], width=0)
    cv.create_rectangle(hx-4, hy+12*HC+2, hx+44, hy+12*HC+13, fill="#0b1020", width=0)
    cv.create_text(hx+20, hy+12*HC+8, text=h["name"], fill=COL["W"], font=("Consolas", 8))
def draw_proj(cv, p):
    if p["mage"]:
        cv.create_rectangle(p["x"]-4, p["y"]-4, p["x"]+4, p["y"]+4, fill=p["col"], width=0)
        cv.create_rectangle(p["x"]-1, p["y"]-1, p["x"]+2, p["y"]+2, fill=COL["W"], width=0)
    else:
        cv.create_rectangle(p["x"]-7, p["y"]-1, p["x"]+3, p["y"]+2, fill=COL["B"], width=0)
        cv.create_rectangle(p["x"]+3, p["y"]-2, p["x"]+7, p["y"]+3, fill=p["col"], width=0)
ROW0 = 44                                   # 첫 장비 행 y (위쪽은 SKILL HERO 메뉴)
FH = ROW0 + len(SKILL_LIST)*ROWH + 16        # 고정 창(메뉴+장비) 전체 높이
def render_menu(cv):   # 좌상단 고정 창: SKILL HERO 메뉴 + 장비 창 (한 몸)
    cv.delete("all")
    cv.create_rectangle(0, 0, PW, FH, fill="#13192a", width=0)
    cv.create_rectangle(0, 0, PW, 20, fill="#1d2740", width=0)          # 메뉴 타이틀바
    cv.create_text(7, 10, anchor="w", fill="#7c9cff", font=("Consolas", 10, "bold"), text="⚔ SKILL HERO")
    cv.create_text(PW-6, 10, anchor="e", fill=("#46e0a0" if mode == "live" else "#ffd166"),
                   font=("Consolas", 8), text="[%s]" % mode.upper())
    cv.create_text(7, 31, anchor="w", fill="#9fb2dd", font=("Consolas", 8), text="◈ %s" % label)
    cv.create_rectangle(0, 41, PW, 42, fill="#2c3a5c", width=0)         # 구분선
    for i, sid in enumerate(SKILL_LIST):
        ry = ROW0 + i*ROWH
        if dragging == sid:
            cv.create_rectangle(2, ry-1, PW-2, ry+ROWH-3, fill="#26324f", width=0)
        ic, colr, nm, atk = CAT[sid]
        dots(cv, ICONS[ic], 7, ry+1, 2, {"X":colr,"W":COL["W"],"B":COL["B"],"Y":COL["Y"]})
        cv.create_text(27, ry+8, anchor="w", fill="#e6ecff", font=("Consolas", 8), text=nm)
        cv.create_text(PW-6, ry+8, anchor="e", fill="#ffd166", font=("Consolas", 7), text=str(atk))
    cv.create_text(PW//2, FH-7, fill="#5f6b88", font=("Consolas", 7), text="용사에 드래그 · SPACE · ESC")

def render_arena(cv):   # 이동 가능한 전장 창 (투명, 캐릭터만)
    cv.delete("all")
    if enemy["alive"]:
        draw_claude(cv)
        if not enemy["dead"]:
            bw = 116; bx = enemy["x"] - bw//2; by = enemy["y"] - len(CLAUDE_G)*6//2 - 18
            cv.create_rectangle(bx, by, bx+bw, by+6, fill="#3a1212", width=0)
            cv.create_rectangle(bx, by, bx+int(bw*enemy["hp"]/enemy["hpMax"]), by+6, fill="#ff5d5d", width=0)
            cv.create_text(enemy["x"], by-6, fill=COL["W"], font=("Consolas", 8),
                           text="CLAUDE  %d/%d" % (enemy["hp"], enemy["hpMax"]))
    elif phase != "idle":
        cv.create_text(enemy["x"], enemy["y"], fill="#46e0a0", font=("Consolas", 12), text="✔ 해결됨")
    for h in heroes: draw_hero(cv, h)
    for p in proj: draw_proj(cv, p)
    for p in pops:
        cv.create_text(p["x"], p["y"], fill=p["col"], text=p["txt"],
                       font=("Consolas", 12 if p["big"] else 9, "bold" if p["big"] else "normal"))
    if banner > 0:
        cv.create_text(enemy["x"], enemy["y"]-92, fill="#46e0a0", font=("Consolas", 22, "bold"), text=bannerTxt)

def build_world():
    setHeroes(2); heroes[0]["eq"].append("autopilot"); heroes[1]["eq"].append("ultrawork")

# ---------- entry ----------
def selftest():
    global mode
    class Dummy:
        def delete(self, *a): pass
        def create_rectangle(self, *a, **k): pass
        def create_text(self, *a, **k): pass
    build_world(); cv = Dummy()
    def draw_all(): render_arena(cv); render_menu(cv)
    for _ in range(60): update(); draw_all()          # 1) 데모 자동전투
    demo_heroes = len(heroes)
    mode = "live"                                       # 2) 라이브 연동
    apply_state({"agents":[{"name":"main"},{"name":"verifier"},{"name":"explorer"}],
                 "skills":["autopilot","verify","review"],"phase":"tool","hp":72})
    for _ in range(50): update(); draw_all()
    live_classes = [h["cls"] for h in heroes]
    apply_state({"agents":[{"name":"main"},{"name":"verifier"},{"name":"explorer"}],"phase":"done"})
    for _ in range(50): update(); draw_all()
    assert demo_heroes >= 2, "demo heroes"
    assert live_classes == ["knight","mage","archer"], live_classes
    # 장비 창 드래그-장착 / 우클릭-해제 로직 검증
    h = nearest_hero(heroes[0]["x"] + 5); assert h is heroes[0], "nearest_hero"
    n0 = len(h["eq"]); equip(h, "ralph"); equip(h, "ralph")     # 중복은 무시
    assert len(h["eq"]) == n0 + 1, "equip/dedup"
    h["eq"].pop(); assert len(h["eq"]) == n0, "unequip"
    print("SELFTEST OK  demoHeroes=%d  liveClasses=%s  finalPhase=%s  equip/unequip=OK"
          % (demo_heroes, live_classes, phase))

def main(auto_quit_ms=None):
    import tkinter as tk
    # 전장 창 (이동 가능, 투명)
    root = tk.Tk(); root.overrideredirect(True)
    try: root.attributes("-topmost", True)
    except Exception: pass
    try: root.attributes("-transparentcolor", TRANSP)   # Windows: 해당 색 투명+클릭통과
    except Exception: pass
    sw = root.winfo_screenwidth(); sh = root.winfo_screenheight()
    root.geometry("%dx%d+%d+%d" % (AW, AH, 12+PW+20, 12))   # 메뉴 창 오른쪽, 같은 높이에서 시작
    enemy["x"] = AW - 100; enemy["y"] = AH - 70           # 적: 전장 창 오른쪽
    cv = tk.Canvas(root, width=AW, height=AH, bg=TRANSP, highlightthickness=0); cv.pack()
    # 고정 창: SKILL HERO 메뉴 + 장비 창 (좌상단, 별도 불투명 창, 이동 불가)
    win_menu = tk.Toplevel(root); win_menu.overrideredirect(True)
    try: win_menu.attributes("-topmost", True)
    except Exception: pass
    win_menu.geometry("%dx%d+%d+%d" % (PW, FH, 12, 12))
    cv_menu = tk.Canvas(win_menu, width=PW, height=FH, bg="#13192a", highlightthickness=0); cv_menu.pack()

    # 전장: 캐릭터(불투명 픽셀)를 잡아 끌면 창 이동, 우클릭=장비 해제
    def a_press(e):
        global moving, mox, moy
        moving = True; mox, moy = e.x, e.y
    def a_motion(e):
        if moving: root.geometry("+%d+%d" % (e.x_root-mox, e.y_root-moy))
    def a_release(e):
        global moving; moving = False
    def a_rclick(e):
        h = nearest_hero(e.x)
        if h and h["eq"]: h["eq"].pop()
    cv.bind("<Button-1>", a_press); cv.bind("<B1-Motion>", a_motion)
    cv.bind("<ButtonRelease-1>", a_release); cv.bind("<Button-3>", a_rclick)
    # 메뉴 창: 타이틀/상태 영역(구분선 위) 드래그 = 창 이동 / 장비 행 드래그 = 스킬 장착
    def m_press(e):
        global dragging, mmoving, mmx, mmy
        if e.y < 42:                                # 메뉴·상태 영역 → 메뉴 창 이동
            mmoving = True; mmx, mmy = e.x, e.y; dragging = None
        else:                                       # 장비 행 → 스킬 드래그
            idx = int((e.y - ROW0) // ROWH)
            dragging = SKILL_LIST[idx] if 0 <= idx < len(SKILL_LIST) and e.y >= ROW0 else None
    def m_motion(e):
        if mmoving: win_menu.geometry("+%d+%d" % (e.x_root-mmx, e.y_root-mmy))
    def m_release(e):
        global dragging, mmoving
        if dragging:                                # 전장 창 위에서 놓으면 가까운 용사에 장착(창 간 드래그)
            ax = e.x_root - root.winfo_rootx(); ay = e.y_root - root.winfo_rooty()
            if 0 <= ax <= AW and 0 <= ay <= AH:
                equip(nearest_hero(ax), dragging)
        dragging = None; mmoving = False
    cv_menu.bind("<Button-1>", m_press); cv_menu.bind("<B1-Motion>", m_motion); cv_menu.bind("<ButtonRelease-1>", m_release)

    def toggle(e):
        global mode, di, dt, dEntered
        mode = "demo" if mode == "live" else "live"
        if mode == "demo": di = dt = 0; dEntered = False
    for w in (root, win_menu):
        w.bind("<Escape>", lambda e: root.destroy())
        w.bind("<space>", toggle)
    try: root.focus_force()
    except Exception: pass
    build_world()
    def tick():
        update()
        if mode == "live" and t % 25 == 0:
            st = read_state()
            if st: apply_state(st)
        render_arena(cv); render_menu(cv_menu)
        root.after(40, tick)
    if auto_quit_ms: root.after(auto_quit_ms, root.destroy)
    tick(); root.mainloop()

if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    elif "--guitest" in sys.argv: main(700); print("GUITEST OK (창 생성/렌더/종료 정상)")
    else: main()
