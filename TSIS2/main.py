import pygame, random, sys, psycopg2, json, os, math
from datetime import datetime
from collections import deque

# --- НАСТРОЙКИ ---
SETTINGS_FILE = 'settings.json'
DEFAULT_SETTINGS = {"snake_color": [0, 255, 0], "grid_overlay": True, "sound": True}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f: json.dump(DEFAULT_SETTINGS, f)
        return DEFAULT_SETTINGS
    with open(SETTINGS_FILE, 'r') as f: return json.load(f)

def save_settings(new_settings):
    with open(SETTINGS_FILE, 'w') as f: json.dump(new_settings, f)

pygame.init()
UI_HEIGHT = 60
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 520
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT - UI_HEIGHT) // GRID_SIZE 

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake: Pro Edition 2026")
font_main = pygame.font.SysFont('Arial', 24)
font_small = pygame.font.SysFont('Arial', 18)

WHITE, BLACK, RED, GRAY = (255, 255, 255), (0, 0, 0), (255, 0, 0), (50, 50, 50)
BLUE, GOLD, GREEN, DARK_RED = (30, 144, 255), (255, 215, 0), (0, 255, 0), (139, 0, 0)

# --- БД ---
try:
    conn = psycopg2.connect(dbname="postgres", 
    user="postgres", 
    password="alibek08", 
    host="localhost")
    conn.set_client_encoding('UTF8')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (user_id SERIAL PRIMARY KEY, user_name VARCHAR(255) UNIQUE);
        CREATE TABLE IF NOT EXISTS user_score (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(user_id), score INTEGER, level INTEGER, played_at TIMESTAMP DEFAULT NOW());
    """)
    conn.commit()
except Exception as e:
    print(f"Ошибка БД: {e}")
    # Можно продолжить без БД, если нужно, но тут мы выходим
    sys.exit()

class Button:
    def __init__(self, x, y, w, h, text, color=GRAY):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect, border_radius=5)
        txt = font_main.render(self.text, True, WHITE)
        surf.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))
    def is_clicked(self, pos): return self.rect.collidepoint(pos)

class TimedItem:
    def __init__(self, color, duration):
        self.pos, self.active, self.spawn_t, self.color, self.duration = (-1,-1), False, 0, color, duration
    def spawn(self, avoid):
        while True:
            p = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            if p not in avoid: 
                self.pos, self.active, self.spawn_t = p, True, pygame.time.get_ticks()
                break
    def update(self):
        if self.active and pygame.time.get_ticks() - self.spawn_t > self.duration:
            self.active = False

class SnakeGame:
    def __init__(self):
        self.settings = load_settings()
        self.state = "MENU"
        self.user_name = "Player" # Имя по умолчанию
        self.user_id = None
        self.reset_game()

    def reset_game(self):
        self.snake = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
        self.dir = (1, 0)
        self.score, self.level = 0, 1
        self.obs = []
        self.food = TimedItem(GREEN, 10000)
        self.poison = TimedItem(DARK_RED, 8000)
        self.last_gen_lvl = 0

    def get_user(self):
        cursor.execute("INSERT INTO users (user_name) VALUES (%s) ON CONFLICT (user_name) DO UPDATE SET user_name=EXCLUDED.user_name RETURNING user_id", (self.user_name,))
        self.user_id = cursor.fetchone()[0]
        conn.commit()

    def menu_screen(self):
        btn_play = Button(200, 200, 200, 50, "PLAY", GREEN)
        btn_lead = Button(200, 270, 200, 50, "LEADERBOARD", BLUE)
        btn_sett = Button(200, 340, 200, 50, "SETTINGS", GRAY)
        input_rect = pygame.Rect(200, 140, 200, 40)
        active_input = False

        while self.state == "MENU":
            screen.fill(BLACK)
            # Отрисовка ввода имени
            pygame.draw.rect(screen, GRAY if not active_input else BLUE, input_rect, 2)
            name_txt = font_main.render(self.user_name, True, WHITE)
            screen.blit(name_txt, (input_rect.x + 5, input_rect.y + 5))
            screen.blit(font_small.render("Type Name:", True, GOLD), (200, 115))

            for b in [btn_play, btn_lead, btn_sett]: b.draw(screen)
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN:
                    active_input = input_rect.collidepoint(e.pos)
                    if btn_play.is_clicked(e.pos): self.get_user(); self.state = "GAME"
                    if btn_lead.is_clicked(e.pos): self.state = "LEADERBOARD"
                    if btn_sett.is_clicked(e.pos): self.state = "SETTINGS"
                if e.type == pygame.KEYDOWN and active_input:
                    if e.key == pygame.K_BACKSPACE: self.user_name = self.user_name[:-1]
                    elif len(self.user_name) < 12: self.user_name += e.unicode

    def game_screen(self):
        self.reset_game()
        game_clock = pygame.time.Clock()
        while self.state == "GAME":
            # Генерация препятствий
            if self.level >= 3 and self.last_gen_lvl != self.level:
                self.obs = [(random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)) for _ in range(self.level)]
                self.last_gen_lvl = self.level

            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_UP and self.dir != (0,1): self.dir = (0,-1)
                    if e.key == pygame.K_DOWN and self.dir != (0,-1): self.dir = (0,1)
                    if e.key == pygame.K_LEFT and self.dir != (1,0): self.dir = (-1,0)
                    if e.key == pygame.K_RIGHT and self.dir != (-1,0): self.dir = (1,0)

            # Логика движения
            new_h = (self.snake[0][0]+self.dir[0], self.snake[0][1]+self.dir[1])
            if (new_h[0]<0 or new_h[0]>=GRID_WIDTH or new_h[1]<0 or new_h[1]>=GRID_HEIGHT or new_h in self.snake or new_h in self.obs):
                self.state = "GAMEOVER"; break

            self.snake.insert(0, new_h)

            # Проверка еды
            if self.food.active and new_h == self.food.pos:
                self.score += 1; self.food.active = False
                if self.score % 5 == 0: self.level += 1
            # Проверка яда (отнимает очки и укорачивает)
            elif self.poison.active and new_h == self.poison.pos:
                self.score = max(0, self.score - 2)
                self.poison.active = False
                if len(self.snake) > 1: self.snake.pop()
                self.snake.pop() # Укорачиваем дважды за яд
            else:
                self.snake.pop()

            # Спавн предметов (исправленный шанс)
            if not self.food.active and random.random() < 0.05: self.food.spawn(self.snake + self.obs)
            if not self.poison.active and random.random() < 0.02: self.poison.spawn(self.snake + self.obs)
            
            self.food.update()
            self.poison.update()

            # Рендер
            screen.fill(BLACK)
            if self.settings['grid_overlay']:
                for x in range(0, SCREEN_WIDTH, GRID_SIZE): pygame.draw.line(screen, (20,20,20), (x, UI_HEIGHT), (x, SCREEN_HEIGHT))
            
            for p in self.obs: pygame.draw.rect(screen, GRAY, (p[0]*GRID_SIZE, p[1]*GRID_SIZE+UI_HEIGHT, GRID_SIZE, GRID_SIZE))
            if self.food.active: pygame.draw.rect(screen, GREEN, (self.food.pos[0]*GRID_SIZE, self.food.pos[1]*GRID_SIZE+UI_HEIGHT, GRID_SIZE, GRID_SIZE))
            if self.poison.active: pygame.draw.rect(screen, RED, (self.poison.pos[0]*GRID_SIZE, self.poison.pos[1]*GRID_SIZE+UI_HEIGHT, GRID_SIZE, GRID_SIZE))
            
            for i, s in enumerate(self.snake):
                color = tuple(self.settings['snake_color']) if i == 0 else BLUE
                pygame.draw.rect(screen, color, (s[0]*GRID_SIZE, s[1]*GRID_SIZE+UI_HEIGHT, GRID_SIZE, GRID_SIZE))
            
            pygame.draw.rect(screen, GRAY, (0,0, SCREEN_WIDTH, UI_HEIGHT))
            screen.blit(font_main.render(f"Score: {self.score}  Lvl: {self.level}  User: {self.user_name}", True, WHITE), (10, 15))
            pygame.display.flip()
            game_clock.tick(8 + self.level)

    def game_over_screen(self):
        cursor.execute("INSERT INTO user_score (user_id, score, level) VALUES (%s, %s, %s)", (self.user_id, self.score, self.level))
        conn.commit()
        btn_retry = Button(150, 300, 140, 50, "RETRY", GREEN)
        btn_menu = Button(310, 300, 140, 50, "MENU", BLUE)
        while self.state == "GAMEOVER":
            screen.fill(BLACK)
            txt = font_main.render(f"GAME OVER! Score: {self.score}", True, RED)
            screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 150))
            btn_retry.draw(screen); btn_menu.draw(screen)
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if btn_retry.is_clicked(e.pos): self.state = "GAME"
                    if btn_menu.is_clicked(e.pos): self.state = "MENU"

    # Остальные методы (leaderboard_screen, settings_screen) остаются такими же...

    def settings_screen(self):
        btn_grid = Button(50, 100, 200, 40, f"Grid: {'ON' if self.settings['grid_overlay'] else 'OFF'}")
        btn_color = Button(50, 160, 200, 40, "Change Color", tuple(self.settings['snake_color']))
        btn_save = Button(200, 400, 200, 50, "SAVE & BACK", GREEN)
        while self.state == "SETTINGS":
            screen.fill(BLACK)
            btn_grid.draw(screen); btn_color.draw(screen); btn_save.draw(screen)
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if btn_grid.is_clicked(e.pos): 
                        self.settings['grid_overlay'] = not self.settings['grid_overlay']
                        btn_grid.text = f"Grid: {'ON' if self.settings['grid_overlay'] else 'OFF'}"
                    if btn_color.is_clicked(e.pos):
                        self.settings['snake_color'] = [random.randint(50,255) for _ in range(3)]
                        btn_color.color = tuple(self.settings['snake_color'])
                    if btn_save.is_clicked(e.pos):
                        save_settings(self.settings); self.state = "MENU"
    
    def leaderboard_screen(self):
        btn_back = Button(225, 450, 150, 40, "BACK", GRAY)
        cursor.execute("SELECT u.user_name, s.score, s.level, s.played_at FROM user_score s JOIN users u ON s.user_id = u.user_id ORDER BY s.score DESC LIMIT 10")
        data = cursor.fetchall()
        while self.state == "LEADERBOARD":
            screen.fill(BLACK)
            screen.blit(font_main.render("TOP 10 SCORES", True, GOLD), (220, 20))
            for i, r in enumerate(data):
                txt = font_small.render(f"{i+1}. {r[0][:10]:<10} | {r[1]:<5} | Lvl:{r[2]} | {r[3].strftime('%Y-%m-%d')}", True, WHITE)
                screen.blit(txt, (50, 70 + i*35))
            btn_back.draw(screen); pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.MOUSEBUTTONDOWN and btn_back.is_clicked(e.pos): self.state = "MENU"

    def run(self):
        while True:
            if self.state == "MENU": self.menu_screen()
            elif self.state == "GAME": self.game_screen()
            elif self.state == "GAMEOVER": self.game_over_screen()
            elif self.state == "LEADERBOARD": self.leaderboard_screen()
            elif self.state == "SETTINGS": self.settings_screen()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()