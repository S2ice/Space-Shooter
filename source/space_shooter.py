import sys
from time import sleep

import pygame

from setting.settings import Settings
from util.scoreboard import Scoreboard
from util.game_stats import GameStats
from widgets.button import Button
from player.ship import Ship
from player.cosmetic.bullet import Bullet
from enemies.alien import Alien

"""Основной класс игрового окна"""
class SpaceShooter:
    """Инициализируем игру и создаем игровые ресурсы"""
    def __init__(self):
        pygame.init() 
        self.settings = Settings()    # Загружаем настройки игры 

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)    # Создаю полноэкранное окно 
        """Обновляю настройки ширины/высоты в соотвествии с экраном"""
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Space Shooter")

        """Инициализация статистики и игрового табла"""
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)    

        """Создаю корабль, группы пуль и пришельцев"""
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()    # Создание прямоугольной группы прешельцев

        self.play_button = Button(self, "Play")    # Создание кнопки "Играть"

    """Запуск основного цикла игры."""
    def run_game(self):
        while True:
            self._check_events()    # Обработка событий

            if self.stats.game_active:
                self.ship.update()    # Обновление позиции корабля
                self._update_bullets()    # Обновление позиции пуль
                self._update_aliens()    # Обновление позиции пришельцев

            self._update_screen() # Перерисовка экрана

    """Обработка нажатий клавиш и событий мыши."""
    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)
    
    """Запускаю новую игру при нажатии кнопки Play."""
    def _check_play_button(self, mouse_pos):
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            self.settings.initialize_dynamic_settings()    # Сброс игровых настроек

            """Сброс игровой статистики"""
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            """Очистка списков пришельцев и пуль"""
            self.aliens.empty()
            self.bullets.empty()

            """Создание новой группы пришельцев и размещение корабля по центру"""
            self._create_fleet()
            self.ship.center_ship()

            pygame.mouse.set_visible(False)    # Скрываем указатель мыши

     """Обработка нажатий клавиш."""
    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()    # Выход по клавише Q
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()    # Выстрел по пробелу

     """Обработка нажатий мыши."""
    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    """Создание новой пули и включение ее в группу"""
    def _fire_bullet(self):
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    """Обновляет позиции пуль и уничтожает старые пули."""
    def _update_bullets(self):
        self.bullets.update()
    """Удаление пуль, вышедших за край экрана."""
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            self.stats.level += 1
            self.sb.prep_level()

    def _update_aliens(self):
        self._check_fleet_edges()
        self.aliens.update()

        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        self._check_aliens_bottom()

    def _check_aliens_bottom(self):
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _ship_hit(self):
        if self.stats.ships_left > 0:
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            self.aliens.empty()
            self.bullets.empty()

            self._create_fleet()
            self.ship.center_ship()

            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _create_fleet(self):
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height -
                             (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        self.sb.show_score()

        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()


if __name__ == '__main__':
    main_win = SpaceShooter()
    main_win.run_game()
