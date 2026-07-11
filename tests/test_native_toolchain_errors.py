import subprocess,unittest
from unittest.mock import patch
from src import main
class NativeToolchainErrorTests(unittest.TestCase):
 def test_missing_clang_is_controlled(self):
  with patch("src.main.shutil.which",return_value=None):
   with self.assertRaisesRegex(RuntimeError,"requires clang"):
    main._emit_windows_coff(object(),"unused.obj","x86_64-pc-windows-msvc")
 def test_clang_timeout_is_controlled(self):
  expired=subprocess.TimeoutExpired(["clang","-c"],main.TOOL_TIMEOUT)
  with patch("src.main.subprocess.run",side_effect=expired):
   with self.assertRaisesRegex(RuntimeError,"clang COFF emission timed out"):
    main._run_tool(["clang","-c"],"clang COFF emission")
if __name__=="__main__":unittest.main()
