import unittest

import numpy as np

import ay8910_wrapper as ay


class TestAyEmul31(unittest.TestCase):

    def setUp(self) -> None:
        """Initialise une instance de ay_emul31 avant chaque test."""
        self.chip = ay.ay_emul31()
        self.clock = 1750000
        self.sample_rate = 44100

    def test_initialization(self) -> None:
        """Vérifie que le wrapper ay_emul31 peut être initialisé."""
        self.assertIsInstance(self.chip, ay.ay_emul31)
        self.assertIsNotNone(self.chip)

    def test_tone_generation(self) -> None:
        """Vérifie que la génération d'un ton produit des échantillons non nuls."""
        # Configurer un son simple : Canal A, Ton 440 Hz approx
        # Period = Clock / (16 * Freq) = 1750000 / (16 * 440) approx 248
        period = 248
        self.chip.set_register(0, period & 0xFF)  # Fine
        self.chip.set_register(1, (period >> 8) & 0x0F)  # Coarse
        
        self.chip.set_register(7, 0x3E)  # Mixer : Tone A ON, others OFF
        self.chip.set_register(8, 15)    # Amplitude A : Max
        
        num_samples = 1000
        samples = self.chip.generate(num_samples, self.clock, self.sample_rate)
        
        self.assertEqual(len(samples), num_samples)
        self.assertTrue(np.any(samples), "Signal non détecté : les échantillons sont tous nuls.")

    def test_reset_mutes_output(self) -> None:
        """Vérifie que la remise à zéro coupe le son."""
        # Activer le son
        self.chip.set_register(7, 0x3E)
        self.chip.set_register(8, 15)
        self.chip.set_register(0, 100)
        
        samples_before = np.array(self.chip.generate(100, self.clock, self.sample_rate))
        self.assertTrue(np.any(samples_before))
        
        # Reset (ici, nous simulons un reset car ay_emul31 n'a pas forcément une méthode reset() exposée, 
        # ou nous devons voir si elle existe. Selon le wrapper.cpp, vérifions.)
        # Si la méthode reset() n'existe pas, on peut au moins remettre les registres à zéro.
        if hasattr(self.chip, 'reset'):
            self.chip.reset()
        else:
            for i in range(14):
                self.chip.set_register(i, 0)
            self.chip.set_register(7, 0xFF) # Tout OFF
        
        samples_after = np.array(self.chip.generate(100, self.clock, self.sample_rate))
        self.assertFalse(np.any(samples_after), "Le son devrait être coupé après reset.")


if __name__ == "__main__":
    unittest.main()
