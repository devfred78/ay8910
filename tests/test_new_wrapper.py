import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import unittest

import ay8910_wrapper as ay


class TestNewClasses(unittest.TestCase):
    def test_instantiation(self):
        # Test ay8910 with all backends
        for backend in ay.Backend:
            with self.subTest(backend=backend):
                chip = ay.ay8910(backend=backend)
                self.assertIsNotNone(chip)
                chip.reset()
                # Test basic register write
                chip.set_register(0, 255)
                # Test generate
                samples = chip.generate(1024)
                self.assertTrue(len(samples) > 0)
        
        # Test ay8912 and ay8913 (just instantiation)
        chip12 = ay.ay8912(backend=ay.Backend.MAME)
        self.assertEqual(chip12._ioports, 1)
        
        chip13 = ay.ay8913(backend=ay.Backend.MAME)
        self.assertEqual(chip13._ioports, 0)

    def test_backend_specifics(self):
        # Test MAME specific
        chip = ay.ay8910(backend=ay.Backend.MAME)
        chip.set_flags(ay.AY8910_LEGACY_OUTPUT)
        
        # Test Caprice32 specific
        chip_cap = ay.ay8910(backend=ay.Backend.CAPRICE32)
        chip_cap.set_stereo_mix(255, 0, 128, 128, 0, 255)
        
        # Test Ay_Emul31 specific
        chip_ay = ay.ay8910(backend=ay.Backend.AY_EMUL31)
        chip_ay.chip_type = ay.ay_emul31_chip_type.YM_Chip
        self.assertEqual(chip_ay.chip_type, ay.ay_emul31_chip_type.YM_Chip)

if __name__ == '__main__':
    unittest.main()
