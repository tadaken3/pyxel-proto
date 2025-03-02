import pyxel
import json

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.is_jumping = False
        self.direction = 1  # 1: 右向き, -1: 左向き
        self.state = "small"  # small, super, fire
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.width = 8
        self.height = 8
        self.gravity = 0.4
        self.jump_power = -8
        self.speed = 2
        self.animation_frame = 0
        self.animation_counter = 0

    def update(self):
        # 入力処理
        if pyxel.btn(pyxel.KEY_LEFT):
            self.vx = -self.speed
            self.direction = -1
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.vx = self.speed
            self.direction = 1
        else:
            self.vx = 0

        # ジャンプ
        if (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_UP)) and not self.is_jumping:
            self.vy = self.jump_power
            self.is_jumping = True

        # 重力
        self.vy += self.gravity
        
        # 位置更新
        self.x += self.vx
        self.y += self.vy

        # アニメーション更新
        self.animation_counter += 1
        if self.animation_counter > 5:
            self.animation_counter = 0
            self.animation_frame = (self.animation_frame + 1) % 3

    def draw(self, camera_x):
        # プレイヤーの描画（仮のスプライト）
        sprite_x = 0 if self.vx == 0 else self.animation_frame * 8
        pyxel.blt(
            self.x - camera_x, 
            self.y, 
            0, 
            sprite_x, 
            0, 
            8 * self.direction, 
            8, 
            5
        )

