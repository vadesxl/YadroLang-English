import unittest
from llvmlite import binding as llvm
from src.lexer import Lexer
from src.syntax import Parser
from src.typesys import TypeChecker, TypeCheckError, BOOL
from src.main import SYSTEM_API
from src.codegen import Codegen

class StrictTypeTests(unittest.TestCase):
 def check(self,source):
  ast=Parser(Lexer(source).tokens()).parse(); return ast,TypeChecker(ast,SYSTEM_API).check()
 def test_comparison_is_bool_and_return_lowers_validly(self):
  ast,types=self.check("fn main() { return 1 < 2 }"); self.assertEqual(BOOL,types.returns["main"]); mod=llvm.parse_assembly(Codegen().generate(ast)); mod.verify()
 def test_mixed_arithmetic_rejected(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2301"): self.check('fn main() { return "x" + 1 }')
 def test_string_variable_rejected_with_migration_diagnostic(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2305"): self.check('fn main() { let x = "hello" return 0 }')
 def test_unreachable_rejected(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2202"): self.check("fn main() { return 1 print(2) }")
 def test_missing_path_rejected(self):
  with self.assertRaisesRegex(TypeCheckError,"YADRO-T2204"): self.check("fn main() { if 1 < 2 { return 1 } }")
 def test_both_return_branches_verify(self):
  ast,_=self.check("fn main() { if 1 < 2 { return 1 } else { return 2 } }"); llvm.parse_assembly(Codegen().generate(ast)).verify()
 def test_print_string_verifies(self):
  ast,_=self.check('fn main() { print("hello") return 0 }'); llvm.parse_assembly(Codegen().generate(ast)).verify()

if __name__=="__main__":unittest.main()
