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


class TailedFileTest(unittest.TestCase):

   def test_read_with_limit(self):
      """
      When we read from a file with a specified limit, observe the limit.
      """
      with tempfile.NamedTemporaryFile() as temp:
         f = multitail2.TailedFile(temp.name, skip_to_end=False)
         # Write more than the limit we will specify.
         temp.write('a' * 110)
         temp.flush()
         f._read(100)
         self.assertEqual(100, len(f._buf))

   def test_read_without_limit(self):
      """
      When we read from a file without a specified limit, read the remainder.
      """
      with tempfile.NamedTemporaryFile() as temp:
         f = multitail2.TailedFile(temp.name, skip_to_end=False)
         # Write a "large" amount of data.
         temp.write('a' * 70000)
         temp.flush()
         # Now read less than that.
         f._read()
         self.assertEqual(70000, len(f._buf))

if __name__ == '__main__':
   unittest.main()
