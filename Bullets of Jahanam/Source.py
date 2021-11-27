import pygame, sys, os, time, random, math, json
from pygame.locals import *
pygame.init()

Width, Height = 800, 600
win = pygame.display.set_mode((Width, Height))
pygame.display.set_caption("Bullets of Jahanam")

icons = [pygame.image.load(os.path.join("assets", "icon.ico")), pygame.image.load(os.path.join("assets", "icon_event.ico")), pygame.image.load(os.path.join("assets", "icon_slowmo.ico"))]
pygame.display.set_icon(icons[0])
chosen_icon = [False, False, False]

player_img = pygame.image.load(os.path.join("assets", "player.png"))
player_slowmo_img = pygame.image.load(os.path.join("assets", "player slowmo.png"))

class OBB:
    def __init__(self, center, size, angle):
        self.center = pygame.Vector2(center)
        self.size = pygame.Vector2(size)
        self.angle = angle

        # utility vectors for calculating corner of bounding box
        self._tl = pygame.Vector2(-self.size.x / 2, self.size.y / 2)
        self._tr = pygame.Vector2(self.size.x / 2, self.size.y / 2)
        self._bl = pygame.Vector2(-self.size.x / 2, -self.size.y / 2)
        self._br = pygame.Vector2(self.size.x / 2, -self.size.y / 2)

    @classmethod
    def from_rect(cls, rect:pygame.Rect):
        center = pygame.Vector2(rect.center)
        size = pygame.Vector2(rect.size)
        return cls(center, size, 0)

    @property
    def orientation(self) -> pygame.Vector2:
        o = pygame.Vector2()
        o.from_polar((1, self.angle))
        return o

    @property
    def topleft(self) -> pygame.Vector2:
        return self.center + self._tl.rotate(self.angle)

    @property
    def topright(self) -> pygame.Vector2:
        return self.center + self._tr.rotate(self.angle)

    @property
    def bottomleft(self) -> pygame.Vector2:
        return self.center + self._bl.rotate(self.angle)

    @property
    def bottomright(self) -> pygame.Vector2:
        return self.center + self._br.rotate(self.angle)

    def corners(self):
        return iter((self.topleft, self.topright, self.bottomright, self.bottomleft))

    def collideobb(self, obb):
        axes = iter((self.orientation, self.orientation.rotate(90), obb.orientation, obb.orientation.rotate(90)))
        for ax in axes:
            min_along1, max_along1 = 1E10, -1E10
            min_along2, max_along2 = 1E10, -1E10
            for corner in self.corners():
                p = ax.dot(corner)
                if p > max_along1:
                    max_along1 = p
                if p < min_along1:
                    min_along1 = p
            for corner in obb.corners():
                p = ax.dot(corner)
                if p > max_along2:
                    max_along2 = p
                if p < min_along2:
                    min_along2 = p
            if min_along1 <= max_along2 and max_along1 >= min_along2:
                continue
            return False
        return True

    def colliderect(self, rect):
        return self.collideobb(OBB.from_rect(rect))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.img = player_img
        self.speed = 5

        self.slowmo_timer = 0
        self.slowmo_cooldown = 0

        self.p_slowmo_timer = 0
        self.p_slowmo_cooldown = 0

        self.score = 0

        self.spawned = time.time()
        self.blink = [time.time(), True]

        self.rect = pygame.Rect(self.x+self.img.get_width()*0.5, self.y+self.img.get_height()*0.5, 1, 1)
        self.graze_rect = pygame.Rect(self.x-15, self.y-15, self.img.get_width()+30, self.img.get_height()+30)

    def render(self):
        if time.time() - self.spawned < 1.5:
            if time.time()-self.blink[0] >= 0.1:
                self.blink[0] = time.time()
                self.blink[1] = not self.blink[1]
            if self.blink[1]:
                self.img.set_alpha(255)
            else:
                self.img.set_alpha(100)
        else:
            if self.img.get_alpha() != 255:
                self.img.set_alpha(255)
        win.blit(self.img, (self.x, self.y))

        # slowmo bar
        if time.time()-self.slowmo_cooldown < 1:
            c = (255, 255, 255)
        elif time.time()-self.slowmo_timer < 3:
            c = (255, 255, 0)
        else:
            c = (255, 255, 255)
        pygame.draw.rect(win, c, (5, 5, 220, 40), 7)
        if time.time()-self.slowmo_cooldown < 1:
            pygame.draw.rect(win, c, (15, 15, 200*(time.time()-self.slowmo_cooldown), 20))
        elif time.time()-self.slowmo_timer < 3:
            pygame.draw.rect(win, c, (15, 15, 200*((abs(time.time()-self.slowmo_timer-3))/3), 20))
        else:
            pygame.draw.rect(win, c, (15, 15, 200, 20))

        # perfect slowmo
        surf = pygame.Surface((227, 47), SRCALPHA)
        if time.time()-self.p_slowmo_cooldown < 5:
            c = (255, 255, 255)
        elif time.time()-self.p_slowmo_timer < 3:
            c = (255, 255, 0)
        else:
            c = (255, 255, 255)
        pygame.draw.rect(surf, c, (3, 3, 220, 40), 7)
        if time.time()-self.p_slowmo_cooldown < 5:
            pygame.draw.rect(surf, c, (13, 13, 200*((time.time()-self.p_slowmo_cooldown)/5), 20))
        elif time.time()-self.p_slowmo_timer < 3:
            pygame.draw.rect(surf, c, (13, 13, 200*((abs(time.time()-self.p_slowmo_timer-3))/3), 20))
        else:
            pygame.draw.rect(surf, c, (13, 13, 200, 20))
        
        win.blit(pygame.transform.rotate(surf, 180), (Width-230, 2))

    def move(self):
        keys = pygame.key.get_pressed()
        if keys[K_a] and self.x > 0:
            self.x -= self.speed
        if keys[K_d] and self.x < Width-self.img.get_width():
            self.x += self.speed
        if keys[K_w] and self.y > 0:
            self.y -= self.speed
        if keys[K_s] and self.y < Height-self.img.get_height():
            self.y += self.speed

        self.rect = pygame.Rect(self.x+self.img.get_width()*0.5, self.y+self.img.get_height()*0.5, 1, 1)
        self.graze_rect = pygame.Rect(self.x-15, self.y-15, self.img.get_width()+30, self.img.get_height()+30)

