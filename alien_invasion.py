import sys
from time import sleep

import pygame
from Settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    """管理游戏资源和行为的类"""
    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode(
            (1200,800))
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        pygame.display.set_caption("Alien Invasion")

        #创建一个用于存储游戏统计信息的实例
        #并创建记分牌
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        #创建Play按钮
        self.play_button = Button(self,"Play")

    def _ship_hit(self):
        #响应飞船被外星人撞到
        if self.stats.ships_left > 0:
            #将ship_left减1并更新记分牌
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            #清空余下的外星人和子弹
            self.aliens.empty()
            self.bullets.empty()

            #创建一群新的外星人，并将飞船放到屏幕底端的中央
            self._create_fleet()
            self.ship.center_ship()

            #暂停
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _create_fleet(self):
        #创建外星人群
        #创建一个外星人并计算一行可容纳多少个外星人
        #外星人的间距为外星人宽度
        alien = Alien(self)
        alien_width,alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2*alien_width)
        number_aliens_x = available_space_x // (2*alien_width)

        #计算屏幕可容纳多少行外星人
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height-
                             (3*alien_height)-ship_height)
        number_rows = available_space_y // (2*alien_height)

        #创建外星人群
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number,row_number)

    def _create_alien(self,alien_number,row_number):
        #创建一个外星人并将其放在当前行
        alien = Alien(self)
        alien_width,alien_height= alien.rect.size
        alien.x = alien_width + 2*alien_width*alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height+2*alien.rect.height*row_number
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        #有外星人到达边缘是采取相应的措施
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        #将外星人整体下移并改变它们的方向
        for alien in self.aliens.sprites():
            alien.rect.y +=self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1


    def run_game(self):
        """开始游戏的主循环"""
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()

                self._update_bullets()
                self._update_aliens()
            self._update_screen()

    def _check_events(self):
        # 响应键盘和鼠标事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)

            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

            elif event.type ==pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self,mouse_pos):
        #在玩家单击play按钮时开始新游戏
        button_click = self.play_button.rect.collidepoint(mouse_pos)
        if  not self.stats.game_active and button_click:
            self._start_a_new_game()

    def _start_a_new_game(self):
        # 重置游戏设置
        self.settings.initialize_dynamic_settings()
        # 重置游戏统计信息
        self.stats.reset_stats()
        self.stats.game_active = True
        self.sb.prep_score()
        self.sb.prep_level()
        self.sb.prep_ships()

        # 清空余下的子弹和外星人
        self.aliens.empty()
        self.bullets.empty()

        # 创建一群新的外星人并让飞船居中
        self._create_fleet()
        self.ship.center_ship()

        # 隐藏鼠标光标
        pygame.mouse.set_visible(False)

    def _check_keydown_events(self,event):
        #响应按键
        if event.key == pygame.K_RIGHT:
            # 向右移动飞船
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key ==pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            if not self.stats.game_active:
                self._start_a_new_game()
            else:
                self._fire_bullet()

    def _bullet_update(self):
        if self.stats.score > 1000:
            self.settings.bullets_allowed = 9

    def _fire_bullet(self):
        #创建一颗子弹，并将其加入到编组bullets中
        if len(self.bullets) < self.settings.bullets_allowed  :

            if self.stats.score <= 1000:
                self.bullets.add(Bullet(self,offset=0))

            else:
                #三发模式
                for offset in [-15,0,15]:
                    self.bullets.add(Bullet(self, offset=offset))
                    

    def _check_keyup_events(self,event):
        #响应松开
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _update_bullets(self):
        #更新子弹的位置并消除消失的子弹
        #更新子弹的位置
        self.bullets.update()
        # 删除消失的子弹
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        #检查是否有子弹击中了外星人
        #如果是，就删除相应的子弹和外星人
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        #响应子弹和外星人碰撞
        # 删除发生碰撞的子弹和外星人
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)
        if collisions:
            for aliens in collisions.values():

                self.stats.score += self.settings.alien_points*len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()
        if not self.aliens:
            # 删除现有的子弹并新建一群外星人
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            #提高等级
            self.stats.level +=1
            self.sb.prep_level()




    def _update_aliens(self):
        #检查是否有外星人位于屏幕边缘，并更新整群外星人的位置
        self._check_fleet_edges()
        self.aliens.update()

        #检测外星人和飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship,self.aliens):
            self._ship_hit()

        #检查是否有外星人到达了屏幕底端
        self._check_aliens_bottom()

    def _check_aliens_bottom(self):
        #检查是否有外星人到达了屏幕底端
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                #像飞船被撞到一样处理
                self._ship_hit()
                break

    def center_ship(self):
        #让飞船在屏幕底端居中
        self.rect.midbottom = self.screen_rect.midbottom
        self.x = float(self.rect.x)

    def _update_screen(self):
        #更新屏幕上的图像并切换到新屏幕
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        #显示得分
        self.sb.show_score()

        #如果游戏处于非活动状态，就绘制Play按钮
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()

if __name__ == '__main__':
    #创建游戏实例并运行
    ai = AlienInvasion()
    ai.run_game()