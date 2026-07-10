import unittest
from llvmlite import binding as llvm
from src.main import compile
from src.typecheck import TypeCheckError
class TypeAndLlvmTests(unittest.TestCase):
 def assert_code(self,code,source):
  with self.assertRaises(TypeCheckError) as caught:compile(source)
  self.assertEqual(code,caught.exception.code)
 def test_bool_literals_and_verified_ir(self):llvm.parse_assembly(compile("fn main() { if true { return 1 } else { return 0 } }")).verify()
 def test_bool_helper_fixpoint(self):llvm.parse_assembly(compile("fn flag() { return true } fn main() { return flag() }")).verify()
 def test_arithmetic_rejects_bool(self):self.assert_code("YADRO-T1001","fn main() { return true + 1 }")
 def test_string_storage_rejected(self):self.assert_code("YADRO-T1005",'fn main() { let x = "secret" return 0 }')
 def test_unreachable_after_return(self):self.assert_code("YADRO-T1008","fn main() { return 1 let x = 2 }")
 def test_mixed_return_types(self):self.assert_code("YADRO-T1001","fn main() { if 1 { return true } return 0 }")
 def test_string_printing_is_valid(self):llvm.parse_assembly(compile('fn main() { print("hello") return 0 }')).verify()
 def test_comparison_return_is_abi_normalized(self):llvm.parse_assembly(compile("fn main() { return 2 > 1 }")).verify()
if __name__=="__main__":unittest.main()
