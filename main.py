import pyxel

class App:
    GROUND_Y = 100

    def __init__(self):
        pyxel.init(160, 120 , fps=60)
        pyxel.load('mychra.pyxres')
        self.init()
        pyxel.run(self.update, self.draw)

    def init(self):
        self.x = 72
        self.y = self.GROUND_Y - 8
        self.vy = 0 # Y方向の速度
        self.is_jumping = False
        self.gravity = 0.05 # 重力

    def input_key(self):
            pressed = pyxel.btn(pyxel.KEY_SPACE) or pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) #スマホのタップを検知する
            if pressed and not self.is_jumping:
                # ジャンプする
                self.vy = -2.5
                self.is_jumping = True # ジャンプ中

    def update(self):
        self.input_key()

        self.vy += self.gravity
        # 速度を更新
        self.y += self.vy

        # ニャンコを地面に着地させる
        if self.y > self.GROUND_Y - 8:
            self.y = self.GROUND_Y - 8
            self.is_jumping = False # 着地したらジャンプ中を解除
        
    def draw(self):
        pyxel.cls(0)
        pyxel.rect(0, self.GROUND_Y, pyxel.width, pyxel.height, 4)
        pyxel.blt(self.x, self.y, 0, 0, 0, 8, 8, 5)

App()
