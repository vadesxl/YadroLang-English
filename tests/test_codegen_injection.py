import importlib,unittest
from src import codegen_verified as backend
class CodegenInjectionTests(unittest.TestCase):
 def test_manglers_are_instance_local(self):
  first=backend.Codegen(symbol_mangler=lambda kind,name:f"first_{kind}_{name}")
  second=backend.Codegen(symbol_mangler=lambda kind,name:f"second_{kind}_{name}")
  self.assertEqual("first_fn_main",first.symbol_mangler("fn","main"));self.assertEqual("second_fn_main",second.symbol_mangler("fn","main"))
 def test_facade_import_does_not_mutate_backend_default(self):
  original=backend.symbol;import src.codegen as facade;importlib.reload(facade);self.assertIs(original,backend.symbol);self.assertIs(original,backend.Codegen().symbol_mangler)
if __name__=="__main__":unittest.main()
