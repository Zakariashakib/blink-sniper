import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
import pygame
from unittest.mock import patch
from game import Game
from tracking import Observation


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game=Game(camera=False)
        self.game.t=2

    def tearDown(self):
        self.game.tracker.close()
        pygame.quit()

    def test_both_entrypoints_import_same_main(self):
        import main
        import game
        self.assertIs(main.main,game.main)

    def test_each_state_draws_and_buttons_fit(self):
        for state in ['menu','playing','settings','calibration','help','paused','complete','won','lost','hostage_lost','calibration_done','calibration_failed']:
            self.game.state=state
            self.game.draw()
            for key,rect in self.game.buttons:
                self.assertTrue(self.game.screen.get_rect().contains(rect),(state,key,rect))

    def test_three_missions_complete_with_hits(self):
        g=self.game
        g.start_game()
        for level in (1,2,3):
            self.assertEqual(g.level,level)
            for enemy in g.entities[:]:
                while enemy.hp>0:
                    g.t+=.3
                    g.aim.update(enemy.x,enemy.y)
                    g.shoot()
            g.play_update(.5)
            self.assertEqual(g.state,'won' if level==3 else 'complete')
            if level<3:g.action('next')
        self.assertEqual(g.hits,g.shots)

    def test_damaged_enemy_counts_as_hit(self):
        g=self.game;g.start_game();g.level=3;g.spawn()
        boss=next(e for e in g.entities if e.kind=='boss')
        g.aim.update(boss.x,boss.y);g.shoot()
        self.assertEqual(g.hits,1)
        self.assertEqual(boss.hp,5)

    def test_lost_tracking_freezes_enemy_attacks(self):
        g=self.game;g.start_game();g.level=2;g.spawn();g.mode='eyes'
        before=[e.attack for e in g.entities]
        g.play_update(1)
        self.assertEqual(before,[e.attack for e in g.entities])
        g.shoot()
        self.assertEqual(g.shots,0)

    def test_civilian_hit_ends_mission(self):
        g=self.game;g.start_game();g.level=3;g.spawn()
        g.aim.update(1050,270);g.shoot()
        self.assertEqual(g.state,'hostage_lost')

    def test_shooting_in_menu_does_not_change_score(self):
        self.game.shoot()
        self.assertEqual(self.game.shots,0)

    def test_pause_cancels_manual_charge(self):
        g=self.game;g.start_game();g.charging=g.t;g.action('pause')
        self.assertIsNone(g.charging)
        g.shoot()
        self.assertEqual(g.shots,0)

    def test_scan_selects_button_at_blink_start(self):
        g=self.game;g.mode='eyes';g.valid_face=True;g.detector.baseline=.3
        g.buttons=[('help',pygame.Rect(0,0,10,10)),('settings',pygame.Rect(20,0,10,10))]
        g.scan_index=1;g.scan_locked=0;g.blink=True;g.detector.closed=True
        g.menu_input(.016)
        self.assertEqual(g.state,'help')

    def test_focus_loss_pauses(self):
        g=self.game;g.start_game()
        pygame.event.post(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        g.events()
        self.assertEqual(g.state,'paused')

    def test_blink_during_calibration_cannot_cancel_setup(self):
        g=self.game;g.state='calibration';g.mode='eyes'
        g.valid_face=True;g.detector.baseline=.3;g.blink=True
        g.buttons=[('menu',pygame.Rect(0,0,10,10))]
        g.menu_input(.016)
        self.assertEqual(g.state,'calibration')

    def test_reacquiring_closed_eyes_keeps_combat_frozen(self):
        g=self.game;g.start_game();g.level=2;g.spawn();g.mode='eyes';g.aim_mode='head'
        g.valid_face=True;g.detector.baseline=.3;g.detector.closed=True
        before=[e.attack for e in g.entities]
        g.play_update(1)
        self.assertEqual(before,[e.attack for e in g.entities])

    def test_camera_observations_fire_once_at_frozen_open_eye_aim(self):
        g=self.game;g.start_game();g.mode='eyes';g.aim_mode='head';g.detector.baseline=.3
        target=g.entities[0]
        g.aim.update(target.x,target.y);g.raw_aim.update(target.x,target.y)
        nose=(.5+(target.x/1280-.5)/4,.5+(target.y/720-.5)/5)
        now=100
        for closed,frames in [(False,20),(True,30)]:
            for i in range(frames):
                now+=.02
                observation=Observation(now,'Face tracked',.1 if closed else .3,(0,0),(.9,.9) if closed else nose)
                with patch.object(g.tracker,'latest',return_value=observation),patch('game.time.monotonic',return_value=now):
                    g.update(.02)
        self.assertEqual(g.shots,1)
        self.assertEqual(g.hits,1)
        self.assertLess(g.aim.distance_to((target.x,target.y)),1)

    def test_calibration_retry_remembers_active_mission(self):
        g=self.game;g.start_game();g.mode='eyes'
        g.start_calibration()
        g.change('calibration_failed');g.start_calibration()
        self.assertTrue(g.cal_resume)
        g.change('calibration_done');g.action('deploy')
        self.assertEqual(g.state,'playing')


if __name__=='__main__':unittest.main()
