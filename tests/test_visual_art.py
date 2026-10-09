"""Headless rendering checks: python -m unittest discover -s tests."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import random
import unittest
import pygame
import visual_art


class ArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1100, 650))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_all_artworks_have_visible_content_and_reuse_cache(self):
        for kind, variants, size in (
            ('person', ('worker', 'Матрос', 'Торговка'), (42, 70)),
            ('building', ('house', 'fort', 'market', 'Верфь', 'Банк', 'Таверна'), (160, 140)),
            ('resource', ('wood', 'stone', 'wool'), (24, 24)),
        ):
            for variant in variants:
                with self.subTest(kind=kind, variant=variant):
                    result=visual_art.artwork(kind,*size,variant)
                    self.assertEqual(result.get_size(), size)
                    self.assertGreater(pygame.mask.from_surface(result).count(), 20)
                    self.assertIs(result, visual_art.artwork(kind,*size,variant))

    def test_decoration_preserves_game_random_generator(self):
        state=random.getstate()
        visual_art.artwork('resource', 43, 43, 'wool')
        visual_art.island_ground(1100,650,65)
        for title in ('ТАВЕРНА','БАНК','ТОРГОВАЯ ЛАВКА','РЫНОК','КОРОЛЕВСКАЯ ВЕРФЬ'):
            visual_art.decorate_room(pygame.Surface((1100,650)),title)
        self.assertEqual(random.getstate(),state)

    def test_person_scale_changes_visible_bounds(self):
        bounds=[]
        for scale in (0.75,1.5):
            target=pygame.Surface((300,300),pygame.SRCALPHA)
            visual_art.draw_person(target,150,150,'worker',scale)
            bounds.append(target.get_bounding_rect())
        self.assertGreater(bounds[1].height,bounds[0].height)
        self.assertGreater(bounds[1].width,bounds[0].width)


if __name__ == '__main__':
    unittest.main()