class Attack:
    def __init__(self):
        self.attack = 0
        self.attack_timer = 0
        self.pre_attack = 0
        self.obstacles = []
        self.shoot_cooldown = 0
        
        self.angered = False
        self.angered_timer = 0
        self.angered_times = 0
        self.pre_angered = False

        self.modif = 0

        # attack 0
        self.offset = 0
        self.rotate_dir = 0

        # attack 1
        self.shot_dir = 0

        # attack 2
        self.edge = 0

        #attack 3
        self.subshot_timer = 0

        self.endlesstorture_timer = 0

    def attacks(self):
        global text_appear
        if time.time()-self.attack_timer >= 3:
            self.attack_timer = time.time()
            self.pre_attack = self.attack
            self.attack = random.randint(0, 4)
            if self.pre_attack != self.attack:
                player.score += 2

            if random.randint(0, 10) == 0 and not self.angered and not self.pre_angered and time.time()-player.spawned >= 1.5:
                self.obstacles = []
                self.angered = True
                self.angered_timer = time.time()
                self.modif += 4+self.angered_times
                self.angered_times += 1
            if not self.angered:
                if self.pre_angered:
                    player.score += 25
                self.pre_angered = False

        if self.angered and time.time()-self.angered_timer >= 29:
            self.angered = False
            self.obstacles = []
            self.modif = 0
            self.pre_angered = True
            text_appear = [False, 0]
        
        if player.score >= 1000:
            self.shot_dir = random.randint(0, 3)
            if time.time()-self.endlesstorture_timer >= .75:
                for _ in range(random.randint(1, 3)):
                    if self.shot_dir == 0:
                        x = random.randint(1, Width-1)
                        self.obstacles.append(Obstacle(x, -Obstacle.obstacles["Arrow"][0].get_height(), "Arrow", (x, 100), 2))
                    elif self.shot_dir == 1:
                        x = random.randint(1, Width-1)
                        self.obstacles.append(Obstacle(x, Height, "Arrow", (x, Height-100), 2))
                    elif self.shot_dir == 2:
                        y = random.randint(1, Height-1)
                        self.obstacles.append(Obstacle(-Obstacle.obstacles["Arrow"][0].get_width(), y, "Arrow", (100, y), 2))
                    else:
                        y = random.randint(1, Height-1)
                        self.obstacles.append(Obstacle(Width, y, "Arrow", (Width-100, y), 2))
                    
                self.endlesstorture_timer = time.time()


        if self.attack == 0:
            if time.time() - self.attack_timer <= .05 and self.pre_attack != 0:
                self.offset = random.uniform(0, math.pi*2)
                self.rotate_dir = random.randint(0, 1)
            if time.time()-self.shoot_cooldown >= .25:
                for x in range(12+self.modif):
                    rad = math.radians(x*360/(12+self.modif))+self.offset
                    x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                    if self.rotate_dir == 0:
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    else:
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5))
                self.offset += 0.1
                self.shoot_cooldown = time.time()

        elif self.attack == 1:
            self.shot_dir = random.randint(0, 3)
            if time.time()-self.shoot_cooldown >= .3:
                for _ in range(random.randint(2, 5+self.modif)):
                    if self.shot_dir == 0:
                        x = random.randint(1, Width-1)
                        self.obstacles.append(Obstacle(x, -Obstacle.obstacles["Arrow"][0].get_height(), "Arrow", (x, 100), 7))
                    elif self.shot_dir == 1:
                        x = random.randint(1, Width-1)
                        self.obstacles.append(Obstacle(x, Height, "Arrow", (x, Height-100), 7))
                    elif self.shot_dir == 2:
                        y = random.randint(1, Height-1)
                        self.obstacles.append(Obstacle(-Obstacle.obstacles["Arrow"][0].get_width(), y, "Arrow", (100, y), 7))
                    else:
                        y = random.randint(1, Height-1)
                        self.obstacles.append(Obstacle(Width, y, "Arrow", (Width-100, y), 7))
                    
                self.shoot_cooldown = time.time()

        elif self.attack == 2:
            self.edge = random.randint(0, 1)
            if time.time()-self.shoot_cooldown >= 1/((self.modif/4)+1):
                if self.edge == 0:
                    for x in range(8):
                        rad = math.radians(x*360/(8))
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, 1
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    for x in range(8):
                        rad = math.radians(x*360/(8))
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height-14
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    for x in range(8):
                        rad = math.radians(x*360/(8))
                        x, y = 1, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    for x in range(8):
                        rad = math.radians(x*360/(8))
                        x, y = Width-14, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                else:
                    for x in range(8):
                        rad = math.radians(x*360/(8))
                        x, y = 1, 1
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    for x in range(8):
                        rad = math.radians(x*360/(8))
                        x, y = 1, Height-14
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    for x in range(8):
                        rad = math.radians(x*360/(8))
                        x, y = Width-14, 1
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    for x in range(8):
                        rad = math.radians(x*360/(8))
                        x, y = Width-14, Height-14
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                
                self.shoot_cooldown = time.time()

        elif self.attack == 3:
            if time.time() - self.attack_timer <= .05 and self.pre_attack != 0:
                self.offset = random.uniform(0, math.pi*2)
                self.rotate_dir = random.randint(0, 1)
            if time.time()-self.shoot_cooldown >= .25:
                for x in range(4):
                    rad = math.radians(x*360/4)+self.offset
                    x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                    if self.rotate_dir == 0:
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, True))
                    else:
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5, True))
                self.offset += 0.1+self.modif/30
                self.shoot_cooldown = time.time()

        elif self.attack == 4:
            if time.time()-self.shoot_cooldown >= 1/((self.modif/6)+1):
                # Top
                x, y = Width*0.5-Obstacle.obstacles["Arrow"][0].get_width()*0.5, -Obstacle.obstacles["Arrow"][0].get_height()
                self.obstacles.append(Obstacle(x, y, "Arrow", player.rect.center, 5))

                # Bottom
                x, y = Width*0.5-Obstacle.obstacles["Arrow"][0].get_width()*0.5, Height
                self.obstacles.append(Obstacle(x, y, "Arrow", player.rect.center, 5))

                # Left
                x, y = -Obstacle.obstacles["Arrow"][0].get_width(), Height*0.5-Obstacle.obstacles["Arrow"][0].get_height()*0.5
                self.obstacles.append(Obstacle(x, y, "Arrow", player.rect.center, 5))

                # Right
                x, y = Width, Height*0.5-Obstacle.obstacles["Arrow"][0].get_height()*0.5
                self.obstacles.append(Obstacle(x, y, "Arrow", player.rect.center, 5))

                # TL Corner
                x, y = -Obstacle.obstacles["Arrow"][0].get_width(), -Obstacle.obstacles["Arrow"][0].get_height()
                self.obstacles.append(Obstacle(x, y, "Arrow", player.rect.center, 5))

                # BL Corner
                x, y = -Obstacle.obstacles["Arrow"][0].get_width(), Height
                self.obstacles.append(Obstacle(x, y, "Arrow", player.rect.center, 5))

                # TR Corner
                x, y = Width, -Obstacle.obstacles["Arrow"][0].get_height()
                self.obstacles.append(Obstacle(x, y, "Arrow", player.rect.center, 5))

                # BR Corner
                x, y = Width, Height
                self.obstacles.append(Obstacle(x, y, "Arrow", player.rect.center, 5))
                
                self.shoot_cooldown = time.time()