class Map:
    def __init__(self, level_file):
        self.tile_size = 8
        self.width = 0
        self.height = 0
        self.tile_data = []
        self.load_map(level_file)
        self.width_px = self.width * self.tile_size
        self.height_px = self.height * self.tile_size

    def load_map(self, level_file):
        try:
            with open(level_file, 'r') as f:
                level_data = json.load(f)
                self.width = level_data.get('width', 0)
                self.height = level_data.get('height', 0)
                self.tile_data = level_data.get('tile_data', [])
        except FileNotFoundError:
            # 仮のマップデータを作成
            self.width = 32
            self.height = 16
            self.tile_data = [[0 for _ in range(self.width)] for _ in range(self.height)]
            # 地面を設定
            for x in range(self.width):
                self.tile_data[self.height - 1][x] = 1

    def check_collision(self, player):
        # 衝突判定の改善
        # プレイヤーの四隅の座標からタイル位置を計算
        left = int(player.x // self.tile_size)
        right = int((player.x + player.width - 1) // self.tile_size)
        top = int(player.y // self.tile_size)
        bottom = int((player.y + player.height - 1) // self.tile_size)
        
        # 範囲チェック
        if left < 0:
            player.x = 0
            left = 0
        if right >= self.width:
            player.x = (self.width - 1) * self.tile_size - player.width
            right = self.width - 1
            
        # 下方向の衝突（地面や床）
        if 0 <= bottom < self.height:
            if self.tile_data[bottom][left] > 0 or self.tile_data[bottom][right] > 0:
                player.y = bottom * self.tile_size - player.height
                player.vy = 0
                player.is_jumping = False
        
        # 上方向の衝突（ブロックの下側）
        if 0 <= top < self.height:
            if self.tile_data[top][left] > 0 or self.tile_data[top][right] > 0:
                # ブロックの下に衝突
                player.y = (top + 1) * self.tile_size
                player.vy = 0
                
                # ここでブロックとの衝突処理（例：?ブロックからアイテム出現など）
                # 実装は省略
        
        # 左右の衝突（壁）
        # 左側の衝突
        if 0 <= left < self.width and 0 <= top < self.height and 0 <= bottom < self.height:
            if self.tile_data[top][left] > 0 or self.tile_data[bottom][left] > 0:
                player.x = (left + 1) * self.tile_size
                player.vx = 0
        
        # 右側の衝突
        if 0 <= right < self.width and 0 <= top < self.height and 0 <= bottom < self.height:
            if self.tile_data[top][right] > 0 or self.tile_data[bottom][right] > 0:
                player.x = right * self.tile_size - player.width
                player.vx = 0

    def draw(self, camera_x):
        # 画面に表示される範囲のタイルのみ描画
        start_x = int(camera_x // self.tile_size)
        end_x = min(start_x + (pyxel.width // self.tile_size) + 1, self.width)
        
        for y in range(self.height):
            for x in range(start_x, end_x):
                if x < 0 or x >= self.width or y < 0 or y >= self.height:
                    continue
                    
                tile_id = self.tile_data[y][x]
                if tile_id > 0:
                    # タイルIDに応じて描画
                    color = 0
                    if tile_id == 1:  # 地面
                        color = 4  # 茶色
                    elif tile_id == 2:  # レンガブロック
                        color = 8  # 赤
                    elif tile_id == 3:  # ?ブロック
                        color = 10  # 黄色
                    else:
                        color = tile_id + 3
                        
                    # タイルを描画
                    pyxel.rect(
                        x * self.tile_size - camera_x,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                        color
                    )
                    
                    # タイルの枠線を描画
                    pyxel.rectb(
                        x * self.tile_size - camera_x,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                        0
                    )

class EnemyManager:
    def __init__(self, level_file):
        self.enemies = []
        self.load_enemies(level_file)

    def load_enemies(self, level_file):
        try:
            with open(level_file, 'r') as f:
                level_data = json.load(f)
                objects_data = level_data.get('objects', [])
                for obj_data in objects_data:
                    if obj_data.get('type') == 'goomba':
                        self.enemies.append(Goomba(obj_data.get('x'), obj_data.get('y')))
                    # 他のオブジェクトタイプも追加可能
        except FileNotFoundError:
            # 仮の敵を配置
            self.enemies.append(Goomba(120, 112))

    def update(self, map_obj):
        for enemy in self.enemies:
            enemy.update(map_obj)

    def check_collision(self, player):
        for enemy in self.enemies:
            # 敵との衝突判定
            if (abs(player.x - enemy.x) < (player.width + enemy.width) // 2 and
                abs(player.y - enemy.y) < (player.height + enemy.height) // 2):
                # プレイヤーが上から踏んだ場合
                if player.vy > 0 and player.y < enemy.y:
                    enemy.is_alive = False
                    player.vy = -5  # 踏んだ後に少しジャンプ
                    player.score += 100
                # 横から当たった場合
                else:
                    # プレイヤーがダメージを受ける処理
                    pass

    def draw(self, camera_x):
        for enemy in self.enemies:
            if enemy.is_alive:
                enemy.draw(camera_x)

class Goomba:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = -0.5  # 左に移動
        self.vy = 0
        self.width = 8
        self.height = 8
        self.is_alive = True
        self.gravity = 0.4
        self.is_on_ground = False

    def update(self, map_obj):
        if not self.is_alive:
            return
            
        # 重力
        self.vy += self.gravity
        
        # 位置更新
        self.x += self.vx
        self.y += self.vy
        
        # マップとの衝突判定
        self.check_map_collision(map_obj)
        
    def check_map_collision(self, map_obj):
        # タイル座標に変換
        tile_size = map_obj.tile_size
        left = int(self.x // tile_size)
        right = int((self.x + self.width - 1) // tile_size)
        top = int(self.y // tile_size)
        bottom = int((self.y + self.height - 1) // tile_size)
        
        # 範囲チェック
        if left < 0 or right >= map_obj.width:
            # 壁に当たったら向きを変える
            self.vx = -self.vx
            # 位置を調整
            if left < 0:
                self.x = 0
            if right >= map_obj.width:
                self.x = (map_obj.width - 1) * tile_size - self.width
        
        # 下方向の衝突（地面）
        self.is_on_ground = False
        if 0 <= bottom < map_obj.height:
            if (left >= 0 and right < map_obj.width and 
                (map_obj.tile_data[bottom][left] > 0 or map_obj.tile_data[bottom][right] > 0)):
                self.y = bottom * tile_size - self.height
                self.vy = 0
                self.is_on_ground = True
        
        # 左右の衝突（壁）
        if 0 <= top < map_obj.height and 0 <= bottom < map_obj.height:
            # 左側の衝突
            if left >= 0 and (map_obj.tile_data[top][left] > 0 or map_obj.tile_data[bottom][left] > 0):
                self.x = (left + 1) * tile_size
                self.vx = -self.vx  # 向きを変える
            
            # 右側の衝突
            if right < map_obj.width and (map_obj.tile_data[top][right] > 0 or map_obj.tile_data[bottom][right] > 0):
                self.x = right * tile_size - self.width
                self.vx = -self.vx  # 向きを変える

    def draw(self, camera_x):
        # 敵の描画（仮のスプライト）
        pyxel.blt(
            self.x - camera_x,
            self.y,
            0,
            16,
            0,
            8,
            8,
            5
        )

class Game:
    def __init__(self):
        pyxel.init(256, 224, title="Super Mario 1-1 Clone")
        pyxel.load("mychra.pyxres")  # 既存のリソースファイルを使用

        self.init_game()
        
        # Pyxel のメインループ開始
        pyxel.run(self.update, self.draw)
    
    def init_game(self):
        self.map = Map("data/level1.json")
        self.player = Player(16, 112)  # スタート位置を修正
        self.enemies = EnemyManager("data/level1.json")
        self.camera_x = 0
        self.time = 400  # 制限時間
        self.time_counter = 0
        self.game_state = "title"  # title, playing, game_over, clear
        self.state_timer = 0  # 状態遷移用タイマー
        self.flag_y = 40  # ゴールのフラッグ位置

    def update(self):
        # ゲーム状態に応じた更新処理
        if self.game_state == "title":
            self.update_title()
        elif self.game_state == "playing":
            self.update_playing()
        elif self.game_state == "game_over":
            self.update_game_over()
        elif self.game_state == "clear":
            self.update_clear()
    
    def update_title(self):
        # タイトル画面の更新
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self.game_state = "playing"
    
    def update_playing(self):
        self.player.update()
        self.enemies.update(self.map)

        # 衝突判定
        self.map.check_collision(self.player)
        self.enemies.check_collision(self.player)

        # カメラ更新
        if self.player.x > pyxel.width // 2:
            self.camera_x = max(0, self.player.x - pyxel.width // 2)
        
        # タイマー更新
        self.time_counter += 1
        if self.time_counter >= 60:  # 1秒ごとに減少
            self.time_counter = 0
            self.time -= 1
            if self.time <= 0:
                self.game_state = "game_over"
                self.state_timer = 0

        # 画面外に落ちたらゲームオーバー
        if self.player.y > pyxel.height:
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.game_state = "game_over"
                self.state_timer = 0
            else:
                # 残機があれば再スタート
                self.player.x = 16
                self.player.y = 112  # 再スタート位置も修正
                self.player.vx = 0
                self.player.vy = 0
                self.camera_x = 0
        
        # ゴールフラッグに触れたらクリア
        flag_x = 240  # レベルデータから取得するべき
        if abs(self.player.x - flag_x) < 8:
            self.game_state = "clear"
            self.state_timer = 0
    
    def update_game_over(self):
        # ゲームオーバー画面の更新
        self.state_timer += 1
        if self.state_timer > 180:  # 3秒後
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
                self.init_game()  # ゲームをリセット
    
    def update_clear(self):
        # クリア画面の更新
        self.state_timer += 1
        
        # フラッグを下げるアニメーション
        if self.state_timer < 60:
            self.flag_y += 2
        
        if self.state_timer > 180:  # 3秒後
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
                self.init_game()  # ゲームをリセット

    def draw(self):
        pyxel.cls(12)  # 空色の背景
        
        if self.game_state == "title":
            self.draw_title()
        else:
            # マップとキャラクターの描画
            self.map.draw(self.camera_x)
            self.player.draw(self.camera_x)
            self.enemies.draw(self.camera_x)
            
            # HUD表示
            self.draw_hud()
            
            # 状態に応じた追加描画
            if self.game_state == "game_over":
                self.draw_game_over()
            elif self.game_state == "clear":
                self.draw_clear()
    
    def draw_title(self):
        # タイトル画面の描画
        pyxel.text(80, 80, "SUPER MARIO BROS", 7)
        pyxel.text(80, 100, "1-1 CLONE", 7)
        pyxel.text(80, 140, "PRESS SPACE TO START", 7)
    
    def draw_hud(self):
        # HUD表示
        pyxel.text(10, 5, f"SCORE:{self.player.score}", 7)
        pyxel.text(80, 5, f"COINS:{self.player.coins}", 7)
        pyxel.text(150, 5, f"TIME:{self.time}", 7)
        pyxel.text(220, 5, f"LIVES:{self.player.lives}", 7)
    
    def draw_game_over(self):
        # ゲームオーバー表示
        if self.state_timer > 30:  # 少し遅延させて表示
            pyxel.text(100, 100, "GAME OVER", 8)
            if self.state_timer > 120:
                pyxel.text(70, 120, "PRESS SPACE TO RESTART", 7)
    
    def draw_clear(self):
        # クリア表示
        # フラッグポールの描画
        flag_x = 240 - self.camera_x
        pyxel.rect(flag_x, 80, 2, 120, 7)  # ポール
        pyxel.rect(flag_x - 6, self.flag_y, 6, 6, 8)  # フラッグ
        
        if self.state_timer > 90:
            pyxel.text(100, 100, "STAGE CLEAR!", 7)
            if self.state_timer > 150:
                pyxel.text(70, 120, "PRESS SPACE TO CONTINUE", 7)

if __name__ == "__main__":
    Game()
