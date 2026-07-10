import shutil,subprocess,tempfile,unittest,os
from pathlib import Path
from src.abi import external_symbol
from src.main import compile,build_native
class NativeAbiTests(unittest.TestCase):
 def test_symbols_are_c_compatible_and_collision_resistant(self):
  names=[external_symbol(x) for x in ("user.data","user_data","пользователь.данные")];self.assertEqual(3,len(set(names)))
  for name in names:self.assertRegex(name,r"^[A-Za-z_][A-Za-z0-9_]*$")
 def test_native_external_link_and_run(self):
  cc=next((shutil.which(x) for x in ("clang","cc","gcc") if shutil.which(x)),None)
  if not cc:self.skipTest("no C linker on runner")
  source='fn main() requires [NetworkAccess] { let x = user.data() let y = anonymize(x) return net.send(y) }'
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp);obj=tmp/"program.o";build_native(compile(source),str(obj));stubs=tmp/"runtime.c";stubs.write_text("#include <stdint.h>\n"+f"int64_t {external_symbol('user.data')}(void){{return 41;}}\n"+f"int64_t {external_symbol('anonymize')}(int64_t x){{return x+1;}}\n"+f"int64_t {external_symbol('net.send')}(int64_t x){{return x;}}\n",encoding="utf-8");exe=tmp/("app.exe" if os.name=='nt' else "app")
   link=subprocess.run([cc,str(obj),str(stubs),"-o",str(exe)],capture_output=True,text=True)
   self.assertEqual(0,link.returncode,f"linker={cc}\nstdout={link.stdout}\nstderr={link.stderr}")
   result=subprocess.run([str(exe)],capture_output=True,text=True)
   self.assertEqual(0,result.returncode,f"stdout={result.stdout}\nstderr={result.stderr}");self.assertIn("42",result.stdout)
if __name__=="__main__":unittest.main()
