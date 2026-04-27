import pygame, sys, json, os
from pygame.locals import *
import random, time

# --- 1. СИСТЕМА ДАННЫХ ---
SETTINGS_FILE = 'settings.json'
SCORES_FILE = 'scores.json'

def load_json(file, default):
    if not os.path.exists(file):
        with open(file, 'w') as f: json.dump(default, f)
        return default
    with open(file, 'r') as f: return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
pygame.init()
FPS = 60
FramePerSec = pygame.time.Clock()
WIDTH, HEIGHT = 400, 600
DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Traffic Racer Ultra")

# Цвета
BLACK, WHITE, RED, GOLD = (0,0,0), (255,255,255), (255,0,0), (255,215,0)
GRAY, GREEN, BLUE, CYAN, PURPLE = (50,50,50), (0,255,0), (30,144,255), (0,255,255), (128,0,128)

font_small = pygame.font.SysFont("Roboto", 22)
font_big = pygame.font.SysFont("Roboto", 55)

# --- 3. КЛАССЫ ОБЪЕКТОВ ---

class Player(pygame.sprite.Sprite):
    def __init__(self, color):
        super().__init__()
        try:
            self.image = pygame.image.load("p1.png").convert_alpha()
            self.image.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        except:
            self.image = pygame.Surface((45, 80)); self.image.fill(color)
        self.rect = self.image.get_rect(center=(200, 520))

    def move(self, nitro_active):
        keys = pygame.key.get_pressed()
        step = 12 if nitro_active else 7
        if keys[K_LEFT] and self.rect.left > 0: self.rect.move_ip(-step, 0)
        if keys[K_RIGHT] and self.rect.right < WIDTH: self.rect.move_ip(step, 0)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed, player_rect):
        super().__init__()
        try: self.image = pygame.image.load("zlodei.png").convert_alpha()
        except: self.image = pygame.Surface((45, 80)); self.image.fill(RED)
        # Safe Spawn: не появляться прямо над игроком
        x_pos = random.randint(40, WIDTH-40)
        while player_rect.left - 50 < x_pos < player_rect.right + 50:
            x_pos = random.randint(40, WIDTH-40)
        self.rect = self.image.get_rect(center=(x_pos, -100))
        self.speed = speed

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.top > HEIGHT: self.kill()

class Collectible(pygame.sprite.Sprite):
    def __init__(self, c_type):
        super().__init__()
        self.type = c_type # "coin1", "coin2", "nitro", "shield", "repair"
        
        # Логика выбора картинки
        if self.type == "coin1":
            try:
                self.image = pygame.image.load("coin_orig.png").convert_alpha()
                self.image = pygame.transform.scale(self.image, (30, 30))
            except:
                self.image = pygame.Surface((25, 25)); self.image.fill(GOLD)
        
        elif self.type == "coin2":
            try:
                self.image = pygame.image.load("coin2.png").convert_alpha()
                self.image = pygame.transform.scale(self.image, (40, 40)) # Вторая монета чуть больше
            except:
                self.image = pygame.Surface((35, 35)); self.image.fill((255, 100, 0)) # Оранжевая если нет фото
        
        elif self.type == "nitro": 
            self.image = pygame.Surface((30, 30)); self.image.fill(CYAN)
        elif self.type == "shield": 
            self.image = pygame.Surface((30, 30)); self.image.fill(PURPLE)
        elif self.type == "repair": 
            self.image = pygame.Surface((30, 30)); self.image.fill(GREEN)
        
        self.rect = self.image.get_rect(center=(random.randint(30, WIDTH-30), -50))

    def update(self, speed):
        self.rect.move_ip(0, speed)
        if self.rect.top > HEIGHT: self.kill()

