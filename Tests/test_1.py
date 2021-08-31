import unittest

import MaxPowerFlow

class Test_test_1(unittest.TestCase):
    def test_A(self):
        self.fail("Not implemented")

    def test_IsSingleRastrInstance(self):
        i1 = MaxPowerFlow.RastrInstance()
        i2 = MaxPowerFlow.RastrInstance()
        
        self.assertEqual(id(i1), id(i2))

if __name__ == '__main__':
    unittest.main()
