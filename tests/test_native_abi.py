import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from src.abi import external_symbol
from src.main import compile,build_native
TIMEOUT=30
class NativeAbiTests(unittest.TestCase):
 def test_symbols_are_c_compatible_and_collision_resistant(self):
  names=[external_symbol(x) for x in ("user.data","user_data","пользователь.данные")];self.assertEqual(3,len(set(names)))
  for name in names:self.assertRegex(name,r"^[A-Za-z_][A-Za-z0-9_]*$")
 def test_native_external_link_and_run(self):
  cc=next((shutil.which(x) for x in ("clang","cc","gcc") if shutil.which(x)),None)
  if not cc:self.fail("required C compiler/linker not found in PATH")
  source='fn main() requires [NetworkAccess] { let x = user.data() let y = anonymize(x) return net.send(y) }'
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp);obj=tmp/"program.obj";build_native(compile(source),str(obj))
   if os.name=="nt":self.assertEqual(b"\x64\x86",obj.read_bytes()[:2],"expected AMD64 COFF magic")
   stubs=tmp/"runtime.c";stubs.write_text("#include <stdint.h>\n"+f"int64_t {external_symbol('user.data')}(void){{return 41;}}\n"+f"int64_t {external_symbol('anonymize')}(int64_t x){{return x+1;}}\n"+f"int64_t {external_symbol('net.send')}(int64_t x){{return x;}}\n",encoding="utf-8")
   exe=tmp/("app.exe" if os.name=='nt' else "app");command=[cc,str(obj),str(stubs),"-o",str(exe)];command[1:1]=["-fuse-ld=lld"] if os.name=='nt' else []
   try:link=subprocess.run(command,capture_output=True,text=True,timeout=TIMEOUT)
   except subprocess.TimeoutExpired as error:self.fail(f"native link timed out after {TIMEOUT}s: {error.cmd[0]}")
   self.assertEqual(0,link.returncode,f"command={command}\nstdout={link.stdout}\nstderr={link.stderr}")
   try:result=subprocess.run([str(exe)],capture_output=True,timeout=TIMEOUT)
   except subprocess.TimeoutExpired as error:self.fail(f"native executable timed out after {TIMEOUT}s: {error.cmd[0]}")
   self.assertEqual(0,result.returncode,f"stdout={result.stdout!r}\nstderr={result.stderr!r}");self.assertIn(b"42",result.stdout)
if __name__=="__main__":unittest.main()
