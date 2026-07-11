# -*- coding: utf-8 -*-
"""YadroLang compiler pipeline: parse, semantics, types, ethics, LLVM."""
import os,shutil,subprocess,sys,tempfile
from llvmlite import binding as llvm
from src.lexer import Lexer,LexerError
from src.syntax import Parser,ParserError,Call,NumberLit,Binary
from src.ethics import EthicalAnalyzer,EthicalError,SINKS,SOURCES,SANITIZERS
from src.typesys import TypeChecker,TypeCheckError
from src.codegen import Codegen,CodegenError
TOOL_TIMEOUT=30
class EntryPointError(Exception):pass
class SemanticError(Exception):pass
def _check_entry_point(ast):
 entries=[f for f in ast.functions if f.name=="main"]
 if not entries:raise EntryPointError("No entry point: program must declare function 'main'.")
 if len(entries)>1:raise EntryPointError("Entry point 'main' must be declared exactly once.")
 if entries[0].parameters:raise EntryPointError("Entry point 'main' must not accept parameters.")
def _check_unique_functions(ast):
 seen=set()
 for function in ast.functions:
  if function.name in seen:raise SemanticError(f"Function '{function.name}' is declared more than once (line {function.string}).")
  if function.name=="printf" or function.name.startswith("yadro_"):raise SemanticError(f"Function '{function.name}' collides with runtime ABI (line {function.string}).")
  seen.add(function.name)
SYSTEM_API_ARITY={**{n:0 for n in SOURCES},**{n:1 for n in SANITIZERS},**{n:1 for n in SINKS},"print":1};SYSTEM_API=set(SYSTEM_API_ARITY)
def _collect(node,kind,out):
 if isinstance(node,kind):out.append(node)
 values=getattr(node,"__dict__",None)
 if values:
  for value in values.values():
   if isinstance(value,list):
    for item in value:_collect(item,kind,out)
   elif hasattr(value,"__dict__"):_collect(value,kind,out)
def _check_calls(ast):
 arity={f.name:len(f.parameters) for f in ast.functions}
 for function in ast.functions:
  calls=[]
  for statement in function.body:_collect(statement,Call,calls)
  for call in calls:
   expected=arity.get(call.name,SYSTEM_API_ARITY.get(call.name))
   if expected is None:raise SemanticError(f"Unknown function '{call.name}' (line {call.string}).")
   if len(call.arguments)!=expected:raise SemanticError(f"Function '{call.name}' expects {expected} argument(s), got {len(call.arguments)} (line {call.string}).")
I64_MIN=-(2**63);I64_MAX=2**63-1
def _constant_int(node):
 if isinstance(node,NumberLit):return node.value
 if not isinstance(node,Binary):return None
 left,right=_constant_int(node.left),_constant_int(node.right)
 if left is None or right is None:return None
 if node.op=="+":return left+right
 if node.op=="-":return left-right
 if node.op=="*":return left*right
 if node.op=="/" and right!=0:return abs(left)//abs(right)*(-1 if (left<0)!=(right<0) else 1)
 return None
def _check_expressions(ast):
 for function in ast.functions:
  numbers=[];binaries=[]
  for statement in function.body:_collect(statement,NumberLit,numbers);_collect(statement,Binary,binaries)
  for number in numbers:
   if not I64_MIN<=number.value<=I64_MAX:raise SemanticError(f"Numeric literal {number.value} is outside i64 (line {number.string}).")
  for binary in binaries:
   if binary.op!="/":continue
   divisor,dividend=_constant_int(binary.right),_constant_int(binary.left)
   if divisor==0:raise SemanticError(f"Division by zero (line {binary.string}).")
   if dividend==I64_MIN and divisor==-1:raise SemanticError(f"Signed i64 division overflow (line {binary.string}).")
def compile(source,emit_ir=False):
 ast=Parser(Lexer(source).tokens()).parse();_check_unique_functions(ast);_check_entry_point(ast);_check_calls(ast);_check_expressions(ast);TypeChecker(SYSTEM_API).check(ast);EthicalAnalyzer().check(ast);ir_code=Codegen().generate(ast)
 if emit_ir:print(ir_code)
 return ir_code
def _run_tool(command,stage):
 try:return subprocess.run(command,capture_output=True,text=True,timeout=TOOL_TIMEOUT)
 except subprocess.TimeoutExpired as error:raise RuntimeError(f"{stage} timed out after {TOOL_TIMEOUT}s: {os.path.basename(str(error.cmd[0]))}") from error
def _emit_windows_coff(module,output,triple):
 clang=shutil.which("clang")
 if not clang:raise RuntimeError("Windows native object emission requires clang from a supported LLVM toolchain in PATH")
 with tempfile.TemporaryDirectory() as tmp:
  ir_path=os.path.join(tmp,"yadro.ll")
  with open(ir_path,"w",encoding="utf-8",newline="\n") as ir_file:ir_file.write(str(module))
  result=_run_tool([clang,"-target",triple,"-x","ir","-c",ir_path,"-o",output],"clang COFF emission")
  if result.returncode:raise RuntimeError(f"clang COFF emission failed: {result.stderr.strip()}")
 with open(output,"rb") as object_file:
  if object_file.read(2)!=b"\x64\x86":raise RuntimeError("clang did not emit an AMD64 COFF object")
def build_native(ir_code,output="kernel.o"):
 for initializer in (getattr(llvm,"initialize",None),getattr(llvm,"initialize_native_target",None),getattr(llvm,"initialize_native_asmprinter",None)):
  if initializer:
   try:initializer()
   except Exception:pass
 triple=llvm.get_default_triple();target=llvm.Target.from_triple(triple);machine=target.create_target_machine();module=llvm.parse_assembly(ir_code);module.triple=triple;module.data_layout=str(machine.target_data);module.verify()
 if os.name=="nt":_emit_windows_coff(module,output,triple)
 else:
  with open(output,"wb") as object_file:object_file.write(machine.emit_object(module))
 print(f"[YADRO] Native object: {output}")
def main_cli():
 if len(sys.argv)<2:print("Usage: python -m src.main file.yad [--ir]");raise SystemExit(1)
 try:
  source=open(sys.argv[1],encoding="utf-8").read();ir_code=compile(source,"--ir" in sys.argv)
  if "--ir" not in sys.argv:build_native(ir_code)
 except (OSError,EntryPointError,SemanticError,TypeCheckError,EthicalError,ParserError,LexerError,CodegenError,RuntimeError) as error:print(f"[YADRO] Compilation error: {error}");raise SystemExit(1)
 print("[YADRO] Compilation complete. Code is law.")
if __name__=="__main__":main_cli()
