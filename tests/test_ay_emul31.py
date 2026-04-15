import unittest

import numpy as np

import ay8910_wrapper as ay


class TestAyEmul31(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = 1750000
        self.sample_rate = 44100
        self.chip = ay.ay8910(backend=ay.Backend.AY_EMUL31, clock=self.clock, sample_rate=self.sample_rate)

    def test_initialization(self) -> None:
        self.assertIsInstance(self.chip, ay.ay8910)
        self.assertIsNotNone(self.chip)

    def test_tone_generation(self) -> None:
        period = 248
        self.chip.set_register(0, period & 0xFF)
        self.chip.set_register(1, (period >> 8) & 0x0F)
        self.chip.set_register(7, 0x3E)
        self.chip.set_register(8, 15)
        
        num_samples = 1000
        samples = self.chip.generate(num_samples)
        
        self.assertEqual(len(samples), num_samples)
        self.assertTrue(np.any(samples))

    def test_reset_mutes_output(self) -> None:
        self.chip.set_register(7, 0x3E)
        self.chip.set_register(8, 15)
        self.chip.set_register(0, 100)
        
        samples_before = np.array(self.chip.generate(100))
        self.assertTrue(np.any(samples_before))
        
        self.chip.reset()
        
        samples_after = np.array(self.chip.generate(100))
        self.assertFalse(np.any(samples_after))

if __name__ == "__main__":
    unittest.main()
