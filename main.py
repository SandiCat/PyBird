import pygame
from pygame.locals import *
from random import randint
from time import clock
from os.path import isfile
import json

blue = pygame.Color(0, 0, 200)
red = pygame.Color(200, 0, 0)
black = pygame.Color(0, 0, 0)
white = pygame.Color(255, 255, 255)

##OBJECT:
#update(events)
#draw()
#bounding_box: BoundingBox

game = None
my_font = None
top_score = None
settings = None


class Game():
    def __init__(self, starting_speed, acceleration, gravity_acc, jump_mag, pipe_width, opening_height, spacing):
        self.fps_clock = pygame.time.Clock()
        self.width = 640
        self.height = 480
        self.window = pygame.display.set_mode((self.width, self.height))
        self.objects = []
        self.time = clock()
        self.speed = starting_speed
        self.acceleration = acceleration
        self.score = 0

        floor_height = 30
        floor = RectangleObj(black, BoundingBox(0, self.height - floor_height, self.width, floor_height + 100))
        self.add_object(floor)
        pipe_manager = PipeManager(pipe_width, opening_height, spacing)
        self.add_object(pipe_manager)
        self.add_object(Bird(pipe_manager, floor, gravity_acc, jump_mag))

    def add_object(self, x):
        self.objects.append(x)

    def remove_object(self, x):
        self.objects.remove(x)

    def update(self):
        events = pygame.event.get()
        for event in events:
            if  or (event.type == KEYDOWN and event.key == K_ESCAPE):
                score_file = open("score", "w")
                score_file.write(str(max(top_score, self.score)))
                score_file.close()
                pygame.quit()

        for x in self.objects:
            x.update(events)

        pygame.display.update()
        self.fps_clock.tick(30)

        if self.time + 1 < clock():
            self.time = clock()
            self.speed *= self.acceleration

    def draw(self, color):
        self.window.fill(color)
        for x in self.objects:
            x.draw()

        label = my_font.render("{} {}".format(self.score, top_score), 50, (0, 255, 0))
        self.window.blit(label, (self.width / 2 - 50, 10))


def new_game():
    global top_score
    if game and game.score > top_score:
        top_score = game.score

    global game
    game = Game(acceleration=settings["game_acceleration"],
                starting_speed=settings["game_starting_speed"],
                gravity_acc=settings["gravity_acceleration"],
                jump_mag=settings["jump_magnitude"],
                pipe_width=settings["pipe_width"],
                opening_height=settings["pipe_opening_height"],
                spacing=settings["pipe_spacing"])


class BoundingBox():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def intersects(self, other_box):
        #this wont detect when other_box is completely contained by self, which doesn't matter for this game
        point_within_box = lambda x, y, box: box.x <= x <= box.x + box.width and box.y <= y <= box.y + box.height
        x1, y1 = self.x, self.y
        x2, y2 = self.x + self.width, self.y
        x3, y3 = self.x, self.y + self.height
        x4, y4 = self.x + self.width, self.y + self.height
        return point_within_box(x1, y1, other_box) or\
               point_within_box(x2, y2, other_box) or\
               point_within_box(x3, y3, other_box) or\
               point_within_box(x4, y4, other_box)


class RectangleObj():
    def __init__(self, color, bounding_box):
        self.bounding_box = bounding_box
        self.color = color

    def draw(self):
        pygame.draw.rect(game.window, self.color,
                         (self.bounding_box.x, self.bounding_box.y, self.bounding_box.width, self.bounding_box.height))

    def update(self, events):
        pass


class Pipe():
    def __init__(self, opening_pos, x, width, opening_height):
        self.x = x
        self.opening_pos = opening_pos
        self.width = width
        self.opening_height = opening_height
        inf = 1000
        self.top = RectangleObj(black, BoundingBox(self.x, -inf, self.width, inf + self.opening_pos))
        self.bottom = RectangleObj\
            (black, BoundingBox(self.x, self.opening_height + self.opening_pos, self.width, inf))

    def update_top_bottom(self):
        self.top.bounding_box.x = self.x
        self.bottom.bounding_box.x = self.x

    def draw(self):
        self.top.draw()
        self.bottom.draw()

    def update(self):
        self.update_top_bottom()


