"""ととのい道 ― サウナ → 水風呂 → 外気浴 を 3 セット遊ぶ Pyxel ゲーム

操作
  A: SPACE / Z / パッドA / 画面タップ
  B: X / ENTER / パッドB / 右下の「でる」ボタン
"""

import math
import random

import pyxel

W, H = 192, 144
FPS = 30
SETS = 3

# 右下の「でる」ボタン (x, y, w, h)
OUT_BTN = (150, 124, 38, 16)

FONT = None


# ---------------------------------------------------------------------------
# 入力
# ---------------------------------------------------------------------------
class Inp:
    out_visible = False

    @staticmethod
    def _on_out():
        x, y, w, h = OUT_BTN
        return (
            Inp.out_visible
            and x <= pyxel.mouse_x < x + w
            and y <= pyxel.mouse_y < y + h
        )

    @staticmethod
    def a_held():
        return (
            pyxel.btn(pyxel.KEY_SPACE)
            or pyxel.btn(pyxel.KEY_Z)
            or pyxel.btn(pyxel.GAMEPAD1_BUTTON_A)
            or (pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and not Inp._on_out())
        )

    @staticmethod
    def a():
        return (
            pyxel.btnp(pyxel.KEY_SPACE)
            or pyxel.btnp(pyxel.KEY_Z)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)
            or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and not Inp._on_out())
        )

    @staticmethod
    def b():
        return (
            pyxel.btnp(pyxel.KEY_X)
            or pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
            or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and Inp._on_out())
        )


# ---------------------------------------------------------------------------
# 描画ヘルパー
# ---------------------------------------------------------------------------
def text_w(s):
    return FONT.text_width(s)


def text(x, y, s, col, border=None):
    if border is not None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            pyxel.text(x + dx, y + dy, s, border, FONT)
    pyxel.text(x, y, s, col, FONT)


