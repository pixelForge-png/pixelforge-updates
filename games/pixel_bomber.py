import time
import random
from helpers.buzzer_sounds import sound
from helpers.oled_functions import (
    BLACK, WHITE, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA,
    ORANGE, PURPLE, HEALTH_GREEN, DANGER_RED, SHIELD_BLUE, SPACE_BLACK,
    ENEMY_BULLET, PLAYER_BULLET, LASER_COLOR, FREEZE_COLOR, BOMB_COLOR,
    GAME_PALETTE,
    center_text_x, draw_tiny_text, draw_color_sprite, draw_sprite, show_display,
    joystick_direction, joystick_pressed, wait_for_joystick_release,
    make_level, update_enimies, upgrades, transition, make_boss, update_boss,
    boss_attack, draw_special_icon, make_aimed_enemy_bullet, bullet_screen_x, bullet_screen_y
)
#functions area









def main():
  