class Obstacle:
    obstacles = {
        "Fireball": [pygame.image.load(os.path.join("assets", "fireball.png")), pygame.image.load(os.path.join("assets", "fireball slowmo.png"))],
        "Arrow": [pygame.image.load(os.path.join("assets", "arrow.png")), pygame.image.load(os.path.join("assets", "arrow slowmo.png"))],
    }
    def __init__(self, x, y, obs_type, end_loc, speed, flip = False):
        self.x = x
        self.y = y
        self.obs_type = obs_type
        if time.time()-player.p_slowmo_timer >= 3:
            self.img = self.obstacles[obs_type][0]
            self._img = self.obstacles[obs_type][0]
        else:
            self.img = self.obstacles[obs_type][1]
            self._img = self.obstacles[obs_type][1]
        self.start_v = pygame.Vector2(self.x, self.y)
        self.end_v = pygame.Vector2(end_loc)
        self.speed = speed
        self.orig_speed = speed

        self.rotation = math.degrees(math.atan2(y-end_loc[1], end_loc[0]-x))
        self.rotated = False
        self.orig_img = self.img
        self.img = pygame.transform.rotate(self.img, self.rotation)

        self.flip = flip
        self.flip_dir = [False, False]
        self.flipped = False

        self.rect = OBB((self.x+self.orig_img.get_width()*0.5, self.y+self.orig_img.get_height()*0.5), self.orig_img.get_size(), -self.rotation)

    def render(self):
        win.blit(self.img, (self.x, self.y))

    def move(self):
        vel = (self.end_v-self.start_v).normalize()*self.speed
        if self.flip_dir[0]:
            vel.x *= -1
        if self.flip_dir[1]:
            vel.y *= -1

        self.x += vel.x; self.y += vel.y
        self.rect.center.x, self.rect.center.y = self.x+self.img.get_width()*0.5, self.y+self.img.get_height()*0.5

    def off_screen(self, obs_list):
        if self.x+self.rect.size[0] < 0 or self.x > Width or self.y+self.rect.size[1] < 0 or self.y > Height:
            if self.flip and not self.flipped:
                self.flipped = True
                if self.x+self.rect.size[0] < 0 or self.x > Width:
                    self.flip_dir[0] = True
                    self.img = pygame.transform.flip(self.img, True, False)
                elif self.y+self.rect.size[1] < 0 or self.y > Height:
                    self.flip_dir[1] = True
                    self.img = pygame.transform.flip(self.img, False, True)
            else:
                try:
                    obs_list.remove(self)
                except:
                    pass
        return obs_list