def ctext(y, s, col, border=None, cx=W // 2):
    text(cx - text_w(s) // 2, y, s, col, border)


def big_text(cx, cy, s, col, scale=3, border=None):
    """標準フォントを拡大して描く（タイトル用）"""
    img = pyxel.images[2]
    img.rect(0, 0, 128, 8, 0)
    img.text(0, 0, s, col)
    w = len(s) * 4
    if border is not None:
        img.rect(0, 8, 128, 8, 0)
        img.text(0, 8, s, border)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pyxel.blt(cx - w / 2 + dx * scale, cy - 2.5 + dy * scale, 2, 0, 8, w, 5, 0, scale=scale)
    pyxel.blt(cx - w / 2, cy - 2.5, 2, 0, 0, w, 5, 0, scale=scale)


def draw_out_button():
    x, y, w, h = OUT_BTN
    pyxel.rect(x, y, w, h, 8)
    pyxel.rectb(x, y, w, h, 7)
    text(x + 5, y + 3, "でる B", 7)


def draw_person(x, y, pose="sit", hat=8, skin=15, flush=0.0):
    """サウナハットをかぶった主人公。(x, y) は足元中央"""
    body = 9 if flush > 0.6 else skin
    if pose == "sit":
        # 足
        pyxel.rect(x - 4, y - 3, 8, 3, body)
        pyxel.rect(x + 2, y - 3, 3, 6, body)
        # タオル
        pyxel.rect(x - 5, y - 6, 9, 4, 7)
        # 胴
        pyxel.rect(x - 4, y - 14, 7, 9, body)
        head_y = y - 19
    elif pose == "lie":
        # 外気浴チェアでリクライニング
        pyxel.rect(x - 10, y - 5, 12, 4, body)
        pyxel.rect(x - 2, y - 6, 8, 3, 7)
        pyxel.rect(x + 6, y - 4, 7, 3, body)
        head_y = y - 9
        x = x - 13
    else:  # "bath" 首まで
        head_y = y - 6
    # 頭
    pyxel.circ(x, head_y, 4, body)
    pyxel.pset(x + 1, head_y, 0)
    pyxel.pset(x + 3, head_y, 0)
    if flush > 0.3:
        pyxel.pset(x + 2, head_y + 2, 8)
        pyxel.pset(x + 4, head_y + 2, 8)
    # サウナハット
    pyxel.elli(x - 6, head_y - 4, 13, 4, hat)
    pyxel.rect(x - 4, head_y - 7, 8, 4, hat)
    pyxel.line(x - 4, head_y - 4, x + 3, head_y - 4, 7)


def gauge_v(x, y, w, h, value, zones, col=8, label=None):
    """縦ゲージ。zones = [(lo, hi, col), ...] 0..100"""
    pyxel.rect(x, y, w, h, 0)
    for lo, hi, c in zones:
        y0 = y + h - h * hi / 100
        y1 = y + h - h * lo / 100
        pyxel.rect(x, y0, 2, y1 - y0, c)
    v = max(0, min(100, value))
    fh = h * v / 100
    pyxel.rect(x + 3, y + h - fh, w - 4, fh, col)
    pyxel.rectb(x - 1, y - 1, w + 2, h + 2, 7)
    if label:
        text(x + w // 2 - text_w(label) // 2, y + h + 3, label, 7, 0)


def gauge_h(x, y, w, h, value, col, back=0):
    pyxel.rect(x, y, w, h, back)
    pyxel.rect(x, y, w * max(0, min(100, value)) / 100, h, col)
    pyxel.rectb(x - 1, y - 1, w + 2, h + 2, 7)


class Popups:
    """ふわっと浮かんで消える文字"""

    def __init__(self):
        self.items = []

    def add(self, x, y, s, col):
        self.items.append([x, y, s, col, 30])

    def update(self):
        for p in self.items:
            p[1] -= 0.6
            p[4] -= 1
        self.items = [p for p in self.items if p[4] > 0]

    def draw(self):
        for x, y, s, col, life in self.items:
            if life > 6 or pyxel.frame_count % 2:
                text(x - text_w(s) // 2, y, s, col, 0)


class Steam:
    def __init__(self):
        self.ps = []

    def emit(self, x, y, n=1, spread=6):
        for _ in range(n):
            self.ps.append([x + random.uniform(-spread, spread), y, random.uniform(-0.3, 0.3), random.uniform(-1.0, -0.4), random.randint(25, 50)])

    def update(self):
        for p in self.ps:
            p[0] += p[2] + math.sin(p[4] * 0.2) * 0.2
            p[1] += p[3]
            p[4] -= 1
        self.ps = [p for p in self.ps if p[4] > 0]

    def draw(self, col=7):
        for x, y, _, _, life in self.ps:
            r = 1 if life < 15 else 2
            if life < 10:
                pyxel.dither(0.5)
            pyxel.circ(x, y, r, col)
            pyxel.dither(1.0)


# ---------------------------------------------------------------------------
# サウンド
# ---------------------------------------------------------------------------
SE_SELECT, SE_GOOD, SE_BAD, SE_ROURYU, SE_SPLASH, SE_TOTONOI, SE_TAP = range(7)
BGM_CH = (8, 9, 10)


def setup_sounds():
    pyxel.sounds[SE_SELECT].set("c3g3", "p", "6", "n", 6)
    pyxel.sounds[SE_GOOD].set("c3e3g3c4", "s", "5", "n", 4)
    pyxel.sounds[SE_BAD].set("c2b1a#1", "s", "6", "s", 8)
    pyxel.sounds[SE_ROURYU].set("c3c3c3c3c2c2c2c2", "n", "76543211", "n", 6)
    pyxel.sounds[SE_SPLASH].set("g3c3g2c2", "n", "7531", "s", 5)
    pyxel.sounds[SE_TOTONOI].set("c3e3g3b3c4e4g4b4c4", "t", "6", "nnnnnnnnf", 7)
    pyxel.sounds[SE_TAP].set("a3", "p", "4", "f", 4)

    # 外気浴 BGM（ゆったりした MML ループ）
    pyxel.sounds[BGM_CH[0]].mml(
        "T72 Q90 @1 V70 O4 L4 @ENV1{40,30,90} "
        "E G >C< B2 G2 A >C< G2 E2 F A G E D2. R4 "
        "E G >C< B2 >D2 C< A G2 E2 F E D C2. R4"
    )
    pyxel.sounds[BGM_CH[1]].mml(
        "T72 Q100 @0 V60 O3 L2 "
        "C1 E1 F1 C1 F1 G1 C1 C1 "
        "C1 E1 F1 C1 F1 G1 C1 C1"
    )
    pyxel.sounds[BGM_CH[2]].mml(
        "T72 Q30 @3 V18 O7 L8 [R C R C R C R C]16"
    )
    pyxel.musics[0].set([BGM_CH[0]], [BGM_CH[1]], [BGM_CH[2]])


def se(n):
    pyxel.play(3, n)


# ---------------------------------------------------------------------------
# プレイヤーの状態（シーン間で受け渡す）
# ---------------------------------------------------------------------------
class Body:
    def __init__(self, set_no):
        self.set_no = set_no
        self.heat = 10.0
        self.sweat = 0.0
        self.sauna_mul = 1.0
        self.sauna_grade = ""
        self.mizu_mul = 1.0
        self.mizu_grade = ""
        self.points = 0.0
        self.totonoi = False

    @property
    def mul(self):
        return self.sauna_mul * self.mizu_mul


# ---------------------------------------------------------------------------
# タイトル
# ---------------------------------------------------------------------------
class TitleScene:
    def __init__(self, game):
        self.game = game
        self.steam = Steam()
        Inp.out_visible = False

    def update(self):
        if pyxel.frame_count % 3 == 0:
            self.steam.emit(random.uniform(20, W - 20), H - 10)
        self.steam.update()
        if Inp.a() or Inp.b():
            se(SE_SELECT)
            self.game.start()

    def draw(self):
        pyxel.cls(4)
        for y in range(0, H, 8):
            pyxel.line(0, y, W, y, 2)
        for x in range(0, W, 24):
            pyxel.line(x + (8 if (x // 24) % 2 else 0), 0, x, H, 2)
        self.steam.draw(13)
        ctext(16, "サウナ・水風呂・外気浴", 10, 0)
        big_text(W / 2, 46, "TOTONOI", 7, scale=4, border=8)
        ctext(64, "ととのい道", 15, 2)
        draw_person(W // 2, 104, "sit", flush=abs(math.sin(pyxel.frame_count * 0.05)))
        if (pyxel.frame_count // 15) % 2:
            ctext(116, "SPACE / タップでスタート", 7, 0)
        ctext(130, f"ハイスコア {self.game.hiscore}", 10, 0)


# ---------------------------------------------------------------------------
# サウナ
# ---------------------------------------------------------------------------
class SaunaScene:
    PLAYER_X = 74

    def __init__(self, game, body):
        self.game = game
        self.body = body
        self.t = 0
        self.upper = False
        self.steam = Steam()
        self.pop = Popups()
        self.base_rate = 0.11 + 0.025 * (body.set_no - 1)  # 1 フレームあたりの体温上昇
        self.next_rouryu = random.randint(4 * FPS, 7 * FPS)
        self.rouryu_count = 0
        self.max_rouryu = body.set_no  # セットが進むほどロウリュが増える
        self.rouryu = None  # {"phase": "pour"/"wind", "t": int, "swings": [...]}
        self.ending = 0
        self.overheat = False
        Inp.out_visible = True
        pyxel.stop()

    # --- ロウリュ ---
    def start_rouryu(self):
        self.rouryu = {"phase": "pour", "t": 0, "swings": [], "hits": 0}
        se(SE_ROURYU)
        self.pop.add(40, 40, "ロウリュ！", 10)

    def update_rouryu(self):
        r = self.rouryu
        r["t"] += 1
        if r["phase"] == "pour":
            self.body.heat += 0.35
            self.steam.emit(30, 92, 3, 8)
            if r["t"] >= 30:
                r["phase"] = "wind"
                r["t"] = 0
                interval = 22 - 3 * self.body.set_no
                r["swings"] = [20 + i * interval for i in range(4)]
                r["judged"] = [False] * 4
            return
        # wind: 輪が縮んで人に重なった瞬間に A
        if Inp.a():
            best = None
            for i, hit_t in enumerate(r["swings"]):
                if not r["judged"][i] and abs(r["t"] - hit_t) <= 8:
                    best = i
                    break
            if best is not None:
                d = abs(r["t"] - r["swings"][best])
                r["judged"][best] = True
                if d <= 3:
                    r["hits"] += 1
                    self.body.sweat += 8
                    self.body.heat += 1.5
                    self.pop.add(self.PLAYER_X, 50, "ナイス熱波！", 11)
                    se(SE_GOOD)
                else:
                    self.body.heat += 3
                    self.pop.add(self.PLAYER_X, 50, "あつっ", 8)
                    se(SE_BAD)
        for i, hit_t in enumerate(r["swings"]):
            if not r["judged"][i] and r["t"] > hit_t + 8:
                r["judged"][i] = True
                self.body.heat += 3
                self.pop.add(self.PLAYER_X, 50, "あつっ", 8)
        if r["t"] > r["swings"][-1] + 15:
            if r["hits"] == 4:
                self.body.sweat += 15
                self.pop.add(self.PLAYER_X, 36, "パーフェクト！", 10)
                se(SE_TOTONOI)
            self.rouryu = None

    def judge(self):
        h = self.body.heat
        if self.overheat:
            mul, grade = 0.3, "のぼせ…"
        elif h < 40:
            mul, grade = 0.35, "早すぎ"
        elif h < 60:
            mul, grade = 0.6, "もうちょい"
        elif h < 75:
            mul, grade = 0.85, "まずまず"
        elif h < 90:
            mul, grade = 1.0, "ちょうどいい"
        else:
            mul, grade = 1.15, "攻めた！"
        mul *= 1 + min(self.body.sweat, 100) / 200
        self.body.sauna_mul = mul
        self.body.sauna_grade = grade

    def update(self):
        self.pop.update()
        self.steam.update()
        if pyxel.frame_count % 6 == 0:
            self.steam.emit(30, 92, 1, 6)

        if self.ending:
            self.ending -= 1
            if self.ending == 0:
                return MizuScene(self.game, self.body)
            return None

        self.t += 1
        if self.rouryu:
            self.update_rouryu()
        else:
            self.upper = Inp.a_held()
            if self.rouryu_count < self.max_rouryu and self.t >= self.next_rouryu:
                self.rouryu_count += 1
                self.next_rouryu = self.t + random.randint(6 * FPS, 9 * FPS)
                self.start_rouryu()

        rate = self.base_rate * (2.1 if self.upper else 1.0)
        self.body.heat += rate
        self.body.sweat += 0.06 if self.upper else 0.02

        if self.body.heat >= 100:
            self.body.heat = 100
            self.overheat = True
            se(SE_BAD)
            self.pop.add(self.PLAYER_X, 40, "のぼせた…！", 8)
            self.finish(45)
        elif Inp.b() and self.t > FPS // 2:
            se(SE_SELECT)
            self.finish(20)
        return None

    def finish(self, wait):
        self.judge()
        self.ending = wait
        Inp.out_visible = False

    def draw(self):
        heat = self.body.heat
        pyxel.cls(4)
        # 木の壁
        for y in range(0, 100, 10):
            pyxel.line(0, y, 140, y, 2)
        for i, y in enumerate(range(0, 100, 10)):
            off = 15 if i % 2 else 0
            for x in range(off, 140, 30):
                pyxel.line(x, y, x, y + 9, 2)
        # 暑さで画面が赤みがかる
        if heat > 70:
            pyxel.dither((heat - 70) / 60)
            pyxel.rect(0, 0, 140, 100, 8)
            pyxel.dither(1.0)
        # 床
        pyxel.rect(0, 100, 140, 44, 2)
        # ストーブ
        pyxel.rect(14, 96, 32, 26, 13)
        pyxel.rect(16, 98, 28, 4, 0)
        for i in range(6):
            pyxel.circ(19 + i * 4.5, 95, 3, 5 if i % 2 else 13)
        glow = 8 if (pyxel.frame_count // 4) % 2 else 9
        pyxel.rect(22, 108, 16, 8, glow)
        # ベンチ（3 段）
        for i, (bx, by) in enumerate(((60, 116), (60, 96), (60, 76))):
            pyxel.rect(bx, by, 80, 6, 9)
            pyxel.line(bx, by, bx + 79, by, 10)
            pyxel.rect(bx, by + 6, 80, 20 if i == 0 else 4, 4)
        # 常連さん（下段に座っている）
        draw_person(118, 116, "sit", hat=12, skin=14, flush=0.4)
        # 主人公
        py = 76 if self.upper or (self.rouryu and self.upper) else 96
        draw_person(self.PLAYER_X, py, "sit", flush=heat / 100)
        # 汗
        if heat > 50 and pyxel.frame_count % max(3, int(20 - heat / 6)) == 0:
            self.pop.items.append([self.PLAYER_X + random.randint(-5, 5), py - 18, "・", 12, 10])

        # 熱波師
        if self.rouryu:
            r = self.rouryu
            hx = 40
            draw_person(hx, 116, "sit", hat=0, skin=15)
            if r["phase"] == "pour":
                pyxel.line(hx + 6, 98, 28, 92, 13)
                pyxel.rect(hx + 4, 96, 4, 4, 9)  # ひしゃく
            else:
                # タオルを振る
                swing = math.sin(r["t"] * 0.5)
                tx = hx + 10 + swing * 6
                pyxel.tri(hx + 4, 98, tx + 10, 80 + swing * 4, tx + 14, 92, 7)
                for i, hit_t in enumerate(r["swings"]):
                    if r["judged"][i]:
                        continue
                    remain = hit_t - r["t"]
                    if -8 <= remain <= 30:
                        rad = 6 + max(0, remain) * 1.2
                        col = 10 if abs(remain) <= 3 else 7
                        pyxel.circb(self.PLAYER_X, py - 12, rad, col)
                pyxel.circb(self.PLAYER_X, py - 12, 6, 11)
                text(4, 4, "わの重なりで A！", 10, 0)
                text(4, 16, "あつすぎたら B", 7, 0)

        self.steam.draw(7)

        # ---- 右側 UI ----
        pyxel.rect(140, 0, 52, H, 1)
        # 12 分計
        cx, cy = 166, 22
        pyxel.circ(cx, cy, 15, 7)
        pyxel.circb(cx, cy, 15, 13)
        for i in range(12):
            a = i / 12 * math.tau
            pyxel.pset(cx + math.sin(a) * 12, cy - math.cos(a) * 12, 0)
        a = self.t / (FPS * 10) * math.tau  # 10 秒で 1 周
        pyxel.line(cx, cy, cx + math.sin(a) * 11, cy - math.cos(a) * 11, 8)
        pyxel.circ(cx, cy, 1, 0)
        gauge_v(150, 44, 12, 70, heat, [(75, 90, 11), (90, 100, 10)], col=8 if heat < 90 else 10)
        text(164, 44, "体", 7, 0)
        text(164, 56, "温", 7, 0)
        text(164, 102, f"{int(heat):>3}", 7, 0)

        text(4, 126, "A長押し:上段", 10, 0)
        text(76, 126, f"第{self.body.set_no}セット", 15, 0)
        if self.ending == 0:
            draw_out_button()
        self.pop.draw()
        if self.ending:
            ctext(40, self.body.sauna_grade, 10, 0, cx=70)


# ---------------------------------------------------------------------------
# 水風呂
# ---------------------------------------------------------------------------
class MizuScene:
    ZONE_H = 26  # 落ち着きゾーンの高さ（%）

    def __init__(self, game, body):
        self.game = game
        self.body = body
        self.t = 0
        self.breath = 50.0  # 0..100
        self.vel = 0.0
        self.calm_frames = 0
        self.in_zone_streak = 0
        self.panic = 0.0
        self.hagoromo = False
        self.pop = Popups()
        self.ripples = []
        self.ending = 0
        self.panicked = False
        self.too_cold = False
        Inp.out_visible = True
        se(SE_SPLASH)
        self.pop.add(70, 76, "ざぶーん", 7)

    def zone_center(self):
        return 50 + math.sin(self.t * 0.03) * 22 + math.sin(self.t * 0.071) * 8

    def judge(self):
        h = self.body.heat
        if self.panicked:
            mul, grade = 0.3, "パニック…"
        elif h > 60:
            mul, grade = 0.4, "冷えてない"
        elif h > 40:
            mul, grade = 0.75, "まだぬるい"
        elif h >= 20:
            mul, grade = 1.0, "キンキン！"
        elif h >= 10:
            mul, grade = 0.85, "ちょい冷え"
        else:
            mul, grade = 0.5, "冷えすぎ…"
        calm_ratio = self.calm_frames / max(1, self.t)
        if not self.panicked:
            mul *= 0.6 + 0.5 * calm_ratio
        self.body.mizu_mul = mul
        self.body.mizu_grade = grade

    def update(self):
        self.pop.update()
        for r in self.ripples:
            r[2] += 0.5
        self.ripples = [r for r in self.ripples if r[2] < 20]
        if pyxel.frame_count % 20 == 0:
            self.ripples.append([70 + random.uniform(-6, 6), 98, 2])

        if self.ending:
            self.ending -= 1
            if self.ending == 0:
                return GaikiScene(self.game, self.body)
            return None

        self.t += 1
        # 冷える
        cool = 0.32 + 0.03 * self.body.set_no
        if self.hagoromo:
            cool *= 0.45
        self.body.heat = max(0.0, self.body.heat - cool)

        # 呼吸カーソル（沈む・A で浮く）
        shock = max(0.0, 1.0 - self.t / (FPS * 4)) * 1.6 + 0.25
        self.vel -= 0.13
        self.vel += random.uniform(-shock, shock) * 0.35
        if Inp.a():
            self.vel += 2.2
            se(SE_TAP)
            self.ripples.append([70, 98, 2])
            self.in_zone_streak = min(self.in_zone_streak, 40)  # 動くと羽衣が崩れる
            if self.hagoromo:
                self.hagoromo = False
                self.pop.add(70, 76, "羽衣がやぶれた", 7)
        self.vel = max(-3, min(3, self.vel)) * 0.96
        self.breath += self.vel
        if self.breath < 0:
            self.breath, self.vel = 0, 0
        if self.breath > 100:
            self.breath, self.vel = 100, -0.5

        zc = self.zone_center()
        in_zone = abs(self.breath - zc) <= self.ZONE_H / 2
        if in_zone:
            self.calm_frames += 1
            self.in_zone_streak += 1
            self.panic = max(0, self.panic - 0.4)
            if self.in_zone_streak == FPS * 2 and not self.hagoromo:
                self.hagoromo = True
                self.pop.add(70, 76, "羽衣 発動！", 10)
                se(SE_GOOD)
        else:
            self.in_zone_streak = 0
            self.hagoromo = False
            self.panic += 1.1

        if self.panic >= 100:
            self.panicked = True
            se(SE_BAD)
            self.pop.add(70, 76, "ぶはっ！", 8)
            self.finish(40)
        elif self.body.heat <= 0:
            self.too_cold = True
            se(SE_BAD)
            self.pop.add(70, 76, "さむい！", 12)
            self.finish(40)
        elif Inp.b() and self.t > FPS:
            se(SE_SPLASH)
            self.finish(20)
        return None

    def finish(self, wait):
        self.judge()
        self.ending = wait
        Inp.out_visible = False

    def draw(self):
        pyxel.cls(13)
        # タイルの壁
        for x in range(0, 140, 12):
            pyxel.line(x, 0, x, 80, 6)
        for y in range(0, 80, 12):
            pyxel.line(0, y, 140, y, 6)
        # 浴槽
        pyxel.rect(10, 80, 124, 50, 7)
        pyxel.rect(14, 86, 116, 40, 12)
        wave = pyxel.frame_count * 0.15
        for x in range(14, 130):
            yy = 86 + math.sin(x * 0.2 + wave) * 1.2
            pyxel.pset(x, yy, 6)
        # 羽衣
        if self.hagoromo:
            pyxel.dither(0.5)
            pyxel.elli(56, 90, 28, 14, 6)
            pyxel.dither(1.0)
            for i in range(5):
                a = pyxel.frame_count * 0.1 + i * 1.25
                pyxel.pset(70 + math.cos(a) * 14, 96 + math.sin(a) * 6, 7)
        for x, y, r in self.ripples:
            pyxel.ellib(x - r, y - r / 3, r * 2, r * 2 / 3, 6)
        shake = 0 if self.hagoromo else int(random.uniform(-1, 1) * max(0, 1 - self.t / (FPS * 4)) * 2)
        draw_person(70 + shake, 98, "bath", flush=self.body.heat / 100)
        # 水面の前側
        pyxel.dither(0.5)
        pyxel.rect(14, 99, 116, 27, 5)
        pyxel.dither(1.0)
        text(18, 112, "水温 15℃", 7, 1)

        # ---- 呼吸メーター（左上）----
        mx, my, mh = 4, 6, 70
        pyxel.rect(mx, my, 10, mh, 0)
        zc = self.zone_center()
        zy = my + mh - mh * (zc + self.ZONE_H / 2) / 100
        pyxel.rect(mx, zy, 10, mh * self.ZONE_H / 100, 3 if not self.hagoromo else 11)
        by = my + mh - mh * self.breath / 100
        pyxel.rect(mx - 2, by - 1, 14, 3, 10)
        pyxel.rectb(mx - 1, my - 1, 12, mh + 2, 7)
        text(17, 6, "呼吸", 7, 0)
        text(17, 18, "A連打", 10, 0)
        # パニック
        text(17, 58, "パニック", 8, 0)
        gauge_h(17, 70, 40, 4, self.panic, 8)

        # ---- 右側 UI ----
        pyxel.rect(140, 0, 52, H, 1)
        gauge_v(150, 20, 12, 90, self.body.heat, [(20, 40, 11), (10, 20, 10)], col=6 if self.body.heat < 60 else 8)
        text(164, 20, "体", 7, 0)
        text(164, 32, "温", 7, 0)
        text(164, 100, f"{int(self.body.heat):>3}", 7, 0)
        text(146, 4, "水風呂", 12, 0)

        if self.ending == 0:
            draw_out_button()
        else:
            ctext(50, self.body.mizu_grade, 10, 0, cx=70)
        self.pop.draw()


# ---------------------------------------------------------------------------
# 外気浴
# ---------------------------------------------------------------------------
NOISES = [
    # (名前, 表示文字, 色)
    ("ka", "プーン", 13),
    ("crow", "カァー", 0),
    ("ojisan", "いい天気だねぇ", 4),
    ("wind", "ヒュオォ", 6),
]


class GaikiScene:
    DURATION = 20 * FPS

    def __init__(self, game, body):
        self.game = game
        self.body = body
        self.t = 0
        self.gauge = 0.0
        self.pop = Popups()
        self.noise = None  # [kind, text, col, life, x, y]
        self.next_noise = random.randint(int(2.5 * FPS), 4 * FPS)
        self.sparkles = []
        self.clouds = [[random.uniform(0, W), random.uniform(8, 40), random.uniform(0.05, 0.2)] for _ in range(4)]
        self.reached = False
        self.ending = 0
        Inp.out_visible = False
        pyxel.playm(0, loop=True)

    def spawn_noise(self):
        kind, s, col = random.choice(NOISES)
        x = random.uniform(40, 120)
        y = random.uniform(30, 70)
        life = int((2.2 - 0.35 * self.body.set_no) * FPS)
        self.noise = [kind, s, col, life, x, y]

    def update(self):
        self.pop.update()
        for c in self.clouds:
            c[0] = (c[0] + c[2]) % (W + 40)
        for s in self.sparkles:
            s[1] -= s[2]
            s[3] -= 1
        self.sparkles = [s for s in self.sparkles if s[3] > 0]

        if self.ending:
            self.ending -= 1
            if self.ending == 0:
                pyxel.stop()
                return SetResultScene(self.game, self.body)
            return None

        self.t += 1
        rate = 100 / (13 * FPS) * self.body.mul
        if self.noise:
            rate *= 0.3
        self.gauge = min(100.0, self.gauge + rate)

        # 邪魔
        if self.noise:
            n = self.noise
            n[3] -= 1
            if n[0] == "ka":
                n[4] += math.sin(self.t * 0.4) * 2
                n[5] += math.cos(self.t * 0.3) * 1.5
            if Inp.a():
                se(SE_TAP)
                self.pop.add(n[4], n[5], "シッシッ", 7)
                self.noise = None
                self.next_noise = self.t + random.randint(int((3.5 - 0.5 * self.body.set_no) * FPS), int((5.5 - 0.5 * self.body.set_no) * FPS))
            elif n[3] <= 0:
                se(SE_BAD)
                self.gauge = max(0, self.gauge - 18)
                self.pop.add(n[4], n[5], "ざわざわ…", 8)
                self.noise = None
                self.next_noise = self.t + random.randint(3 * FPS, 5 * FPS)
        else:
            if Inp.a():
                se(SE_BAD)
                self.gauge = max(0, self.gauge - 6)
                self.pop.add(60, 70, "そわそわ", 8)
            if self.t >= self.next_noise and self.t < self.DURATION - FPS:
                self.spawn_noise()

        if self.gauge >= 100 and not self.reached:
            self.reached = True
            self.body.totonoi = True
            se(SE_TOTONOI)
            self.pop.add(W // 2, 40, "ととのったー", 10)

        self.body.points += self.gauge * 0.01 * (1.5 if self.gauge >= 100 else 1.0)

        if self.gauge >= 60 and pyxel.frame_count % 3 == 0:
            self.sparkles.append([random.uniform(0, W), H, random.uniform(0.3, 1.0), 120, random.choice((7, 10, 14, 11))])

        if self.t >= self.DURATION:
            self.ending = 30
        return None

    def draw(self):
        g = self.gauge
        # 空（ととのうほどサイケデリックに）
        sky = [12, 6, 12, 6, 7]
        if g >= 100:
            sky = [2, 14, 15, 10, 11, 6, 12]
        elif g >= 60:
            sky = [12, 14, 6, 15, 7]
        bands = len(sky)
        shift = self.t // 24 if g >= 60 else 0  # 色の帯がゆっくり流れる
        for i in range(bands):
            y0 = i * 100 // bands
            pyxel.rect(0, y0, W, 100 // bands + 1, sky[(i + shift) % bands])
        if g >= 100:
            # 波打つ光
            for x in range(0, W, 2):
                y = 40 + math.sin(x * 0.08 + self.t * 0.1) * 12
                pyxel.pset(x, y, 7)
        # 雲
        for x, y, _ in self.clouds:
            pyxel.elli(x - 20, y, 24, 8, 7)
            pyxel.elli(x - 12, y - 4, 16, 8, 7)
        # 木
        for tx in (12, 176):
            pyxel.rect(tx - 2, 70, 4, 30, 4)
            pyxel.circ(tx, 64, 12, 3)
            pyxel.circ(tx - 6, 70, 8, 11 if g >= 100 else 3)
        # ウッドデッキ
        pyxel.rect(0, 100, W, 44, 4)
        for x in range(0, W, 16):
            pyxel.line(x, 100, x - 20, H, 2)
        # チェア
        pyxel.line(70, 118, 120, 112, 7)
        pyxel.line(70, 119, 120, 113, 13)
        pyxel.line(72, 118, 66, 128, 13)
        pyxel.line(118, 113, 124, 128, 13)
        pyxel.line(70, 118, 62, 104, 7)
        draw_person(100, 116, "lie", flush=max(0, self.body.heat / 100))
        # 魂（ととのい）
        if g >= 60:
            a = self.t * 0.08
            sx = 87 + math.sin(a) * 4
            sy = 92 - (g - 60) * 0.4 - abs(math.sin(a * 0.5)) * 4
            pyxel.dither(0.6)
            pyxel.circ(sx, sy, 3, 7)
            pyxel.dither(1.0)
        for x, y, _, life, col in self.sparkles:
            if life % 6 < 4:
                pyxel.pset(x, y, col)

        # 邪魔
        if self.noise:
            kind, s, col, life, x, y = self.noise
            if kind == "ka":
                pyxel.pset(x, y, 0)
                pyxel.pset(x - 1, y - 1, 13)
                pyxel.pset(x + 1, y - 1, 13)
            elif kind == "crow":
                pyxel.elli(x - 5, y - 2, 10, 5, 0)
                pyxel.tri(x - 4, y, x - 10, y - 6 + (self.t // 4 % 2) * 6, x, y, 0)
            elif kind == "ojisan":
                draw_person(int(x), 116, "sit", hat=12, skin=14)
                y = 80
                x = x + 14
            elif kind == "wind":
                for i in range(3):
                    lx = (x + self.t * 3 + i * 20) % W
                    pyxel.line(lx, y + i * 6, lx + 12, y + i * 6, 7)
            text(int(x - text_w(s) // 2), int(y - 14), s, 7, col if col != 7 else 0)
            if (self.t // 4) % 2:
                text(int(x - 8), int(y + 6), "A!", 10, 0)

        # UI
        pyxel.rect(0, 130, W, 14, 1)
        text(4, 132, "ととのい", 7)
        gauge_h(48, 134, 90, 6, g, 10 if g >= 100 else 14)
        remain = max(0, (self.DURATION - self.t) // FPS)
        text(146, 132, f"のこり{remain:>2}", 7)
        text(4, 4, "じっとして… 邪魔はAで追い払う", 7, 1)
        self.pop.draw()


# ---------------------------------------------------------------------------
# セット結果 / 最終結果
# ---------------------------------------------------------------------------
class SetResultScene:
    def __init__(self, game, body):
        self.game = game
        self.body = body
        self.t = 0
        game.results.append(body)
        Inp.out_visible = False

    def update(self):
        self.t += 1
        if self.t > FPS and (Inp.a() or Inp.b()):
            se(SE_SELECT)
            if self.body.set_no < SETS:
                return SaunaScene(self.game, Body(self.body.set_no + 1))
            return FinalScene(self.game)
        return None

    def draw(self):
        b = self.body
        pyxel.cls(1)
        ctext(10, f"第{b.set_no}セット けっか", 7, 5)
        rows = [
            ("サウナ", b.sauna_grade, f"x{b.sauna_mul:.2f}", 9),
            ("水風呂", b.mizu_grade, f"x{b.mizu_mul:.2f}", 12),
            ("外気浴", "ととのった！" if b.totonoi else "あと少し…", f"{int(b.points)}点", 10),
        ]
        for i, (name, grade, val, col) in enumerate(rows):
            if self.t > 8 + i * 10:
                y = 36 + i * 22
                pyxel.rect(16, y - 3, W - 32, 17, 5)
                text(22, y, name, col)
                text(74, y, grade, 7)
                text(W - 22 - text_w(val), y, val, 10)
        total = sum(int(r.points) for r in self.game.results)
        if self.t > 40:
            ctext(108, f"合計 {total}点", 10, 0)
        if self.t > FPS and (self.t // 15) % 2:
            label = "つぎのセットへ" if b.set_no < SETS else "最終結果へ"
            ctext(126, f"A: {label}", 7)


RANKS = [
    (1350, "サウナの神", 10),
    (1000, "ととのい職人", 14),
    (650, "サウナー", 11),
    (300, "サウナ好き", 12),
    (0, "サウナビギナー", 7),
]


class FinalScene:
    def __init__(self, game):
        self.game = game
        self.t = 0
        self.total = sum(int(r.points) for r in game.results)
        self.new_record = self.total > game.hiscore
        game.hiscore = max(game.hiscore, self.total)
        self.rank, self.rank_col = next((name, col) for th, name, col in RANKS if self.total >= th)
        self.steam = Steam()
        se(SE_TOTONOI)

    def update(self):
        self.t += 1
        if pyxel.frame_count % 2 == 0:
            self.steam.emit(random.uniform(0, W), H, 1, 0)
        self.steam.update()
        if self.t > FPS and (Inp.a() or Inp.b()):
            se(SE_SELECT)
            return TitleScene(self.game)
        return None

    def draw(self):
        pyxel.cls(2)
        self.steam.draw(14)
        ctext(14, "本日のととのい", 7, 0)
        for i, r in enumerate(self.game.results):
            mark = "◎" if r.totonoi else "△"
            ctext(34 + i * 13, f"第{r.set_no}セット {mark} {int(r.points):>4}点", 7, 0)
        ctext(78, f"合計 {self.total}点", 10, 0)
        if self.new_record and (self.t // 10) % 2:
            ctext(92, "ハイスコア更新！", 8, 7)
        ctext(106, "称号", 15, 0)
        ctext(118, self.rank, self.rank_col, 0)
        if self.t > FPS and (self.t // 15) % 2:
            ctext(132, "A: タイトルへ", 7, 0)


# ---------------------------------------------------------------------------
# ゲーム本体
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        global FONT
        pyxel.init(W, H, title="ととのい道", fps=FPS)
        FONT = pyxel.Font("assets/umplus_j10r.bdf")
        pyxel.mouse(False)
        setup_sounds()
        self.hiscore = 0
        self.results = []
        self.scene = TitleScene(self)
        pyxel.run(self.update, self.draw)

    def start(self):
        self.results = []
        self.scene = SaunaScene(self, Body(1))

    def update(self):
        nxt = self.scene.update()
        if nxt is not None:
            self.scene = nxt

    def draw(self):
        self.scene.draw()


if __name__ == "__main__":
    Game()
