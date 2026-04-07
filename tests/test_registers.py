import unittest

import ay8910_wrapper


class TestRegisterAccess(unittest.TestCase):
    def test_mame_register_access(self) -> None:
        psg = ay8910_wrapper.ay8910(ay8910_wrapper.PSG_TYPE_AY, 1000000, 1, 0)
        
        # Test individual register write/read
        psg.set_register(0, 0x55)
        self.assertEqual(psg.get_register(0), 0x55)
        
        psg.set_register(1, 0xAA)
        # Period coarse for AY is 4 bits
        self.assertEqual(psg.get_register(1), 0x0A)
        
        # Test get_registers
        regs = psg.get_registers()
        self.assertEqual(len(regs), 32)
        self.assertEqual(regs[0], 0x55)
        self.assertEqual(regs[1], 0x0A)

    def test_cap32_register_access(self) -> None:
        psg = ay8910_wrapper.ay8912_cap32(2000000, 44100)
        
        # Test individual register write/read
        psg.set_register(0, 0x55)
        self.assertEqual(psg.get_register(0), 0x55)
        
        psg.set_register(1, 0xAA)
        # Period coarse for AY is 4 bits
        self.assertEqual(psg.get_register(1), 0x0A)
        
        # Test get_registers
        regs = psg.get_registers()
        self.assertEqual(len(regs), 16)
        self.assertEqual(regs[0], 0x55)
        self.assertEqual(regs[1], 0x0A)
        
    def test_address_data_w_mame(self) -> None:
        psg = ay8910_wrapper.ay8910(ay8910_wrapper.PSG_TYPE_AY, 1000000, 1, 0)
        psg.address_w(7)
        psg.data_w(0x3F)
        self.assertEqual(psg.get_register(7), 0x3F)
        
    def test_address_data_w_cap32(self) -> None:
        psg = ay8910_wrapper.ay8912_cap32(2000000, 44100)
        psg.address_w(7)
        psg.data_w(0x3F)
        self.assertEqual(psg.get_register(7), 0x3F)

if __name__ == '__main__':
    unittest.main()
