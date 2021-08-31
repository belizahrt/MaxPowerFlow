import unittest
import MaxPowerFlow

class Test_test_1(unittest.TestCase):

    def test_IsSingleRastrInstance(self):
        i1 = MaxPowerFlow.RastrInstance()
        i2 = MaxPowerFlow.RastrInstance()
        
        self.assertEqual(id(i1), id(i2))

    def test_ReadCmdParams(self):
        argv = ['1', '-rg2', 'pathrg2', '-rg2template', 'pathrg2template', '-unk']
        expected = {'-rg2': 'pathrg2', '-rg2template': 'pathrg2template'} 
        
        result = MaxPowerFlow.ReadCmdLine(argv)
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()
