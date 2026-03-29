import unittest
import ay8910_wrapper as ay
import numpy as np

class TestAY8910Wrapper(unittest.TestCase):

    def setUp(self):
        """Set up a fresh AY8910 instance before each test."""
        self.clock = 2000000  # 2 MHz
        self.sample_rate = 44100
        self.psg = ay.ay8910(ay.psg_type.PSG_TYPE_AY, self.clock, 1, 0)
        self.psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
        self.psg.start()
        self.psg.reset()

    def test_initialization(self):
        """Test that the AY8910 emulator can be initialized."""
        self.assertIsInstance(self.psg, ay.ay8910)
        # Basic check to ensure it's not in a crashed state
        self.assertIsNotNone(self.psg)

    def test_tone_generation(self):
        """Test that generating a simple tone produces non-zero samples."""
        # Program a Middle C tone on Channel A
        self.psg.address_w(7)  # Mixer register
        self.psg.data_w(0b00111110) # Enable Tone A, disable others

        period = int(self.clock / (16 * 261.63)) # Middle C
        self.psg.address_w(0)  # Fine tune
        self.psg.data_w(period & 0xFF)
        self.psg.address_w(1)  # Coarse tune
        self.psg.data_w((period >> 8) & 0x0F)

        self.psg.address_w(8)  # Volume register A
        self.psg.data_w(15)    # Max volume

        # Generate a small number of samples
        num_samples = self.sample_rate // 10 # 0.1 seconds of audio
        samples = self.psg.generate(num_samples, self.sample_rate)

        # Assert that samples were generated
        self.assertEqual(len(samples), num_samples)
        
        # Assert that the generated samples are not all zero (i.e., sound was produced)
        # We use numpy to efficiently check for non-zero values
        self.assertTrue(np.any(samples), "Generated samples should not be all zero.")

    def test_reset_mutes_output(self):
        """Test that a reset mutes the output."""
        # First, generate some sound
        self.psg.address_w(7)
        self.psg.data_w(0b00111110)
        self.psg.address_w(8)
        self.psg.data_w(15)
        period = int(self.clock / (16 * 440)) # A4
        self.psg.address_w(0)
        self.psg.data_w(period & 0xFF)
        self.psg.address_w(1)
        self.psg.data_w((period >> 8) & 0x0F)

        samples_before_reset = self.psg.generate(self.sample_rate // 100, self.sample_rate)
        self.assertTrue(np.any(samples_before_reset), "Should produce sound before reset.")

        # Now reset the chip
        self.psg.reset()

        # Generate samples after reset
        samples_after_reset = self.psg.generate(self.sample_rate // 100, self.sample_rate)
        self.assertFalse(np.any(samples_after_reset), "Should produce silence after reset.")

if __name__ == '__main__':
    unittest.main()
