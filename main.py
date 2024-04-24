import pyxel
import random

class App:
    

    def __init__(self):
        pyxel.init(160, 120 , fps=60)
        pyxel.load('mychra.pyxres')
        self.init()
        pyxel.run(self.update, self.draw)

    def init(self):
        # 地面の初期設定
        self.floors = []
        for i in range(10):
            floor_x = i * 16
            floor_y = random.randint(80, 100)
            floor_width = random.randint(10, 20)
            self.floors.append((floor_x, floor_y, floor_width))

        # プレイヤーの初期位置
        self.player_x = 20
        self.player_y = self.floors[0][1] - 8  # プレイヤーの高さを考慮

        self.is_jumping = False
        self.is_alive = True

        self.vy = 0 # Y方向の速度

        self.gravity = 0.05 # 重力

    def input_key(self):
            pressed = pyxel.btn(pyxel.KEY_SPACE) or pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) #スマホのタップを検知する
            if pressed and not self.is_jumping:
                # ジャンプする
                self.vy = -2.5
                self.is_jumping = True # ジャンプ中
            
            # ゲームオーバーの場合、任意のキーを押すとゲームをリセット
            elif pressed and not self.is_alive:
                self.init()
               

    def update(self):
        #生存していたらっていう条件があるので注意
        if self.is_alive:
            #self.input_key()
            self.vy += self.gravity
            self.player_y += self.vy

            # 地面を左にスクロールさせる
            for i in range(len(self.floors)):
                self.floors[i] = (self.floors[i][0] - 1, self.floors[i][1], self.floors[i][2])

            # プレイヤーが地面に接触しているかチェック
            for floor_x, floor_y, floor_width in self.floors:
                if floor_x <= self.player_x <= floor_x + floor_width and self.player_y >= floor_y:
                    self.player_y = floor_y
                    self.vy = 0
                    self.is_jumping = False
                    break

            # プレイヤーが画面外に出たらゲームオーバー
            if self.player_y > pyxel.height:
                if self.is_alive:
                    self.is_alive = False

    def draw(self):
        pyxel.cls(0)

        ## デバッグ用
        pyxel.text(10, 10, "player_x: " + str(self.player_x), 2)
        pyxel.text(10, 20, "player_y: " + str(self.player_y), 2)
        pyxel.text(10, 40, "is_alive: " + str(self.is_alive), 2)
        pyxel.text(10, 30, "floor_num: " + str(len(self.floors)), 2)
        pyxel.text(10, 50, "is_input_key: " + str(self.input_key()), 2)

        # 地面を描画
        for floor_x, floor_y, floor_width in self.floors:
            pyxel.rect(floor_x, floor_y, floor_width, 2, 4)


        #プレイヤーを描画
        pyxel.blt(self.player_x, self.player_y, 0, 0, 0, 8, 8, 5)

App()
