import unittest
from src.main import compile
from src.typesys import TypeCheckError
class ReturnPathTests(unittest.TestCase):
 def test_helper_missing_return_is_rejected(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2204"):compile("fn helper(x) { if x > 0 { return 1 } } fn main() { return helper(1) }")
 def test_entry_keeps_documented_implicit_zero(self):compile("fn main() { print(1) }")
 def test_both_branches_return(self):compile("fn helper(x) { if x > 0 { return 1 } else { return 0 } } fn main() { return helper(1) }")
 def test_nested_complete_paths(self):compile("fn helper(x) { if x > 0 { if x > 1 { return 2 } else { return 1 } } else { return 0 } } fn main() { return helper(2) }")
 def test_loop_body_return_is_not_total(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2204"):compile("fn helper(x) { while x > 0 { return 1 } } fn main() { return helper(0) }")
 def test_loop_followed_by_return_is_total(self):compile("fn helper(x) { while x > 0 { x = x - 1 } return x } fn main() { return helper(2) }")
 def test_statement_after_total_branch_is_unreachable(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2006"):compile("fn helper(x) { if x > 0 { return 1 } else { return 0 } return 2 } fn main() { return helper(1) }")
if __name__=="__main__":unittest.main()