player = Player(384, 284)
attack = Attack()
clock = pygame.time.Clock()
font = pygame.font.Font("assets/game-font.ttf", 48)

angered_text = font.render("You've angered the gods", True, (255,255,255))
angered_text.set_alpha(0)
text_appear = [False, 0]

if "score.json" in os.listdir("."):
    with open("score.json", "r") as f:
        score_data = json.load(f)
else:
    score_data = [0, 0]
    with open("score.json", "w") as f:
        json.dump(score_data, f)

a_c = [128, "+"]
last_call = time.time()

menu_open = True
paused = False

try:
    pygame.mixer.music.load(os.path.join("assets", "Into Jahanam.ogg"))
except:
    pass

def main_menu():
    global player, attack, angered_text, text_appear, a_c, last_call, menu_open

    title_font = pygame.font.Font("assets/game-font.ttf", 86)

    title = title_font.render("Bullets of Jahanam", 1, (255, 255, 255))
    text = font.render("Press any key to start", 1, (255, 255, 255))
    hscore_text = font.render(f"High Score: {score_data[0]}", 1, (255, 255, 255))
    lscore_text = font.render(f"Last Score: {score_data[1]}", 1, (255, 255, 255))
    while True:
        win.fill((0, 0, 0))
        win.blit(title, (Width*0.5-title.get_width()*0.5, 20))
        win.blit(text, (Width*0.5-text.get_width()*0.5, Height*0.5-text.get_height()*0.5))
        win.blit(hscore_text, (50, Height-20-hscore_text.get_height()))
        win.blit(lscore_text, (Width-50-lscore_text.get_width(), Height-20-lscore_text.get_height()))
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                player = Player(384, 284)
                attack = Attack()

                angered_text.set_alpha(0)
                text_appear = [False, 0]

                a_c = [128, "+"]
                last_call = time.time()

                menu_open = False
                return

        pygame.display.set_caption(f"Bullets of Jahanam | FPS: {int(clock.get_fps())}")
        pygame.display.flip()

