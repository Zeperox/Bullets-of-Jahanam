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
    def __init__(self, x, y, mirror = False):
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

        self.mirror = mirror

        self.rect = pygame.Rect(self.x+self.img.get_width()*0.5, self.y+self.img.get_height()*0.5, 1, 1)
        self.rect_img = pygame.Rect(self.x, self.y, self.img.get_width(), self.img.get_height())
        self.graze_rect = pygame.Rect(self.x-15, self.y-15, self.img.get_width()+30, self.img.get_height()+30)

    def render(self):
        if not self.mirror:
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

        # player
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

    def move(self):
        keys = pygame.key.get_pressed()
        if attack.mirror:
            mid_rect = pygame.Rect(Width*0.5-3, 0, 5, Height)
            if keys[K_a] or keys[K_LEFT]:
                if self.mirror:
                    if self.x < Width-self.img.get_width():
                        self.x += self.speed*dt
                        self.rect_img.x = self.x
                        if self.rect_img.colliderect(mid_rect):
                            self.x = mid_rect.left-self.rect_img.width
                else:
                    if self.x > 0:
                        self.x -= self.speed*dt
                        self.rect_img.x = self.x
                        if self.rect_img.colliderect(mid_rect):
                            self.x = mid_rect.right
            if keys[K_d] or keys[K_RIGHT]:
                if self.mirror:
                    if self.x > 0:
                        self.x -= self.speed*dt
                        self.rect_img.x = self.x
                        if self.rect_img.colliderect(mid_rect):
                            self.x = mid_rect.right
                else:
                    if self.x < Width-self.img.get_width():
                        self.x += self.speed*dt
                        self.rect_img.x = self.x
                        if self.rect_img.colliderect(mid_rect):
                            self.x = mid_rect.left-self.rect_img.width
        else:
            if keys[K_a] or keys[K_LEFT]:
                if self.x > 0:
                    self.x -= self.speed*dt
            if keys[K_d] or keys[K_RIGHT]:
                if self.x < Width-self.img.get_width():
                    self.x += self.speed*dt

        if keys[K_w] or keys[K_UP]:
            if self.y > 0:
                self.y -= self.speed*dt
        if keys[K_s] or keys[K_DOWN]:
            if self.y < Height-self.img.get_height():
                self.y += self.speed*dt

        self.rect = pygame.Rect(self.x+self.img.get_width()*0.5, self.y+self.img.get_height()*0.5, 1, 1)
        self.rect_img = pygame.Rect(self.x, self.y, self.img.get_width(), self.img.get_height())
        self.graze_rect = pygame.Rect(self.x-15, self.y-15, self.img.get_width()+30, self.img.get_height()+30)

