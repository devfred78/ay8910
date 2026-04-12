import unittest
from unittest.mock import MagicMock, patch

import numpy as np

import ay8910_wrapper as ay
from ay8910_wrapper.direct_output import DirectOutput


class TestDirectOutput(unittest.TestCase):

    def setUp(self):
        # Mock the sounddevice OutputStream
        self.sd_patcher = patch('sounddevice.OutputStream')
        self.mock_sd_stream = self.sd_patcher.start()
        
        # Create a mock chip
        self.mock_chip = MagicMock()
        # Simulate generating 1024 samples
        self.mock_chip.generate.return_value = [0] * 1024
        
        self.sample_rate = 44100
        self.channels = 1
        self.clock = 1750000

    def tearDown(self):
        self.sd_patcher.stop()

    def test_initialization(self):
        do = DirectOutput(self.mock_chip, self.sample_rate, self.channels, self.clock)
        self.assertEqual(do.device, self.mock_chip)
        self.assertEqual(do.sample_rate, self.sample_rate)
        self.assertEqual(do.channels, self.channels)
        self.assertIsNone(do.stream)

    def test_start_stop(self):
        do = DirectOutput(self.mock_chip, self.sample_rate, self.channels, self.clock)
        do.start()
        self.mock_sd_stream.assert_called_once()
        self.mock_sd_stream.return_value.start.assert_called_once()
        self.assertIsNotNone(do.stream)
        
        do.stop()
        self.mock_sd_stream.return_value.stop.assert_called_once()
        self.mock_sd_stream.return_value.close.assert_called_once()
        self.assertIsNone(do.stream)

    def test_callback_mono_mame(self):
        # Test callback with mono chip (MAME signature)
        do = DirectOutput(self.mock_chip, self.sample_rate, 1, self.clock)
        outdata = np.zeros((10, 1), dtype=np.int16)
        
        # MAME generate signature: generate(frames, sample_rate)
        self.mock_chip.generate.return_value = [100] * 10
        
        do._callback(outdata, 10, None, None)
        
        self.mock_chip.generate.assert_called_with(10, self.sample_rate)
        self.assertTrue(np.all(outdata == 100))

    def test_callback_mono_ay_emul31(self):
        # Test callback with mono chip (Ay_Emul31 signature)
        # We need to simulate a TypeError for the first call to trigger the fallback
        def side_effect(frames, *args):
            if len(args) == 1: # MAME signature
                raise TypeError("Wrong number of arguments")
            return [200] * frames
            
        self.mock_chip.generate.side_effect = side_effect
        
        do = DirectOutput(self.mock_chip, self.sample_rate, 1, self.clock)
        outdata = np.zeros((10, 1), dtype=np.int16)
        
        do._callback(outdata, 10, None, None)
        
        # It should have tried both
        self.assertEqual(self.mock_chip.generate.call_count, 2)
        self.assertTrue(np.all(outdata == 200))

    def test_callback_stereo_caprice32(self):
        # Test callback with stereo chip (Caprice32 signature)
        do = DirectOutput(self.mock_chip, self.sample_rate, 2, self.clock)
        outdata = np.zeros((10, 2), dtype=np.int16)
        
        # Caprice32 generate signature: generate(frames) -> 2 * frames samples
        self.mock_chip.generate.return_value = [300] * 20
        
        do._callback(outdata, 10, None, None)
        
        self.mock_chip.generate.assert_called_with(10)
        self.assertTrue(np.all(outdata == 300))

class TestLiveSupport(unittest.TestCase):
    
    @patch('sounddevice.OutputStream')
    def test_play_stop_methods(self, mock_sd):
        # Test that the injected play/stop methods work
        chip = ay.ay8910(ay.psg_type.PSG_TYPE_AY, 2000000, 1, 0)
        chip.start()
        
        self.assertFalse(hasattr(chip, '_live_output')) # Actually it's in a global dict in __init__.py
        
        chip.play()
        mock_sd.assert_called()
        
        chip.stop()
        # Verify it stopped (how to check the global dict? it's private)
        # But we can check if it can be started again
        chip.play()
        self.assertEqual(mock_sd.call_count, 2)
        chip.stop()

if __name__ == "__main__":
    unittest.main()
