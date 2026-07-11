import unittest
from src.main import compile
from src.typesys import TypeCheckError
class ReturnPathTests(unittest.TestCase):
 def test_helper_missing_return_is_rejected(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2204"):compile("fn helper(x) { if x > 0 { return 1 } } fn main() { return helper(1) }")
 def test_entry_keeps_documented_implicit_zero(self):compile("fn main() { print(1) }")
 def test_both_branches_return(self):compile("fn helper(x) { if x > 0 { return 1 } else { return 0 } } fn main() { return helper(1) }")
 def test_nested_complete_paths(self):compile("fn helper(x) { if x > 0 { if x > 1 { return 2 } else { return 1 } } else { return 0 } } fn main() { return helper(2) }")
if __name__=="__main__":unittest.main()