def pause():
    global paused, menu_open, last_call

    surf = pygame.Surface((800, 600))
    surf.fill((0, 0, 0))
    surf.set_alpha(128)
    win.blit(surf, (0, 0))

    pause_font = pygame.font.Font("assets/game-font.ttf", 86)
    text_font = pygame.font.Font("assets/game-font.ttf", 32)

    pause_text = pause_font.render("Paused", 1, (255, 255, 255))
    text = text_font.render("Press ESC to quit or press any key to continue", 1, (255, 255, 255))

    win.blit(pause_text, (Width*0.5-pause_text.get_width()*0.5, Height*0.5-pause_text.get_height()*0.5))
    win.blit(text, (Width*0.5-text.get_width()*0.5, Height*0.5-text.get_height()*0.5+pause_text.get_height()))
    
    pygame.display.flip()

    timers = [
        time.time()-player.spawned,
        time.time()-player.blink[0],
        time.time()-player.slowmo_cooldown if player.slowmo_cooldown else time.time(),
        time.time()-player.slowmo_timer if player.slowmo_timer else time.time(),
        time.time()-player.p_slowmo_cooldown if player.p_slowmo_cooldown else time.time(),
        time.time()-player.p_slowmo_timer if player.p_slowmo_timer else time.time(),
        time.time()-attack.attack_timer if attack.attack_timer else time.time(),
        time.time()-attack.angered_timer if attack.angered_timer else time.time(),
        time.time()-attack.endlesstorture_timer if attack.endlesstorture_timer else time.time(),
        time.time()-attack.shoot_cooldown if attack.shoot_cooldown else time.time(),
        time.time()-last_call
    ]

    while True:
        # fix timers
        player.spawned = time.time()-timers[0]
        player.blink[0] = time.time()-timers[1]
        player.slowmo_cooldown = time.time()-timers[2]
        player.slowmo_timer = time.time()-timers[3]
        player.p_slowmo_cooldown = time.time()-timers[4]
        player.p_slowmo_timer = time.time()-timers[5]
        attack.attack_timer = time.time()-timers[6]
        attack.angered_timer = time.time()-timers[7]
        attack.endlesstorture_timer = time.time()-timers[8]
        attack.shoot_cooldown = time.time()-timers[9]
        last_call = time.time()-timers[10]
        

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    menu_open = True
                    if score_data[0] < player.score:
                        score_data[0] = player.score
                    score_data[1] = player.score
                    with open("score.json", "w") as f:
                        json.dump(score_data, f)
                paused = False
                try:
                    pygame.mixer.music.unpause()
                except:
                    pass
                return