class Attack:
    def __init__(self):
        self.attack = 0
        self.attack_timer = 0
        self.pending_attack = random.randint(0, 9)
        self.pre_attack = 0
        self.obstacles = []
        self.shoot_cooldown = 0
        self.attack_change_cooldown = 3
        
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
        self.skipped = [False, None]
        self.cleared = False

        self.attack_speed = 5
        self.time = 1

        # attack 2
        self.edge = 0

        # attack 3
        self.shoot2_cooldown = 0

        # attack 4
        self.collided_obs = []

        # attack 7
        self.mirror = False
        self.sub_att = [None, None]
        self.sub_att_cooldown = [0, 0]

        # endless torture
        self.endlesstorture_timer = 0
        self.shot_dir = 0

    def attacks(self):
        global text_appear
        angered_time = 29
        if difficulty == "Paragar":
            self.attack_change_cooldown = 10 if self.attack == 1 else 3
        elif difficulty == "Rahenga":
            self.attack_change_cooldown = 3 if self.attack == 0 else 10
            angered_time = 59
        if time.time()-self.attack_timer >= self.attack_change_cooldown:
            self.attack_timer = time.time()
            self.pre_attack = self.attack
            n = 3 if difficulty == "Ifren" else 4 if difficulty == "Jahanam" else 5 if difficulty == "Paragar" else 9
            self.sub_att = [None, None]
            if self.pending_attack > n:
                self.pending_attack = random.randint(0, n)
            self.attack = self.pending_attack
            self.pending_attack = random.randint(0, n)
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

        if self.angered and time.time()-self.angered_timer >= angered_time:
            self.angered = False
            self.obstacles = []
            self.modif = 0
            self.pre_angered = True
            text_appear = [False, 0]
        
        if difficulty != "Ifren":
            if difficulty == "Jahanam":
                et_data = [1000, 3]
            elif difficulty == "Paragar":
                et_data = [500, 5]
            else:
                et_data = [0, 10]

            if player.score >= et_data[0]:
                self.shot_dir = random.randint(0, 3)
                if time.time()-self.endlesstorture_timer >= .75:
                    for _ in range(random.randint(1, et_data[1])):
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


        if difficulty != "Rahenga":
            if difficulty == "Paragar":
                if self.pre_attack == 1 and self.attack != 1 and not self.cleared:
                    self.obstacles = []
                    self.cleared = True

            if self.attack == 0: # Spinny Boi
                if time.time() - self.attack_timer <= .05 and self.pre_attack != 0:
                    self.offset = random.uniform(0, math.pi*2)
                    self.rotate_dir = random.randint(0, 1)
                if time.time()-self.shoot_cooldown >= .25:
                    if difficulty == "Ifren":
                        n = 8
                    else:
                        n = 12

                    for x in range(n+self.modif):
                        rad = math.radians(x*360/(n+self.modif))+self.offset
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        if self.rotate_dir == 0:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5))
                    if difficulty == "Paragar":
                        for x in range(12+self.modif):
                            rad = math.radians(x*360/(12+self.modif))-self.offset
                            x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                            if self.rotate_dir == 0:
                                self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                            else:
                                self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5))

                    self.offset += 0.1
                    self.shoot_cooldown = time.time()

            elif self.attack == 1: # Arrow Barrage
                if difficulty != "Paragar":
                    if difficulty == "Ifren":
                        n = 3
                    else:
                        n = 5
                    self.shot_dir = random.randint(0, 3)
                    if time.time()-self.shoot_cooldown >= .3:
                        for _ in range(random.randint(2, n+self.modif)):
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
                else:
                    self.cleared = False
                    if time.time() - self.attack_timer <= .05 and self.pre_attack != 1:
                        self.offset = 0

                    if time.time()-self.shoot_cooldown >= .25:
                        if self.angered:
                            s = 5
                        else:
                            s = 3
                        for x in range(8):
                            if self.skipped[0] and x == self.skipped[1]:
                                self.skipped = [False, None]
                                continue
                            if random.randint(0, 10) == 0:
                                self.skipped = [True, x]
                                continue
                            x = (x*100+50-Obstacle.obstacles["Arrow"][0].get_width()*0.5)+self.offset
                            self.obstacles.append(Obstacle(x, -Obstacle.obstacles["Arrow"][0].get_height(), "Arrow", (x, 100), s))
                        for y in range(6):
                            if self.skipped[0] and y == self.skipped[1]:
                                self.skipped = [False, None]
                                continue
                            if random.randint(0, 10) == 0:
                                self.skipped = [True, y]
                                continue
                            y = (y*100+50-Obstacle.obstacles["Arrow"][0].get_height()*0.5)+self.offset
                            self.obstacles.append(Obstacle(-Obstacle.obstacles["Arrow"][0].get_width(), y, "Arrow", (100, y), s))

                        self.shoot_cooldown = time.time()

                    self.offset += 1
                    if self.offset >= 100:
                        self.offset = 0

            elif self.attack == 2: # Fantastic Pattern
                self.edge = random.randint(0, 1)
                if difficulty == "Paragar":
                    t = .5/((self.modif/4)+1)
                    s = 4
                else:
                    t = 1/((self.modif/4)+1)
                    s = 5
                if difficulty == "Ifren":
                    n = 6
                else:
                    n = 8
                if time.time()-self.shoot_cooldown >= t:
                    if difficulty == "Paragar":
                        self.offset += 0.2
                    else:
                        self.offset = 0
                    if self.edge == 0:
                        for x in range(n):
                            rad = math.radians(x*360/n)+self.offset
                            x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, 1
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), s))
                        for x in range(n):
                            rad = math.radians(x*360/n)-self.offset
                            x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height-14
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), s))
                        for x in range(n):
                            rad = math.radians(x*360/n)+self.offset
                            x, y = 1, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), s))
                        for x in range(n):
                            rad = math.radians(x*360/n)-self.offset
                            x, y = Width-14, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), s))
                    else:
                        for x in range(n):
                            rad = math.radians(x*360/n)+self.offset
                            x, y = 1, 1
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), s))
                        for x in range(n):
                            rad = math.radians(x*360/n)-self.offset
                            x, y = 1, Height-14
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), s))
                        for x in range(n):
                            rad = math.radians(x*360/n)+self.offset
                            x, y = Width-14, 1
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), s))
                        for x in range(n):
                            rad = math.radians(x*360/n)-self.offset
                            x, y = Width-14, Height-14
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), s))
                    
                    self.shoot_cooldown = time.time()

            elif self.attack == 3: # Bouncy Boi
                if time.time() - self.attack_timer <= .05 and self.pre_attack != 3:
                    self.offset = random.uniform(0, math.pi*2)
                    self.rotate_dir = random.randint(0, 1)
                if time.time()-self.shoot_cooldown >= .25:
                    if difficulty != "Paragar":
                        if difficulty == "Ifren":
                            n = 3
                            d = 30
                        else:
                            n = 4
                            d = 50

                        for x in range(n):
                            rad = math.radians(x*360/n)+self.offset
                            x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                            if self.rotate_dir == 0:
                                self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, True))
                            else:
                                self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5, True))
                        self.offset += 0.1+self.modif/d
                    else:
                        for x in range(4):
                            rad = math.radians(x*360/4)+self.offset
                            if self.angered:
                                x, y = Width*0.25-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                            else:
                                x, y = Width*0.33-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                            if self.rotate_dir == 0:
                                self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, True))
                            else:
                                self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5, True))
                        for x in range(4):
                            rad = math.radians(x*360/4)-self.offset
                            if self.angered:
                                x, y = Width*0.75-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                            else:
                                x, y = Width*0.66-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                            if self.rotate_dir == 0:
                                self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, True))
                            else:
                                self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5, True))
                        
                        self.offset += 0.5
                    self.shoot_cooldown = time.time()
                if time.time()-self.shoot2_cooldown >= .5 and self.angered and difficulty == "Paragar":
                    for x in range(12):
                        rad = math.radians(x*360/12)
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        if self.rotate_dir == 0:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5))
                    
                    self.shoot2_cooldown = time.time()

            elif self.attack == 4: # Eagle Eye Shots
                if time.time()-self.shoot_cooldown >= 1/((self.modif/6)+1):
                    # Top
                    x, y = Width*0.5-Obstacle.obstacles["Arrow"][0].get_height()*0.5, -Obstacle.obstacles["Arrow"][0].get_height()
                    self.obstacles.append(Obstacle(x, y, "Arrow", (player.rect.centerx-Obstacle.obstacles["Arrow"][0].get_height()*0.5, player.rect.centery-Obstacle.obstacles["Arrow"][0].get_height()*0.5), 5))

                    # Bottom
                    x, y = Width*0.5-Obstacle.obstacles["Arrow"][0].get_height()*0.5, Height
                    self.obstacles.append(Obstacle(x, y, "Arrow", (player.rect.centerx-Obstacle.obstacles["Arrow"][0].get_height()*0.5, player.rect.centery-Obstacle.obstacles["Arrow"][0].get_height()*0.5), 5))

                    # Left
                    x, y = -Obstacle.obstacles["Arrow"][0].get_height(), Height*0.5-Obstacle.obstacles["Arrow"][0].get_height()*0.5
                    self.obstacles.append(Obstacle(x, y, "Arrow", (player.rect.centerx-Obstacle.obstacles["Arrow"][0].get_height()*0.5, player.rect.centery-Obstacle.obstacles["Arrow"][0].get_height()*0.5), 5))

                    # Right
                    x, y = Width, Height*0.5-Obstacle.obstacles["Arrow"][0].get_height()*0.5
                    self.obstacles.append(Obstacle(x, y, "Arrow", (player.rect.centerx-Obstacle.obstacles["Arrow"][0].get_height()*0.5, player.rect.centery-Obstacle.obstacles["Arrow"][0].get_height()*0.5), 5))

                    # TL Corner
                    x, y = -Obstacle.obstacles["Arrow"][0].get_height(), -Obstacle.obstacles["Arrow"][0].get_height()
                    self.obstacles.append(Obstacle(x, y, "Arrow", (player.rect.centerx-Obstacle.obstacles["Arrow"][0].get_height()*0.5, player.rect.centery-Obstacle.obstacles["Arrow"][0].get_height()*0.5), 5))

                    # BL Corner
                    x, y = -Obstacle.obstacles["Arrow"][0].get_height(), Height
                    self.obstacles.append(Obstacle(x, y, "Arrow", (player.rect.centerx-Obstacle.obstacles["Arrow"][0].get_height()*0.5, player.rect.centery-Obstacle.obstacles["Arrow"][0].get_height()*0.5), 5))

                    # TR Corner
                    x, y = Width, -Obstacle.obstacles["Arrow"][0].get_height()
                    self.obstacles.append(Obstacle(x, y, "Arrow", (player.rect.centerx-Obstacle.obstacles["Arrow"][0].get_height()*0.5, player.rect.centery-Obstacle.obstacles["Arrow"][0].get_height()*0.5), 5))

                    # BR Corner
                    x, y = Width, Height
                    self.obstacles.append(Obstacle(x, y, "Arrow", (player.rect.centerx-Obstacle.obstacles["Arrow"][0].get_height()*0.5, player.rect.centery-Obstacle.obstacles["Arrow"][0].get_height()*0.5), 5))
                    
                    self.shoot_cooldown = time.time()

            elif self.attack == 5: # Random Lethality
                if time.time()-self.shoot_cooldown >= .15/((self.modif/8)+1):
                    while 1:
                        x, y = random.randint(1, Width-1), random.randint(1, Height-1)
                        rect = pygame.Rect(x-150, y-150, 300, 300)
                        if not rect.colliderect(player.rect):
                            break

                    for a in range(12):
                        rad = math.radians(a*360/12)

                        if self.rotate_dir == 0:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5))

                    self.shoot_cooldown = time.time()
        else:
            self.attack = 7

            if self.attack != 7:
                self.mirror = False

            if self.attack == 0: # Concentrated Knives
                if time.time()-self.shoot_cooldown >= .25:
                    for b in range(16+self.modif):
                        rad = math.radians(b*360/(16+self.modif))
                        x, y = (player.rect.centerx-Obstacle.obstacles["Knife"][0].get_height()*0.5)+100*math.sin(rad), (player.rect.centery-Obstacle.obstacles["Knife"][0].get_height()*0.5)+100*math.cos(rad)
                        if b%2 == 0:
                            self.obstacles.append(Obstacle(x, y, "Knife", ((player.rect.centerx-Obstacle.obstacles["Knife"][0].get_height()*0.5)+200*math.sin(rad), (player.rect.centery-Obstacle.obstacles["Knife"][0].get_height()*0.5)+200*math.cos(rad)), 2))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Knife", ((player.rect.centerx-Obstacle.obstacles["Knife"][0].get_height()*0.5), (player.rect.centery-Obstacle.obstacles["Knife"][0].get_height()*0.5)), 2))
                    self.shoot_cooldown = time.time()

            elif self.attack == 1: # Gotta Go Fast
                if time.time() - self.attack_timer <= .05:
                    if self.pre_attack != 1:
                        self.offset = random.uniform(0, math.pi*2)
                        self.rotate_dir = random.randint(0, 1)
                    self.time = 1
                    self.attack_speed = 5
                if time.time()-self.shoot_cooldown >= self.time:
                    print(self.attack_speed)
                    for x in range(48+self.modif):
                        rad = math.radians(x*360/(48+self.modif))-self.offset
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        if self.rotate_dir == 0:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), self.attack_speed))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), self.attack_speed))

                    self.offset += 0.1
                    if self.attack_speed < 12:
                        self.time -= 0.05
                        self.attack_speed += 0.5
                    self.shoot_cooldown = time.time()
                if time.time()-self.shoot_cooldown >= self.time/2 and time.time()-self.shoot_cooldown <= self.time/2+0.02:
                    for x in range(8):
                        x = (x*100+50-Obstacle.obstacles["Arrow"][0].get_width()*0.5)
                        self.obstacles.append(Obstacle(x, -Obstacle.obstacles["Arrow"][0].get_height(), "Arrow", (x, Height), self.attack_speed*2))
                    for y in range(6):
                        y = (y*100+50-Obstacle.obstacles["Arrow"][0].get_height()*0.5)
                        self.obstacles.append(Obstacle(-Obstacle.obstacles["Arrow"][0].get_width(), y, "Arrow", (Width, y), self.attack_speed*2))
                    for x in range(8):
                        x = (x*100+50-Obstacle.obstacles["Arrow"][0].get_width()*0.5)
                        self.obstacles.append(Obstacle(x, Height, "Arrow", (x, 0), self.attack_speed*2))
                    for y in range(6):
                        y = (y*100+50-Obstacle.obstacles["Arrow"][0].get_height()*0.5)
                        self.obstacles.append(Obstacle(Width, y, "Arrow", (0, y), self.attack_speed*2))

            elif self.attack == 2: # Tight Movements
                if time.time()-self.shoot_cooldown >= 2:
                    if time.time()-self.attack_timer >= self.attack_change_cooldown-2:
                        for x in range(32):
                            rad = math.radians(x*360/32)
                            x, y = Width*0.5-Obstacle.obstacles["Knife"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Knife"][0].get_height()*0.5
                            self.obstacles.append(Obstacle(x, y, "Knife", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    for x in range(16):
                        rad = math.radians(x*360/16)+self.offset
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, 1
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                    for x in range(16):
                        rad = math.radians(x*360/16)-self.offset
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height-14
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                    for x in range(16):
                        rad = math.radians(x*360/16)+self.offset
                        x, y = 1, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                    for x in range(16):
                        rad = math.radians(x*360/16)-self.offset
                        x, y = Width-14, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                    for x in range(16):
                        rad = math.radians(x*360/16)+self.offset
                        x, y = 1, 1
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                    for x in range(16):
                        rad = math.radians(x*360/16)-self.offset
                        x, y = 1, Height-14
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                    for x in range(16):
                        rad = math.radians(x*360/16)+self.offset
                        x, y = Width-14, 1
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                    for x in range(16):
                        rad = math.radians(x*360/16)-self.offset
                        x, y = Width-14, Height-14
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                    self.offset -= 0.5
                    self.shoot_cooldown = time.time()

            elif self.attack == 3: # Eagle Spin
                if time.time()-self.shoot_cooldown >= .25:
                    for x in range(48+self.modif):
                        n = x-(48+self.modif)//2
                        if n < 0:
                            rad = math.atan2(player.rect.centery - Height*0.5, player.rect.centerx - Width*0.5)-math.radians(abs(n)*(360/(48+self.modif)))
                        elif n > 0:
                            rad = math.atan2(player.rect.centery - Height*0.5, player.rect.centerx - Width*0.5)+math.radians(n*(360/(48+self.modif)))
                        else:
                            rad = math.atan2(player.rect.centery - Height*0.5, player.rect.centerx - Width*0.5)
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                    self.shoot_cooldown = time.time()
                        
            elif self.attack == 4: # Bouncy Duplication
                if time.time()-self.shoot_cooldown >= .75:
                    for x in range(8+self.modif):
                        n = x-(8+self.modif)//2
                        if n < 0:
                            rad = math.atan2(player.rect.centery - Height*0.5, player.rect.centerx - Width*0.5)-math.radians(abs(n)*(360/(8+self.modif)))
                        elif n > 0:
                            rad = math.atan2(player.rect.centery - Height*0.5, player.rect.centerx - Width*0.5)+math.radians(n*(360/(8+self.modif)))
                        else:
                            rad = math.atan2(player.rect.centery - Height*0.5, player.rect.centerx - Width*0.5)
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, True))
                    self.shoot_cooldown = time.time()

            elif self.attack == 5: # Locked Knives (ran out of ideas)
                if time.time()-self.shoot_cooldown >= .25:
                    for b in range(16+self.modif):
                        rad = math.radians(b*360/(16+self.modif))
                        x, y = (player.rect.centerx-Obstacle.obstacles["Knife"][0].get_height()*0.5)+100*math.sin(rad), (player.rect.centery-Obstacle.obstacles["Knife"][0].get_height()*0.5)+100*math.cos(rad)
                        self.obstacles.append(Obstacle(x, y, "Knife", ((player.rect.centerx-Obstacle.obstacles["Knife"][0].get_height()*0.5)+200*math.sin(rad), (player.rect.centery-Obstacle.obstacles["Knife"][0].get_height()*0.5)+200*math.cos(rad)), 5, True))
                    self.shoot_cooldown = time.time()

            elif self.attack == 6: # Boom (ran out of ideas)
                if time.time() - self.attack_timer <= .05 and self.pre_attack != 6:
                    self.offset = random.uniform(0, math.pi*2)
                    self.rotate_dir = random.randint(0, 1)
                if time.time()-self.shoot_cooldown >= 1:
                    for x in range(64):
                        rad = math.radians(x*360/64)+self.offset
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        if self.rotate_dir == 0:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 1))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 1))
                    self.offset += 1
                    self.shoot_cooldown = time.time()
                if time.time()-self.shoot2_cooldown >= 3:
                    for x in range(32):
                        rad = math.radians(x*360/32)+self.offset
                        x, y = Width*0.5-(Obstacle.obstacles["Fireball"][0].get_width()*2)*0.5, Height*0.5-(Obstacle.obstacles["Fireball"][0].get_height()*2)*0.5
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, size=2))
                    self.shoot2_cooldown = time.time()
                    self.offset += 1
                    self.rotate_dir = abs(self.rotate_dir - 1)

            elif self.attack == 7: # Mirror
                self.mirror = True
                if self.sub_att == [None, None]:
                    self.sub_att[0] = random.randint(0, 2)
                    self.sub_att[1] = random.randint(0, 2)
                if time.time()-self.attack_timer < 0.1:
                    player.spawned = time.time()
                    if player_mirror:
                        player_mirror.spawned = time.time()

                for i, a in enumerate(self.sub_att):
                    if a == 0:
                        if time.time() - self.attack_timer <= .05 and self.pre_attack != 7:
                            self.offset = random.uniform(0, math.pi*2)
                            self.rotate_dir = random.randint(0, 1)
                        if time.time() - self.sub_att_cooldown[i] >= 0.25:
                            for x in range(12+self.modif):
                                rad = math.radians(x*360/(12+self.modif))+self.offset
                                x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                                
                                if i == 0:
                                    x -= Width*0.25
                                else:
                                    x += Width*0.25
                                
                                if self.rotate_dir == 0:
                                    self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                                else:
                                    self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5))
                            for x in range(12+self.modif):
                                rad = math.radians(x*360/(12+self.modif))-self.offset
                                x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                                
                                if i == 0:
                                    x -= Width*0.25
                                else:
                                    x += Width*0.25

                                if self.rotate_dir == 0:
                                    self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                                else:
                                    self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5))

                            self.offset += 0.1
                            self.sub_att_cooldown[i] = time.time()

                    elif a == 1:
                        if time.time()-self.sub_att_cooldown[i] >= .25/((self.modif/8)+1):
                            while 1:
                                x, y = random.randint(1, Width*0.5-1), random.randint(1, Height*0.5-1)
                                if i == 1:
                                    x += Width*0.5; y += Height*0.5

                                try:
                                    rect = pygame.Rect(x-150, y-150, 300, 300)
                                    if i == 0:
                                        if player.x < Width*0.5:
                                            if not rect.colliderect(player.rect):
                                                break
                                        else:
                                            if not rect.colliderect(player_mirror.rect):
                                                break
                                    else:
                                        if player.x > Width*0.5:
                                            if not rect.colliderect(player.rect):
                                                break
                                        else:
                                            if not rect.colliderect(player_mirror.rect):
                                                break
                                except AttributeError:
                                    break

                            for a in range(12):
                                rad = math.radians(a*360/12)

                                if self.rotate_dir == 0:
                                    self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                                else:
                                    self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5))
                            self.sub_att_cooldown[i] = time.time()

                    elif a == 2:
                        if time.time()-self.sub_att_cooldown[i] >= .75:
                            for z in range(2):
                                if z == 0:
                                    y = 0
                                else:
                                    y = Height-Obstacle.obstacles["Fireball"][0].get_height()
                                for x in range(24+self.modif):
                                    rad = math.radians(x*360/(24+self.modif))
                                    x = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5
                                    if i == 0:
                                        x -= Width*0.25
                                    else:
                                        x += Width*0.25

                                    self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5))
                            self.sub_att_cooldown[i] = time.time()

            elif self.attack == 8: # Duplicated Arrows
                if time.time()-self.shoot_cooldown >= .2:
                    self.obstacles.append(Obstacle(0, -Obstacle.obstacles["Arrow"][0].get_height(), "Arrow", (0, Height), 2))
                    self.obstacles.append(Obstacle(-Obstacle.obstacles["Arrow"][0].get_width(), Height-Obstacle.obstacles["Arrow"][0].get_height(), "Arrow", (Width, Height-Obstacle.obstacles["Arrow"][0].get_height()), 2))
                    self.obstacles.append(Obstacle(Width-Obstacle.obstacles["Arrow"][0].get_height(), Height-Obstacle.obstacles["Arrow"][0].get_height(), "Arrow", (Width-Obstacle.obstacles["Arrow"][0].get_height(), 0), 2))
                    self.obstacles.append(Obstacle(Width, 0, "Arrow", (0, 0), 2))
                
                    self.shoot_cooldown = time.time()

            elif self.attack == 9: # Upgrades Bouncy Boi
                if time.time() - self.attack_timer <= .05 and self.pre_attack != 2:
                    self.offset = random.uniform(0, math.pi*2)
                    self.rotate_dir = random.randint(0, 1)
                if time.time()-self.shoot_cooldown >= .35:
                    for x in range(8):
                        rad = math.radians(x*360/8)+self.offset
                        x, y = Width*0.25-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        if self.rotate_dir == 0:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, True))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5, True))
                    for x in range(8):
                        rad = math.radians(x*360/8)-self.offset
                        x, y = Width*0.75-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        if self.rotate_dir == 0:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, True))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5, True))
                    
                    for x in range(16):
                        rad = math.radians(x*360/16)
                        x, y = Width*0.5-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height*0.5-Obstacle.obstacles["Fireball"][0].get_height()*0.5
                        if self.angered:
                            bounce = True
                        else:
                            bounce = False
                        if self.rotate_dir == 0:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, bounce))
                        else:
                            self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.sin(rad), y+100*math.cos(rad)), 5, bounce))
                    
                    self.shoot_cooldown = time.time()
                    self.offset += 1
            
                    
        for obs in self.obstacles:
            if self.attack == 1 and difficulty == "Paragar":
                if obs.x >= Width-1:
                    obs.x = self.offset-60
                if obs.y >= Height-1:
                    obs.y = self.offset-60
            
            elif self.attack == 4 and difficulty == "Paragar" and not obs in self.collided_obs and obs.obs_type == "Arrow":
                main_rect = pygame.Rect(obs.rect.topleft.x, obs.rect.topleft.y, obs.rect.size[0], obs.rect.size[1])
                list_rect = [pygame.Rect(_obs.rect.topleft.x, _obs.rect.topleft.y, _obs.rect.size[0], _obs.rect.size[1]) for _obs in self.obstacles if _obs != obs and not _obs in self.collided_obs]
                if main_rect.collidelist(list_rect) != -1:
                    self.collided_obs.append(obs)
                    self.offset = random.uniform(0, math.pi*2)
                    for x in range(3):
                        rad = math.radians(x*360/(3))+self.offset
                        self.obstacles.append(Obstacle(obs.rect.center[0], obs.rect.center[1], "Fireball", (obs.rect.center[0]+100*math.cos(rad), obs.rect.center[1]+100*math.sin(rad)), 3))
                    break

            elif self.attack == 4 and difficulty == "Rahenga":
                if obs.flipped:
                    self.obstacles.remove(obs)
                    for x in range(3):
                        x -= 1
                        if x < 0:
                            rad = math.atan2(Height*0.5 - obs.rect.center.y, Width*0.5 - obs.rect.center.x)-math.radians(abs(x)*30)
                        elif x > 0:
                            rad = math.atan2(Height*0.5 - obs.rect.center.y, Width*0.5 - obs.rect.center.x)+math.radians(x*30)
                        else:
                            rad = math.atan2(Height*0.5 - obs.rect.center.y, Width*0.5 - obs.rect.center.x)
                        x, y = obs.x, obs.y
                        self.obstacles.append(Obstacle(x, y, "Fireball", (x+100*math.cos(rad), y+100*math.sin(rad)), 5, False, True))
                if obs.offscreen_disable:
                    if not (obs.x+obs.rect.size[0] < 0 or obs.x > Width or obs.y+obs.rect.size[1] < 0 or obs.y > Height):
                        obs.offscreen_disable = False

            elif self.attack == 5 and difficulty == "Rahenga":
                if obs.flipped and obs.flipped_times < 2:
                    obs.flipped = False
                    obs.flipped_dir = [False, False]

            elif self.attack == 8 and obs.obs_type == "Arrow":
                if random.randint(0, 500) == 1:
                    if obs.end_v == pygame.Vector2(0, Height) or obs.end_v == pygame.Vector2(Width, Height-Obstacle.obstacles["Arrow"][0].get_height()) or obs.end_v == pygame.Vector2(Width-Obstacle.obstacles["Arrow"][0].get_height(), 0) or obs.end_v == pygame.Vector2(0, 0):
                        self.obstacles.remove(obs)
                        for x in range(3+self.modif//2):
                            n = x-(3+self.modif//2)//2
                            if n < 0:
                                rad = math.atan2(player.rect.centery - obs.rect.center.y, player.rect.centerx - obs.rect.center.x)-math.radians(abs(n)*(90/(3+self.modif//2)))
                            elif n > 0:
                                rad = math.atan2(player.rect.centery - obs.rect.center.y, player.rect.centerx - obs.rect.center.x)+math.radians(n*(90/(3+self.modif//2)))
                            else:
                                rad = math.atan2(player.rect.centery - obs.rect.center.y, player.rect.centerx - obs.rect.center.x)
                                
                            x, y = obs.x, obs.y
                            self.obstacles.append(Obstacle(x, y, "Arrow", (x+100*math.cos(rad), y+100*math.sin(rad)), 3))

class Obstacle:
    obstacles = {
        "Fireball": [pygame.image.load(os.path.join("assets", "fireball.png")), pygame.image.load(os.path.join("assets", "fireball slowmo.png"))],
        "Arrow": [pygame.image.load(os.path.join("assets", "arrow.png")), pygame.image.load(os.path.join("assets", "arrow slowmo.png"))],
        "Knife": [pygame.image.load(os.path.join("assets", "knife.png")), pygame.image.load(os.path.join("assets", "knife slowmo.png"))]
    }
    def __init__(self, x, y, obs_type, end_loc, speed, flip = False, offscreen_disable = False, size=1):
        self.x = x
        self.y = y
        self.obs_type = obs_type
        if time.time()-player.p_slowmo_timer >= 3:
            self.img = pygame.transform.scale(self.obstacles[obs_type][0], (self.obstacles[obs_type][0].get_width()*size, self.obstacles[obs_type][0].get_height()*size))
            self._img = pygame.transform.scale(self.obstacles[obs_type][0], (self.obstacles[obs_type][0].get_width()*size, self.obstacles[obs_type][0].get_height()*size))
        else:
            self.img = pygame.transform.scale(self.obstacles[obs_type][1], (self.obstacles[obs_type][1].get_width()*size, self.obstacles[obs_type][1].get_height()*size))
            self._img = pygame.transform.scale(self.obstacles[obs_type][1], (self.obstacles[obs_type][1].get_width()*size, self.obstacles[obs_type][1].get_height()*size))
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
        self.flipped_times = 0

        self.offscreen_disable = offscreen_disable

        self.rect = OBB((self.x+self.img.get_width()*0.5, self.y+self.img.get_height()*0.5), self.img.get_size(), -self.rotation)

    def render(self):
        win.blit(self.img, (self.x, self.y))

    def move(self):
        vel = (self.end_v-self.start_v).normalize()*self.speed
        if self.flip_dir[0]:
            vel.x *= -1
        if self.flip_dir[1]:
            vel.y *= -1

        self.x += vel.x*dt; self.y += vel.y*dt
        self.rect.center.x, self.rect.center.y = self.x+self.img.get_width()*0.5, self.y+self.img.get_height()*0.5

    def off_screen(self, obs_list):
        if (self.x+self.rect.size[0] < 0 or self.x > Width or self.y+self.rect.size[1] < 0 or self.y > Height) and not self.offscreen_disable:
            if self.flip and not self.flipped:
                self.flipped = True
                self.flipped_times += 1
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

player = Player(Width*0.5-player_img.get_width()*0.5, Height*0.5-player_img.get_height()*0.5)
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
    score_data = {"Ifren": [0, 0], "Jahanam": [0, 0], "Paragar": [0, 0], "Rahenga": [0, 0]}
    with open("score.json", "w") as f:
        json.dump(score_data, f, indent=4)

a_c = [128, "+"]
last_call = time.time()

menu_open = True
paused = False
difficulty = "Jahanam"

try:
    pygame.mixer.music.load(os.path.join("assets", "Into Jahanam.ogg"))
except:
    pass

def FPS_ind(last_time):
    return (time.time() - last_time) * 60, time.time()
last_time = time.time()

def main_menu():
    global player, attack, angered_text, text_appear, a_c, last_call, last_time, menu_open, difficulty

    title_font = pygame.font.Font("assets/game-font.ttf", 86)

    title = title_font.render(f"Bullets of {difficulty}", 1, (255, 255, 255))
    x = "Easy" if difficulty == "Ifren" else "Normal" if difficulty == "Jahanam" else "Hard" if difficulty == "Paragar" else "Hellfire"
    difficulty_text = font.render(x, 1, (255, 255, 255))
    texts = [font.render("Press Space/Enter to start", 1, (255, 255, 255)), font.render("Press W & S to change difficulty", 1, (255, 255, 255)), font.render("Press C to view controls", 1, (255, 255, 255))]
    hscore_text = font.render(f"High Score: {score_data[difficulty][0]}", 1, (255, 255, 255))
    lscore_text = font.render(f"Last Score: {score_data[difficulty][1]}", 1, (255, 255, 255))

    def controls():
        surf = pygame.Surface(win.get_size())
        surf.fill(0)
        surf.set_alpha(220)

        texts = [font.render("Movement: WASD/Arrow Keys", 1, (255, 255, 255)), font.render("Slow Down Player: Space/Z", 1, (255, 255, 255)), font.render("Slow Down Time: LShift/X", 1, (255, 255, 255))]
        win.blit(surf, (0, 0))
        for x, text in enumerate(texts):
            x -= 1
            win.blit(text, (Width*0.5-text.get_width()*0.5, Height*0.5-text.get_height()*0.5+x*50))
        pygame.display.flip()

        while 1:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit(); sys.exit()
                if event.type == KEYDOWN:
                    return

            pygame.display.set_caption(f"Bullets of {difficulty} | FPS: {int(clock.get_fps())}")
            pygame.display.flip()
    
    while 1:
        clock.tick(60)
        if difficulty == "Ifren":
            win.fill((0, 0, 0))
        elif difficulty == "Jahanam":
            win.fill((150, 0, 0))
        else:
            win.fill((200, 0, 0))

        win.blit(title, (Width*0.5-title.get_width()*0.5, 20))
        win.blit(difficulty_text, (Width*0.5-difficulty_text.get_width()*0.5, 110))
        for x, text in enumerate(texts):
            x -= 1
            win.blit(text, (Width*0.5-text.get_width()*0.5, Height*0.5-text.get_height()*0.5+x*50))
        win.blit(hscore_text, (50, Height-20-hscore_text.get_height()))
        win.blit(lscore_text, (Width-50-lscore_text.get_width(), Height-20-lscore_text.get_height()))
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_SPACE or event.key == K_KP_ENTER or event.key == K_RETURN:
                    player = Player(384, 284)
                    attack = Attack()

                    angered_text.set_alpha(0)
                    text_appear = [False, 0]

                    a_c = [128, "+"]
                    last_call = time.time()
                    last_time = time.time()

                    menu_open = False
                    return
                if event.key == K_w or event.key == K_UP:
                    if difficulty == "Ifren":
                        difficulty = "Jahanam"
                        difficulty_text = font.render("Normal", 1, (255, 255, 255))
                    elif difficulty == "Jahanam":
                        difficulty = "Paragar"
                        difficulty_text = font.render("Hard", 1, (255, 255, 255))
                    elif difficulty == "Paragar":
                        if score_data["Paragar"][0] >= 500:
                            difficulty = "Rahenga"
                            difficulty_text = font.render("Hellfire", 1, (255, 255, 255))
                        else:
                            difficulty = "Ifren"
                            difficulty_text = font.render("Easy", 1, (255, 255, 255))
                    else:
                        difficulty = "Ifren"
                        difficulty_text = font.render("Easy", 1, (255, 255, 255))

                    title = title_font.render(f"Bullets of {difficulty}", 1, (255, 255, 255))
                    hscore_text = font.render(f"High Score: {score_data[difficulty][0]}", 1, (255, 255, 255))
                    lscore_text = font.render(f"Last Score: {score_data[difficulty][1]}", 1, (255, 255, 255))
                if event.key == K_s or event.key == K_DOWN:
                    if difficulty == "Rahenga":
                        difficulty = "Paragar"
                        difficulty_text = font.render("Hard", 1, (255, 255, 255))
                    elif difficulty == "Paragar":
                        difficulty = "Jahanam"
                        difficulty_text = font.render("Normal", 1, (255, 255, 255))
                    elif difficulty == "Jahanam":
                        difficulty = "Ifren"
                        difficulty_text = font.render("Easy", 1, (255, 255, 255))
                    else:
                        if score_data["Paragar"][0] >= 500:
                            difficulty = "Rahenga"
                            difficulty_text = font.render("Hellfire", 1, (255, 255, 255))
                        else:
                            difficulty = "Paragar"
                            difficulty_text = font.render("Hard", 1, (255, 255, 255))

                    title = title_font.render(f"Bullets of {difficulty}", 1, (255, 255, 255))
                    hscore_text = font.render(f"High Score: {score_data[difficulty][0]}", 1, (255, 255, 255))
                    lscore_text = font.render(f"Last Score: {score_data[difficulty][1]}", 1, (255, 255, 255))
                if event.key == K_c:
                    controls()

        pygame.display.set_caption(f"Bullets of {difficulty} | FPS: {int(clock.get_fps())}")
        pygame.display.flip()

def pause():
    global paused, menu_open, last_call, last_time, dt

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
        time.time()-attack.shoot2_cooldown if attack.shoot2_cooldown else time.time(),
        time.time()-attack.sub_att_cooldown[0] if attack.sub_att_cooldown[0] else time.time(),
        time.time()-attack.sub_att_cooldown[1] if attack.sub_att_cooldown[1] else time.time(),
        time.time()-last_call,
        time.time()-last_time
    ]
    i = 0
    if player_mirror:
        timers.insert(1, time.time()-player_mirror.spawned)
        i += 1

    while 1:
        # fix timers
        player.spawned = time.time()-timers[0]
        if player_mirror:
            player_mirror.spawned = time.time()-timers[1]
        player.blink[0] = time.time()-timers[1+i]
        player.slowmo_cooldown = time.time()-timers[2+i]
        player.slowmo_timer = time.time()-timers[3+i]
        player.p_slowmo_cooldown = time.time()-timers[4+i]
        player.p_slowmo_timer = time.time()-timers[5+i]
        attack.attack_timer = time.time()-timers[6+i]
        attack.angered_timer = time.time()-timers[7+i]
        attack.endlesstorture_timer = time.time()-timers[8+i]
        attack.shoot_cooldown = time.time()-timers[9+i]
        attack.shoot2_cooldown = time.time()-timers[10+i]
        attack.sub_att_cooldown[0] = time.time()-timers[11+i]
        attack.sub_att_cooldown[1] = time.time()-timers[12+i]
        last_call = time.time()-timers[13+i]
        last_time = time.time()-timers[14+i]
        

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    menu_open = True
                    if score_data[difficulty][0] < player.score:
                        score_data[0] = player.score
                    score_data[difficulty][1] = player.score
                    with open("score.json", "w") as f:
                        json.dump(score_data, f, indent=4)
                paused = False
                try:
                    pygame.mixer.music.unpause()
                except:
                    pass
                return
dt = 0

circle_size = 200
while 1:
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

        if difficulty == "Rahenga":
            text = font.render(str(abs(round(time.time()-attack.angered_timer)-60)), True, (255, 255, 255))
        else:
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
    dt, last_time = FPS_ind(last_time)    

    score_text = font.render(str(player.score), True, (255,255,255))
    win.blit(score_text, (Width*0.5-score_text.get_width()*0.5, 5))

    if attack.mirror:
        pygame.draw.line(win, (255,255,255), (Width*0.5-2.5, 0), (Width*0.5-2.5, Height), 5)
        if not player_mirror:
            player_mirror = Player(Width-player.x-player_img.get_width(), player.y, True)
    else:
        player_mirror = None


    player.render()
    if player_mirror:
        player_mirror.render()

    # Attack Spawn Indicator
    if time.time()-attack.attack_timer >= attack.attack_change_cooldown-1 and attack.pending_attack != attack.attack:
        circle_size -= 3*dt
        if attack.pending_attack == 0:
            if difficulty == "Rahenga":
                for b in range(16+attack.modif):
                    rad = math.radians(b*360/(16+attack.modif))
                    pygame.draw.circle(win, (255,255,255), (player.rect.centerx+100*math.sin(rad), player.rect.centery+100*math.cos(rad)), circle_size, 5)
            else:
                pygame.draw.circle(win, (255,255,255), (Width*0.5, Height*0.5), circle_size, 5)
        elif attack.pending_attack == 1:
            if difficulty == "Rahenga":
                for x in range(8):
                    pygame.draw.circle(win, (255,255,255), (x*100+50-Obstacle.obstacles["Fireball"][0].get_width()*0.5, 0), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (x*100+50-Obstacle.obstacles["Fireball"][0].get_width()*0.5, Height), circle_size, 5)
                for y in range(6):
                    pygame.draw.circle(win, (255,255,255), (0, y*100+50-Obstacle.obstacles["Fireball"][0].get_height()*0.5), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (Width, y*100+50-Obstacle.obstacles["Fireball"][0].get_height()*0.5), circle_size, 5)
                pygame.draw.circle(win, (255,255,255), (Width*0.5, Height*0.5), circle_size, 5)
            elif difficulty == "Paragar":
                for x in range(32):
                    pygame.draw.circle(win, (255,255,255), (x*50, 0), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (x*50, Height), circle_size, 5)
                for y in range(24):
                    pygame.draw.circle(win, (255,255,255), (0, y*50), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (Width, y*50), circle_size, 5)
            else:
                for x in range(16):
                    pygame.draw.circle(win, (255,255,255), (x*50, 0), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (x*50, Height), circle_size, 5)
                for y in range(12):
                    pygame.draw.circle(win, (255,255,255), (0, y*50), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (Width, y*50), circle_size, 5)
        elif attack.pending_attack == 2:
            pygame.draw.circle(win, (255,255,255), (0, 0), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width, 0), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (0, Height), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width, Height), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width*0.5, 0), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (0, Height*0.5), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width*0.5, Height), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width, Height*0.5), circle_size, 5)
        elif attack.pending_attack == 3:
            if difficulty == "Rahenga":
                pygame.draw.circle(win, (255,255,255), (Width*0.5, Height*0.5), circle_size, 5)
            elif difficulty == "Paragar":
                if attack.angered:
                    pygame.draw.circle(win, (255,255,255), (Width*0.25, Height*0.5), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (Width*0.5, Height*0.5), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (Width*0.75, Height*0.5), circle_size, 5)
                else:
                    pygame.draw.circle(win, (255,255,255), (Width*0.33, Height*0.5), circle_size, 5)
                    pygame.draw.circle(win, (255,255,255), (Width*0.66, Height*0.5), circle_size, 5)
            else:
                pygame.draw.circle(win, (255,255,255), (Width*0.5, Height*0.5), circle_size, 5)
        elif attack.pending_attack == 4:
            if difficulty == "Rahenga":
                pygame.draw.circle(win, (255,255,255), (Width*0.5, Height*0.5), circle_size, 5)
            else:
                pygame.draw.circle(win, (255,255,255), (0, 0), circle_size, 5)
                pygame.draw.circle(win, (255,255,255), (Width, 0), circle_size, 5)
                pygame.draw.circle(win, (255,255,255), (0, Height), circle_size, 5)
                pygame.draw.circle(win, (255,255,255), (Width, Height), circle_size, 5)
                pygame.draw.circle(win, (255,255,255), (Width*0.5, 0), circle_size, 5)
                pygame.draw.circle(win, (255,255,255), (0, Height*0.5), circle_size, 5)
                pygame.draw.circle(win, (255,255,255), (Width*0.5, Height), circle_size, 5)
                pygame.draw.circle(win, (255,255,255), (Width, Height*0.5), circle_size, 5)
        elif attack.pending_attack == 5:
            if difficulty == "Rahenga":
                for b in range(16+attack.modif):
                    rad = math.radians(b*360/(16+attack.modif))
                    pygame.draw.circle(win, (255,255,255), (player.rect.centerx+100*math.sin(rad), player.rect.centery+100*math.cos(rad)), circle_size, 5)
        elif attack.pending_attack == 6:
            pygame.draw.circle(win, (255,255,255), (Width*0.5, Height*0.5), circle_size, 5)
        elif attack.pending_attack == 8:
            pygame.draw.circle(win, (255,255,255), (0, 0), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width, 0), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (0, Height), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width, Height), circle_size, 5)
        elif attack.pending_attack == 9:
            pygame.draw.circle(win, (255,255,255), (Width*0.25, Height*0.5), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width*0.5, Height*0.5), circle_size, 5)
            pygame.draw.circle(win, (255,255,255), (Width*0.75, Height*0.5), circle_size, 5)
    else:
        circle_size = 200


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
            if event.key == K_SPACE or event.key == K_z:
                if time.time()-player.slowmo_cooldown >= 1 and player.speed == 5:
                    if player_mirror:
                        player_mirror.speed = 2
                        player_mirror.img = player_slowmo_img
                    player.speed = 2
                    player.slowmo_timer = time.time()
                    player.img = player_slowmo_img
            if len(attack.obstacles) > 0:
                if event.key == K_LSHIFT or event.key == K_x:
                    if time.time()-player.p_slowmo_cooldown >= 5 and attack.obstacles[0].speed == attack.obstacles[0].orig_speed and time.time()-player.p_slowmo_timer >= 3:
                        player.p_slowmo_timer = time.time()
    
            if event.key == K_ESCAPE:
                paused = True

    if player.speed == 2 and time.time()-player.slowmo_timer >= 3:
        if player_mirror:
            player_mirror.speed = 5
            player_mirror.img = player_img
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
                if score_data[difficulty][0] < player.score:
                    score_data[difficulty][0] = player.score
                score_data[difficulty][1] = player.score
                with open("score.json", "w") as f:
                    json.dump(score_data, f, indent=4)
                
                menu_open = True
        if obs.rect.colliderect(player.graze_rect):
            score_modif += 1
        
        if player_mirror:
            if obs.rect.colliderect(player_mirror.rect):
                if time.time() - player.spawned >= 1.5:
                    if score_data[difficulty][0] < player.score:
                        score_data[difficulty][0] = player.score
                    score_data[difficulty][1] = player.score
                    with open("score.json", "w") as f:
                        json.dump(score_data, f, indent=4)
                    
                    menu_open = True
            if obs.rect.colliderect(player_mirror.graze_rect):
                score_modif += 1
            
    player.move()
    if player_mirror:
        player_mirror.move()
    if angered_text.get_alpha() == 0:
        attack.attacks()
        if attack.angered:
            score_modif += 1
    
    if time.time() - player.spawned < 1.5:
        score_modif = 0
        player.score = 0

    if time.time()-last_call >= .1:
        player.score += 1*score_modif
        last_call = time.time()

    pygame.display.set_caption(f"Bullets of {difficulty} | FPS: {int(clock.get_fps())}")
    pygame.display.flip()
