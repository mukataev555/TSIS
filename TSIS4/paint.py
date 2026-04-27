import pygame, sys, math
from pygame.locals import *
from collections import deque

pygame.init()

# Настройки экрана
fps = 120
timer = pygame.time.Clock()
WIDTH = 1000 
HEIGHT = 600
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('Paint by Mukataev Alibek07')

base_canvas = pygame.Surface((WIDTH, HEIGHT))
base_canvas.fill('white')

active_size = 3
active_color = (0, 0, 0)
active_shape = 6  
drawing = False
start_pos = (0, 0)
last_pos = (0, 0)
run = True

def flood_fill(surf, x, y, new_color):
    width, height = surf.get_size()
    try:
        target_color = surf.get_at((x, y))
    except IndexError: return
    if target_color == new_color: return

    queue = deque([(x, y)])
    pixels = pygame.PixelArray(surf)
    new_color_mapped = surf.map_rgb(new_color)
    target_color_mapped = surf.map_rgb(target_color)

    while queue:
        cx, cy = queue.popleft()
        if 0 <= cx < width and 0 <= cy < height:
            if pixels[cx, cy] == target_color_mapped:
                pixels[cx, cy] = new_color_mapped
                queue.append((cx + 1, cy))
                queue.append((cx - 1, cy))
                queue.append((cx, cy + 1))
                queue.append((cx, cy - 1))
    del pixels

def get_points(shape, start, end):
    x1, y1 = start
    x2, y2 = end
    w, h = x2 - x1, y2 - y1
    if shape == 2: return [(x1 + w // 2, y1), (x1, y2), (x2, y2)]
    elif shape == 3:
        side = abs(w)
        alt = int(side * (math.sqrt(3) / 2))
        direction = 1 if h > 0 else -1
        return [(x1 + w // 2, y1), (x1 + w // 2 - side // 2, y1 + alt * direction), (x1 + w // 2 + side // 2, y1 + alt * direction)]
    elif shape == 4: return [(x1 + w // 2, y1), (x2, y1 + h // 2), (x1 + w // 2, y2), (x1, y1 + h // 2)]
    return []

def draw_menu(color, size, shape):
    pygame.draw.rect(screen, 'gray', [0, 0, WIDTH, 70])
    pygame.draw.line(screen, 'black', (0, 70), (WIDTH, 70), 3)
    
    # Толщина
    t_btns = [pygame.draw.rect(screen, 'black', [10 + i*50, 15, 45, 45]) for i in range(3)]
    for i, t in enumerate([1, 3, 5]):
        pygame.draw.line(screen, 'white', (15 + i*50, 37), (50 + i*50, 37), t)
    curr_t = {1:0, 3:1, 5:2}.get(size, 1)
    pygame.draw.rect(screen, 'green', [10 + curr_t*50, 15, 45, 45], 3)

    # Кнопки инструментов
    sh_btns = []
    for i in range(8):
        btn = pygame.draw.rect(screen, 'black', [180 + i*55, 15, 45, 45])
        sh_btns.append(btn)
        if shape == i: pygame.draw.rect(screen, 'green', [180 + i*55, 15, 45, 45], 3)

    # Иконки (просто для визуала)
    pygame.draw.circle(screen, 'white', (202, 37), 12, 1) # 0
    pygame.draw.rect(screen, 'white', [243, 23, 28, 28], 1) # 1
    pygame.draw.polygon(screen, 'white', [(307, 23), (292, 52), (322, 52)], 1) # 2
    pygame.draw.polygon(screen, 'white', [(362, 23), (347, 48), (377, 48)], 1) # 3
    pygame.draw.polygon(screen, 'white', [(417, 20), (432, 37), (417, 54), (402, 37)], 1) # 4
    pygame.draw.rect(screen, 'white', [465, 25, 30, 25], 1) # 5 (Eraser)
    pygame.draw.circle(screen, 'white', (532, 37), 3) # 6 (Brush)
    pygame.draw.rect(screen, 'cyan', [585, 25, 30, 25], 1) # 7 (Fill)

    # Цвета
    rgbs = [(0, 0, 255), (255, 0, 0), (0, 255, 0), (0, 0, 0), (255, 255, 255), (255, 255, 0)]
    c_rects = [pygame.draw.rect(screen, c, [WIDTH - 210 + i*32, 22, 25, 25]) for i, c in enumerate(rgbs)]

    return t_btns, sh_btns, c_rects, rgbs

while run:
    timer.tick(fps)
    # Сначала рисуем накопленный холст
    screen.blit(base_canvas, (0, 0))

    mouse_pos = pygame.mouse.get_pos()

    if drawing:
        if active_shape == 5: # Ластик (рисуем сразу на холсте)
            pygame.draw.line(base_canvas, 'white', last_pos, mouse_pos, active_size * 10)
            last_pos = mouse_pos
        elif active_shape == 6: # Кисть (рисуем сразу на холсте)
            pygame.draw.line(base_canvas, active_color, last_pos, mouse_pos, active_size * 2)
            last_pos = mouse_pos
        else:
            # Предпросмотр фигур рисуем на SCREEN (временный контур)
            r = pygame.Rect(start_pos, (mouse_pos[0]-start_pos[0], mouse_pos[1]-start_pos[1]))
            r.normalize()
            if active_shape == 0: pygame.draw.ellipse(screen, active_color, r, active_size)
            elif active_shape == 1: pygame.draw.rect(screen, active_color, r, active_size)
            elif active_shape in [2,3,4]:
                pts = get_points(active_shape, start_pos, mouse_pos)
                if pts: pygame.draw.polygon(screen, active_color, pts, active_size)

    t_b, s_b, c_r, rgbs = draw_menu(active_color, active_size, active_shape)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            run = False
        
        if event.type == pygame.KEYDOWN:
            #Для сохранения при нажатии Ctrl + S
            if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
                # Сохраняем холст
                import datetime
                filename = f"painting_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                pygame.image.save(base_canvas, filename)
                print(f"Рисунок сохранен как {filename}")
        
        if event.type == MOUSEBUTTONDOWN:
            if event.pos[1] < 70: # Клик по меню
                for i, b in enumerate(t_b):
                    if b.collidepoint(event.pos): active_size = [1, 3, 5][i]
                for i, b in enumerate(s_b):
                    if b.collidepoint(event.pos): active_shape = i
                for i, r_c in enumerate(c_r):
                    if r_c.collidepoint(event.pos): active_color = rgbs[i]
            else: # Клик по холсту
                if active_shape == 7: # ЗАЛИВКА
                    flood_fill(base_canvas, event.pos[0], event.pos[1], active_color)
                else:
                    drawing = True
                    start_pos = event.pos
                    last_pos = event.pos
        
        if event.type == MOUSEBUTTONUP:
            if drawing:
                if active_shape not in [5, 6, 7]:
                    r = pygame.Rect(start_pos, (event.pos[0]-start_pos[0], event.pos[1]-start_pos[1]))
                    r.normalize()
                    if active_shape == 0: pygame.draw.ellipse(base_canvas, active_color, r, active_size)
                    elif active_shape == 1: pygame.draw.rect(base_canvas, active_color, r, active_size)
                    elif active_shape in [2,3,4]:
                        pts = get_points(active_shape, start_pos, event.pos)
                        if pts: pygame.draw.polygon(base_canvas, active_color, pts, active_size)
                drawing = False

    pygame.display.flip()

pygame.quit()