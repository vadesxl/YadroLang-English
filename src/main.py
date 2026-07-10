# -*- coding: utf-8 -*-
"""YadroLang compiler entry point and semantic validation."""
import sys
from llvmlite import binding as llvm
from src.lexer import Lexer, LexerError
from src.syntax import Parser, ParserError, Call, NumberLit, Binary
from src.ethics import EthicalAnalyzer, EthicalError, SINKS, SOURCES, SANITIZERS
from src.codegen import Codegen, CodegenError
from src.typesys import TypeChecker, TypeCheckError

class EntryPointError(Exception): pass
class SemanticError(Exception): pass

def _check_entry_point(ast):
 points=[f for f in ast.functions if f.name=="main"]
 if not points:raise EntryPointError("No entry point: program must declare function 'main'.")
 if len(points)>1:raise EntryPointError("Entry point 'main' must be declared exactly once.")
 if points[0].parameters:raise EntryPointError("Entry point 'main' must not accept parameters.")

def _check_unique_functions(ast):
 seen=set()
 for function in ast.functions:
  if function.name in seen:raise SemanticError(f"Function '{function.name}' is declared more than once (line {function.string}).")
  seen.add(function.name)

SYSTEM_API_ARITY={**{n:0 for n in SOURCES},**{n:1 for n in SANITIZERS},**{n:1 for n in SINKS},"print":1}
SYSTEM_API=set(SYSTEM_API_ARITY)

def _walk(node,kind,out):
 if isinstance(node,kind):out.append(node)
 values=getattr(node,"__dict__",None)
 if values:
  for value in values.values():
   if isinstance(value,list):
    for item in value:_walk(item,kind,out)
   elif hasattr(value,"__dict__"):_walk(value,kind,out)

def _check_calls(ast):
 arity={f.name:len(f.parameters) for f in ast.functions}
 for function in ast.functions:
  calls=[]
  for statement in function.body:_walk(statement,Call,calls)
  for call in calls:
   expected=arity.get(call.name,SYSTEM_API_ARITY.get(call.name))
   if expected is None:raise SemanticError(f"Unknown function '{call.name}' (line {call.string}).")
   if len(call.arguments)!=expected:raise SemanticError(f"Function '{call.name}' expects {expected} argument(s), got {len(call.arguments)} (line {call.string}).")

I64_MIN=-(2**63);I64_MAX=2**63-1

def _constant(node):
 if isinstance(node,NumberLit):return node.value
 if not isinstance(node,Binary):return None
 left,right=_constant(node.left),_constant(node.right)
 if left is None or right is None:return None
 if node.op=="+":return left+right
 if node.op=="-":return left-right
 if node.op=="*":return left*right
 if node.op=="/" and right:return abs(left)//abs(right)*(-1 if (left<0)!=(right<0) else 1)
 return None

def _check_expressions(ast):
 for function in ast.functions:
  numbers,binaries=[],[]
  for statement in function.body:_walk(statement,NumberLit,numbers);_walk(statement,Binary,binaries)
  for number in numbers:
   if not I64_MIN<=number.value<=I64_MAX:raise SemanticError(f"Numeric literal {number.value} is outside i64 (line {number.string}).")
  for binary in binaries:
   if binary.op=="/":
    divisor,dividend=_constant(binary.right),_constant(binary.left)
    if divisor==0:raise SemanticError(f"Division by zero (line {binary.string}).")
    if dividend==I64_MIN and divisor==-1:raise SemanticError(f"Signed i64 division overflow (line {binary.string}).")

def compile(source:str,emit_ir=False)->str:
 ast=Parser(Lexer(source).tokens()).parse();_check_unique_functions(ast);_check_entry_point(ast);_check_calls(ast);_check_expressions(ast)
 TypeChecker(ast,SYSTEM_API).check();EthicalAnalyzer().check(ast);ir_code=Codegen().generate(ast)
 if emit_ir:print(ir_code)
 return ir_code

def build_native(ir_code:str,output="kernel.o"):
 for initializer in (getattr(llvm,"initialize",None),getattr(llvm,"initialize_native_target",None),getattr(llvm,"initialize_native_asmprinter",None)):
  if initializer:
   try:initializer()
   except Exception:pass
 module=llvm.parse_assembly(ir_code);module.verify();target=llvm.Target.from_default_triple().create_target_machine()
 with open(output,"wb") as f:f.write(target.emit_object(module))
 print(f"[YADRO] Native object: {output}")

def main_cli():
 if len(sys.argv)<2:print("Usage: python -m src.main file.yad [--ir]");sys.exit(1)
 try:
  source=open(sys.argv[1],encoding="utf-8").read();ir_code=compile(source,emit_ir="--ir" in sys.argv)
  if "--ir" not in sys.argv:build_native(ir_code)
 except (OSError,EntryPointError,SemanticError,TypeCheckError,EthicalError,ParserError,LexerError,CodegenError,RuntimeError) as error:
  print(f"[YADRO] Compilation error: {error}");sys.exit(1)
 print("[YADRO] Compilation complete. Code is law.")

if __name__=="__main__":main_cli()
