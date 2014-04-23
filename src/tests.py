import unittest
import tempfile   
import multitail2
import sys
import os

sys.path.insert(0, '.')

class MultiReadTest(unittest.TestCase):

   def test_read(self): 
      with tempfile.NamedTemporaryFile() as temp:
         mt = multitail2.MultiTail(temp.name) 
         self.assertEqual([], list(mt.poll()))
         temp.write('Some data' + os.linesep)
         temp.flush()
         actual = list(mt.poll())
         expected = [((temp.name, 0), 'Some data')]
         self.assertEqual(actual, expected)

if __name__ == '__main__':
   unittest.main()