while True:
    if menu_open:
        try:
            pygame.mixer.music.stop()
        except:
            pass
        main_menu()
    if paused:
        try:
            pygame.mixer.music.pause()
        except:
            pass
        pause()

    try:
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(fade_ms=2000) 
    except:
        pass

    score_modif = 1
    clock.tick(60)
    win.fill((0, 0, 0))
    if attack.angered:
        if a_c[1] == "+":
            a_c[0] += .5
            if a_c[0] >= 200:
                a_c[1] = "-"
        else:
            a_c[0] -= .5
            if a_c[0] <= 128:
                a_c[1] = "+"
        win.fill((a_c[0], 0, 0))

        text = font.render(str(abs(round(time.time()-attack.angered_timer)-30)), True, (255, 255, 255))
        text = pygame.transform.scale(text, (text.get_width()*4, text.get_height()*4))
        text.set_alpha(50)
        win.blit(text, (Width*0.5-text.get_width()*0.5, Height*0.5-text.get_height()*0.5))
        if not text_appear[0] or angered_text.get_alpha() != 0:
            if text_appear[1] == 0:
                angered_text.set_alpha(angered_text.get_alpha()+3)
                if angered_text.get_alpha() >= 255:
                    text_appear[1] = 1
            else:
                angered_text.set_alpha(angered_text.get_alpha()-3)
            if angered_text.get_alpha() == 0:
                text_appear[0] = True
            attack.angered_timer = time.time()
            score_modif = 0
        win.blit(angered_text, (Width*0.5-angered_text.get_width()*0.5, Height*0.5-angered_text.get_height()*0.5))
    
    score_text = font.render(str(player.score), True, (255,255,255))
    win.blit(score_text, (Width*0.5-score_text.get_width()*0.5, 5))

    player.render()

    if attack.angered:
        if not chosen_icon[1]:
            pygame.display.set_icon(icons[1])
            chosen_icon = [False, True, False]
    elif time.time()-player.slowmo_timer < 3 or time.time()-player.p_slowmo_timer < 3:
        if not chosen_icon[2]:
            pygame.display.set_icon(icons[2])
            chosen_icon = [False, False, True]
    else:
        if not chosen_icon[0]:
            pygame.display.set_icon(icons[0])
            chosen_icon = [True, False, False]

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit(); sys.exit()

        if event.type == KEYDOWN:
            if event.key == K_SPACE and time.time()-player.slowmo_cooldown >= 1 and player.speed == 5:
                player.speed = 2
                player.slowmo_timer = time.time()
                player.img = player_slowmo_img
            if len(attack.obstacles) > 0:
                if event.key == K_LSHIFT and time.time()-player.p_slowmo_cooldown >= 5 and attack.obstacles[0].speed == attack.obstacles[0].orig_speed and time.time()-player.p_slowmo_timer >= 3:
                    player.p_slowmo_timer = time.time()
    
            if event.key == K_ESCAPE:
                paused = True

    if player.speed == 2 and time.time()-player.slowmo_timer >= 3:
        player.speed = 5
        player.slowmo_cooldown = time.time()
        player.img = player_img
    
    if len(attack.obstacles) > 0:
        if time.time()-player.p_slowmo_timer >= 3 and attack.obstacles[0].speed == attack.obstacles[0].orig_speed/2:
            player.p_slowmo_cooldown = time.time()
            for obs in attack.obstacles:
                obs.img = pygame.transform.flip(pygame.transform.rotate(Obstacle.obstacles[obs.obs_type][0], obs.rotation), obs.flip_dir[0], obs.flip_dir[1])
                obs.rotated = False

    for obs in attack.obstacles:
        obs.render()
        if time.time()-player.p_slowmo_timer < 3:
            obs.speed = obs.orig_speed/2
            if not obs.rotated:
                obs.img = pygame.transform.flip(pygame.transform.rotate(Obstacle.obstacles[obs.obs_type][1], obs.rotation), obs.flip_dir[0], obs.flip_dir[1])
                obs.rotated = True
        else:
            obs.speed = obs.orig_speed

        obs.move()
        obs_list = obs.off_screen(attack.obstacles)

        if obs.rect.colliderect(player.rect):
            if time.time() - player.spawned >= 1.5:
                if score_data[0] < player.score:
                    score_data[0] = player.score
                score_data[1] = player.score
                with open("score.json", "w") as f:
                    json.dump(score_data, f)
                
                menu_open = True
        if obs.rect.colliderect(player.graze_rect):
            score_modif += 1
    player.move()
    if angered_text.get_alpha() == 0:
        attack.attacks()
        if attack.angered:
            score_modif += 1
    
    if time.time() - player.spawned < 1.5:
        score_modif = 0

    if time.time()-last_call >= .1:
        player.score += 1*score_modif
        last_call = time.time()

    pygame.display.set_caption(f"Bullets of Jahanam | FPS: {int(clock.get_fps())}")
    pygame.display.flip()