class Button:
    def __init__(self, x, y, w, h, text, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color

    def draw(self, surf):
        # Рисуем саму кнопку
        pygame.draw.rect(surf, self.color, self.rect, border_radius=10)
        # Рисуем текст по центру кнопки
        t = font_small.render(self.text, True, WHITE)
        surf.blit(t, (self.rect.centerx - t.get_width()//2, self.rect.centery - t.get_height()//2))

    # ВОТ ЭТОТ МЕТОД НУЖНО ДОБАВИТЬ:
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
# --- 4. ОСНОВНОЙ ДВИЖОК ---
class RacingApp:
    def __init__(self):
        self.settings = load_json(SETTINGS_FILE, {"snake_color": [255,255,255], "sound_on": True, "diff": "Med"})
        self.leaderboard = load_json(SCORES_FILE, [])
        self.state = "MENU"
        self.player_name = input("Enter Username: ") or "Guest"
        try: self.bg = pygame.image.load("fon.png").convert()
        except: self.bg = pygame.Surface((WIDTH, HEIGHT)); self.bg.fill((80,80,80))

    def play_sound(self, sound_file):
        if self.settings['sound_on']:
            try: pygame.mixer.Sound(sound_file).play()
            except: pass

    def menu(self):
        btn_p = Button(100, 200, 200, 50, "PLAY", GREEN)
        btn_s = Button(100, 270, 200, 50, "SETTINGS", BLUE)
        btn_l = Button(100, 340, 200, 50, "LEADERBOARD", GOLD)
        btn_q = Button(100, 410, 200, 50, "QUIT", RED)
        
        while self.state == "MENU":
            DISPLAYSURF.fill(BLACK)
            DISPLAYSURF.blit(font_big.render("TRAFFIC RACER", True, WHITE), (35, 80))
            for b in [btn_p, btn_s, btn_l, btn_q]: b.draw(DISPLAYSURF)
            
            for event in pygame.event.get():
                if event.type == QUIT: pygame.quit(); sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    if btn_p.is_clicked(event.pos): self.state = "GAME"
                    if btn_s.is_clicked(event.pos): self.state = "SETTINGS"
                    if btn_l.is_clicked(event.pos): self.state = "LEADERBOARD"
                    if btn_q.is_clicked(event.pos): pygame.quit(); sys.exit()
            pygame.display.update()
            FramePerSec.tick(FPS)

    def settings_menu(self):
        while self.state == "SETTINGS":
            DISPLAYSURF.fill(GRAY)
            s_txt = f"Sound: {'ON' if self.settings['sound_on'] else 'OFF'}"
            btn_snd = Button(50, 200, 300, 50, s_txt, BLUE)
            btn_clr = Button(50, 270, 300, 50, "Change Car Color", (100,100,100))
            btn_bak = Button(150, 450, 100, 50, "BACK", BLACK)
            
            for b in [btn_snd, btn_clr, btn_bak]: b.draw(DISPLAYSURF)
            for event in pygame.event.get():
                if event.type == MOUSEBUTTONDOWN:
                    if btn_snd.is_clicked(event.pos): 
                        self.settings['sound_on'] = not self.settings['sound_on']
                    if btn_clr.is_clicked(event.pos):
                        self.settings['snake_color'] = [random.randint(100,255) for _ in range(3)]
                    if btn_bak.is_clicked(event.pos): 
                        save_json(SETTINGS_FILE, self.settings); self.state = "MENU"
                if event.type == QUIT: pygame.quit(); sys.exit()
            pygame.display.update()
            FramePerSec.tick(FPS)

    def leaderboard_view(self):
        while self.state == "LEADERBOARD":
            DISPLAYSURF.fill(BLACK)
            DISPLAYSURF.blit(font_big.render("TOP 10", True, GOLD), (130, 50))
            for i, entry in enumerate(self.leaderboard[:10]):
                txt = f"{i+1}. {entry['name']} - {entry['score']}"
                DISPLAYSURF.blit(font_small.render(txt, True, WHITE), (80, 150 + i*30))
            
            btn_bak = Button(150, 500, 100, 40, "BACK", RED)
            btn_bak.draw(DISPLAYSURF)
            for event in pygame.event.get():
                if event.type == MOUSEBUTTONDOWN and btn_bak.is_clicked(event.pos): self.state = "MENU"
                if event.type == QUIT: pygame.quit(); sys.exit()
            pygame.display.update()
            FramePerSec.tick(FPS)

    def game_run(self):
        # 1. Инициализация игрока и групп
        diff_key = 'difficulty' if 'difficulty' in self.settings else 'diff'
        
        player = Player(self.settings['snake_color'])
        enemies = pygame.sprite.Group()
        coins = pygame.sprite.Group()     # Группа для монет
        powerups = pygame.sprite.Group()  # Группа для бонусов
        all_sprites = pygame.sprite.Group(player)
        
        game_speed = 5 if self.settings.get(diff_key) == "Easy" else 8
        score, coin_count, distance = 0, 0, 0
        active_p, p_timer = None, 0
        
        if self.settings['sound_on']:
            try:
                pygame.mixer.music.load("background.mp3")
                pygame.mixer.music.play(-1)
            except: pass

        # 2. Настройка таймеров
        pygame.time.set_timer(USEREVENT+1, 1000) # Враги
        pygame.time.set_timer(USEREVENT+2, 1200) # МОНЕТЫ
        pygame.time.set_timer(USEREVENT+3, 6000) # Бонусы

        while self.state == "GAME":
            now = pygame.time.get_ticks()
            DISPLAYSURF.blit(self.bg, (0,0))
            
            # Увеличение дистанции
            distance += game_speed / 15

            for event in pygame.event.get():
                if event.type == QUIT: pygame.quit(); sys.exit()
                
                # Спавн Врагов
                if event.type == USEREVENT+1:
                    e = Enemy(game_speed, player.rect)
                    enemies.add(e)
                    all_sprites.add(e)
                
                # Спавн МОНЕТ (Алгоритм: 20% шанс на редкую монету)
                if event.type == USEREVENT+2:
                    chosen_type = "coin2" if random.random() < 0.2 else "coin1"
                    c = Collectible(chosen_type)
                    coins.add(c)
                    all_sprites.add(c)
                
                # Спавн Бонусов
                if event.type == USEREVENT+3:
                    p = Collectible(random.choice(["nitro", "shield", "repair"]))
                    powerups.add(p)
                    all_sprites.add(p)

            # 3. Логика движения
            if active_p == "nitro" and now > p_timer: active_p = None
            player.move(active_p == "nitro")
            
            enemies.update()
            coins.update(game_speed)
            powerups.update(game_speed)

            # 4. Обработка столкновений с монетами
            coin_hits = pygame.sprite.spritecollide(player, coins, True)
            for hit in coin_hits:
                # Начисление очков в зависимости от типа монеты
                if hit.type == "coin1":
                    score += 1
                elif hit.type == "coin2":
                    score += 3
                
                coin_count += 1
                if coin_count % 5 == 0: 
                    game_speed += 1 

            # 5. Обработка бонусов
            for p in pygame.sprite.spritecollide(player, powerups, True):
                active_p = p.type
                if p.type == "nitro": p_timer = now + 5000
                elif p.type == "repair": 
                    for e in enemies: e.kill()
                    active_p = None

            # 6. Коллизия с врагами
            if pygame.sprite.spritecollideany(player, enemies):
                if active_p == "shield":
                    pygame.sprite.spritecollide(player, enemies, True)
                    active_p = None
                else:
                    self.play_sound("crash.wav")
                    pygame.mixer.music.stop()
                    self.leaderboard.append({"name": self.player_name, "score": score})
                    self.leaderboard = sorted(self.leaderboard, key=lambda x: x['score'], reverse=True)[:10]
                    save_json(SCORES_FILE, self.leaderboard)
                    self.state = "MENU"

            # 7. ОТРИСОВКА
            for s in all_sprites: 
                DISPLAYSURF.blit(s.image, s.rect)
            
            # --- ИНТЕРФЕЙС ---
            # Score в левом верхнем углу
            DISPLAYSURF.blit(font_small.render(f"Score: {score}", True, BLACK), (10, 10))
            DISPLAYSURF.blit(font_small.render(f"Total Coins: {coin_count}", True, BLACK), (10, 35))
            
            # Distance в ПРАВОМ верхнем углу
            dist_txt = font_small.render(f"Distance: {int(distance)}m", True, BLACK)
            DISPLAYSURF.blit(dist_txt, (WIDTH - dist_txt.get_width() - 10, 10))
            
            if active_p:
                DISPLAYSURF.blit(font_small.render(f"MOD: {active_p.upper()}", True, RED), (WIDTH//2 - 40, 10))
            
            pygame.display.update()
            FramePerSec.tick(FPS)

# --- ЗАПУСК ---
if __name__ == "__main__":
    app = RacingApp()
    while True:
        if app.state == "MENU": app.menu()
        if app.state == "GAME": app.game_run()
        if app.state == "SETTINGS": app.settings_menu()
        if app.state == "LEADERBOARD": app.leaderboard_view()