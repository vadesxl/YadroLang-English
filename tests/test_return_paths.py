import unittest
from src.main import compile
from src.typesys import TypeCheckError
class ReturnPathTests(unittest.TestCase):
 def test_missing(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2204"):compile("fn helper(x) { if x > 0 { return 1 } } fn main() { return helper(1) }")
 def test_entry_compat(self):compile("fn main() { print(1) }")
 def test_complete(self):compile("fn helper(x) { if x > 0 { return 1 } else { return 0 } } fn main() { return helper(1) }")
if __name__=="__main__":unittest.main()