class PipeManager():
    def __init__(self, pipe_width, pipe_opening_height, spacing):
        self.spacing = spacing
        self.pipe_width = pipe_width
        self.pipe_opening_height = pipe_opening_height
        self.pipes = []

    def generate_pipe(self):
        last_x = self.pipes[-1].x + self.pipe_width if self.pipes else game.width - self.spacing - self.pipe_width
        self.pipes.append\
            (Pipe(randint(10, game.height - self.pipe_opening_height - 30),
                  last_x + self.pipe_width + self.spacing,
                  self.pipe_width,
                  self.pipe_opening_height))

    def draw(self):
        for pipe in self.pipes:
            pipe.draw()

    def update(self, events):
        last_x_back = self.pipes[-1].x + self.pipe_width if self.pipes else 0
        if game.width - last_x_back >= self.spacing:
            self.generate_pipe()

        if self.pipes[0].x + self.pipe_width <= 0:
            self.pipes.pop(0)
            game.score += 1

        for pipe in self.pipes:
            pipe.x -= game.speed
            pipe.update()


class Bird():
    def __init__(self, pipe_manager, floor, gravity_acceleration, jump_magnitude):
        self.graphics = RectangleObj(black, BoundingBox(10, 100, 30, 30))
        self.vertical_speed = 0
        self.acceleration = gravity_acceleration
        self.jump_magnitude = jump_magnitude
        self.pipe_manager = pipe_manager
        self.floor = floor

    def draw(self):
        self.graphics.draw()

    def update(self, events):
        self.vertical_speed += self.acceleration
        self.graphics.bounding_box.y += self.vertical_speed

        for event in events:
            if event.type == KEYDOWN and event.key == K_SPACE:
                self.vertical_speed = -self.jump_magnitude

        collidable = [self.floor]
        for pipe in self.pipe_manager.pipes:
            collidable.append(pipe.top)
            collidable.append(pipe.bottom)

        for obj in collidable:
            if obj is not self and self.graphics.bounding_box.intersects(obj.bounding_box):
                new_game()
                return

    def __update(self, events):
        for event in events:
            if event.type == KEYDOWN:
                speed = 10
                if event.key == K_DOWN:
                    self.graphics.bounding_box.y += speed
                elif event.key == K_UP:
                    self.graphics.bounding_box.y -= speed
                elif event.key == K_RIGHT:
                    self.graphics.bounding_box.x += speed
                elif event.key == K_LEFT:
                    self.graphics.bounding_box.x -= speed

        collidable = [self.floor]
        for pipe in self.pipe_manager.pipes:
            collidable.append(pipe.top)
            collidable.append(pipe.bottom)

        for obj in collidable:
            if obj is not self and self.graphics.bounding_box.intersects(obj.bounding_box):
                new_game()
                return


def main():
    pygame.init()
    pygame.display.set_caption("Flappy bird clone")
    global my_font
    my_font = pygame.font.SysFont("monospace", 50)

    global top_score
    score_file_name = "score"
    if isfile(score_file_name):
        score_file = open(score_file_name, "r")
        top_score = int(score_file.read())
        score_file.close()
    else:
        top_score = 0

    global settings
    settings_file_name = "settings"
    if isfile(settings_file_name):
        settings = json.load(open(settings_file_name, "r"))
    else:
        settings = {"game_starting_speed": 2,
                    "game_acceleration": 1.1,
                    "gravity_acceleration": 2,
                    "jump_magnitude": 20,
                    "pipe_width": 70,
                    "pipe_opening_height": 150,
                    "pipe_spacing": 100}
        json.dump(settings, open(settings_file_name, "w"), indent=0)

    new_game()

    while True:
        game.draw(white)
        game.update()

main()
