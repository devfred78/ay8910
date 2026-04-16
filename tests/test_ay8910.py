import unittest

import numpy as np

import ay8910_wrapper as ay


class TestAY8910MAME(unittest.TestCase):

    def setUp(self) -> None:
        """Set up a fresh AY8910 instance before each test."""
        self.clock = 2000000  # 2 MHz
        self.sample_rate = 44100
        self.psg = ay.ay8910(backend=ay.Backend.MAME, clock=self.clock, sample_rate=self.sample_rate)
        self.psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
        self.psg.reset()

    def test_initialization(self) -> None:
        """
        Tests that the AY8910 emulator can be correctly initialized.
        """
        self.assertIsInstance(self.psg, ay.ay8910)
        self.assertIsNotNone(self.psg)

    def test_tone_generation(self) -> None:
        """
        Tests that generating a simple tone produces non-zero audio samples.
        """
        # Program a Middle C tone on Channel A
        self.psg.address_w(7)
        self.psg.data_w(0b00111110) 

        period = int(self.clock / (16 * 261.63)) # Middle C
        self.psg.address_w(0)  # Fine tune
        self.psg.data_w(period & 0xFF)
        self.psg.address_w(1)  # Coarse tune
        self.psg.data_w((period >> 8) & 0x0F)

        self.psg.address_w(8)  # Volume register A
        self.psg.data_w(15)    # Max volume

        num_samples = self.sample_rate // 10 # 0.1 seconds of audio
        samples = self.psg.generate(num_samples)

        self.assertEqual(len(samples), num_samples)
        self.assertTrue(np.any(samples), "Generated samples should not be all zero.")

    def test_reset_mutes_output(self) -> None:
        """
        Tests that calling reset() mutes the audio output.
        """
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

        samples_before_reset = np.array(self.psg.generate(self.sample_rate // 100))
        self.assertGreater(np.std(samples_before_reset), 1000, "Should produce audible sound before reset.")

        # Now reset the chip
        self.psg.reset()

        # Generate samples after reset
        samples_after_reset = np.array(self.psg.generate(self.sample_rate // 100), dtype=np.float32)
        
        # A "silent" AY-8910 channel still outputs a small DC voltage.
        # A silent signal has a standard deviation of (or very close to) zero.
        std_dev = np.std(samples_after_reset)
        
        self.assertLess(std_dev, 1.0, 
            f"Signal should be silent (near-zero standard deviation) after reset, but std dev was {std_dev}")

    def test_different_psg_types(self) -> None:
        """Test initialization with different PSG types (AY vs YM)."""
        # Note: Current wrapper defaults to AY for MAME backend. 
        # Switching PSG type for MAME would need a backend_options parameter if we wanted to support it via AYBase.
        psg_ay = ay.ay8910(backend=ay.Backend.MAME, clock=self.clock)
        self.assertIsInstance(psg_ay, ay.ay8910)

    def test_noise_generation(self) -> None:
        """Test that enabling noise produces a signal."""
        # Enable Noise on Channel A, Tone disabled
        self.psg.address_w(7)
        self.psg.data_w(0b00110111) # Tone A, B, C off, Noise A on, B, C off
        
        self.psg.address_w(6) # Noise period
        self.psg.data_w(10)
        
        self.psg.address_w(8) # Volume A
        self.psg.data_w(15)
        
        samples = np.array(self.psg.generate(1000))
        self.assertTrue(np.any(samples), "Noise should produce non-zero samples.")
        
        # Noise should be somewhat random, so checking std dev
        self.assertGreater(np.std(samples), 100, "Noise should have significant variance.")

    def test_envelope_generation(self) -> None:
        """Test that envelope hardware produces a signal."""
        # Enable Tone A, Volume controlled by Envelope
        self.psg.address_w(7)
        self.psg.data_w(0b00111110)
        
        # Tone frequency
        self.psg.address_w(0)
        self.psg.data_w(100)
        self.psg.address_w(1)
        self.psg.data_w(0)
        
        # Envelope volume (bit 4 = 1)
        self.psg.address_w(8)
        self.psg.data_w(0x10)
        
        # Envelope period
        self.psg.address_w(11) # Fine
        self.psg.data_w(0)
        self.psg.address_w(12) # Coarse
        self.psg.data_w(10)
        
        # Envelope shape (Sawtooth)
        self.psg.address_w(13)
        self.psg.data_w(0x08)
        
        samples = np.array(self.psg.generate(4000))
        self.assertTrue(np.any(samples), "Envelope should produce non-zero samples.")

    def test_output_flags(self) -> None:
        """Test that different output flags produce different (but non-zero) results."""
        # Setup a tone
        self.psg.address_w(7)
        self.psg.data_w(0b00111110)
        self.psg.address_w(0)
        self.psg.data_w(100)
        self.psg.address_w(8)
        self.psg.data_w(15)
        
        # Legacy output
        self.psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
        samples_legacy = np.array(self.psg.generate(100))
        
        # Reset and use Single output
        self.psg.reset()
        self.psg.set_flags(ay.AY8910_SINGLE_OUTPUT)
        # Re-program because reset might have cleared registers
        self.psg.address_w(7)
        self.psg.data_w(0b00111110)
        self.psg.address_w(0)
        self.psg.data_w(100)
        self.psg.address_w(8)
        self.psg.data_w(15)
        samples_single = np.array(self.psg.generate(100))
        
        self.assertTrue(np.any(samples_legacy))
        self.assertTrue(np.any(samples_single))
        # They should be different in scale/offset
        self.assertFalse(np.array_equal(samples_legacy, samples_single), "Legacy and Single outputs should differ.")

class TestAY8912Caprice32(unittest.TestCase):

    def setUp(self) -> None:
        """Set up a fresh ay8912 instance with Caprice32 backend before each test."""
        self.clock = 1000000  # 1 MHz
        self.sample_rate = 44100
        self.psg = ay.ay8912(backend=ay.Backend.CAPRICE32, clock=self.clock, sample_rate=self.sample_rate)
        self.psg.reset()

    def test_initialization(self) -> None:
        """Test that the Caprice32 emulator can be initialized."""
        self.assertIsInstance(self.psg, ay.ay8912)
        self.assertIsNotNone(self.psg)

    def test_stereo_generation(self) -> None:
        """Test that Caprice32 generates interleaved stereo samples (length is 2 * num_samples)."""
        num_samples = 1000
        samples = self.psg.generate(num_samples)
        
        # In Caprice32, generate returns num_samples * 2 (interleaved stereo)
        self.assertEqual(len(samples), num_samples * 2)

    def test_tone_generation_stereo(self) -> None:
        """Test that generating a tone produces sound in both channels."""
        # Enable Channel A
        self.psg.address_w(7)
        self.psg.data_w(0b111110) # Noise disabled, Tone A enabled
        
        # Set Frequency A
        period = 100
        self.psg.address_w(0)
        self.psg.data_w(period & 0xFF)
        self.psg.address_w(1)
        self.psg.data_w((period >> 8) & 0x0F)
        
        # Set Volume A
        self.psg.address_w(8)
        self.psg.data_w(15)
        
        # Standard ABC mix (A=Left, B=Center, C=Right)
        # Weights: 255=Full, 0=None
        self.psg.set_stereo_mix(255, 0, 128, 128, 0, 255)
        
        num_samples = 441
        samples = np.array(self.psg.generate(num_samples))
        left = samples[0::2]
        right = samples[1::2]
        
        self.assertTrue(np.any(left), "Left channel should have sound")
        self.assertFalse(np.any(right), "Right channel should be silent (only A enabled, A is full Left)")

    def test_panning(self) -> None:
        """Test that set_stereo_mix correctly pans audio."""
        # Enable Channel A
        self.psg.address_w(7)
        self.psg.data_w(0b111110)
        self.psg.address_w(8)
        self.psg.data_w(15)
        
        # Pan A to the Right
        self.psg.set_stereo_mix(0, 255, 0, 0, 0, 0)
        
        samples = np.array(self.psg.generate(441))
        left = samples[0::2]
        right = samples[1::2]
        
        self.assertFalse(np.any(left), "Left channel should be silent")
        self.assertTrue(np.any(right), "Right channel should have sound")

    def test_reset_cap32(self) -> None:
        """Test that reset in Caprice32 mutes the output."""
        # Enable sound
        self.psg.address_w(7)
        self.psg.data_w(0b111110)
        self.psg.address_w(8)
        self.psg.data_w(15)
        
        samples_before = np.array(self.psg.generate(441))
        self.assertTrue(np.any(samples_before))
        
        self.psg.reset()
        samples_after = np.array(self.psg.generate(441))
        # Caprice32 reset should clear volumes and registers
        self.assertFalse(np.any(samples_after), "Should be silent after reset")

    def test_noise_cap32(self) -> None:
        """Test noise generation in Caprice32."""
        # Enable Noise on A, Tone off
        self.psg.address_w(7)
        self.psg.data_w(0b110111)
        self.psg.address_w(6)
        self.psg.data_w(10)
        self.psg.address_w(8)
        self.psg.data_w(15)
        
        samples = np.array(self.psg.generate(1000))
        self.assertTrue(np.any(samples), "Noise should produce samples in Caprice32")

if __name__ == '__main__':
    unittest.main()