# -*- coding: utf-8 -*-
"""Commercial Yadro Guard source scanner CLI implementation."""
import argparse,json,re,sys
from pathlib import Path
from src import main as compiler
from src.lexer import Lexer,LexerError
from src.syntax import Parser,ParserError
from src.ethics import EthicalAnalyzer,EthicalError
from src import ethics_v21 as runtime
from src.version import VERSION
EXIT_OK,EXIT_POLICY,EXIT_SOURCE,EXIT_INTERNAL=0,2,3,4
KNOWN_LABELS=frozenset(runtime.ALL_LABELS)
_BASE_SOURCES=dict(runtime.SOURCES);_BASE_SINKS=dict(runtime.SINKS);_BASE_SANITIZERS=set(runtime.SANITIZERS);_BASE_COMPLIANCE={k:set(v) for k,v in runtime.COMPLIANCE.items()};_BASE_ARITY=dict(compiler.SYSTEM_API_ARITY)
class PolicyError(ValueError):pass
def reset_policy():
 runtime.SOURCES.clear();runtime.SOURCES.update(_BASE_SOURCES);runtime.SINKS.clear();runtime.SINKS.update(_BASE_SINKS);runtime.SANITIZERS.clear();runtime.SANITIZERS.update(_BASE_SANITIZERS);runtime.COMPLIANCE.clear();runtime.COMPLIANCE.update({k:set(v) for k,v in _BASE_COMPLIANCE.items()});compiler.SYSTEM_API_ARITY.clear();compiler.SYSTEM_API_ARITY.update(_BASE_ARITY);compiler.SYSTEM_API=set(compiler.SYSTEM_API_ARITY)
def load_policy(path):
 data=json.loads(Path(path).read_text(encoding="utf-8"));allowed={"version","sources","sinks","sanitizers"};unknown=set(data)-allowed
 if unknown:raise PolicyError(f"unknown policy fields: {sorted(unknown)}")
 if data.get("version")!="1.0":raise PolicyError("policy.version must be '1.0'")
 for key in ("sources","sinks","sanitizers"):
  if key in data and not isinstance(data[key],dict):raise PolicyError(f"policy.{key} must be an object")
 for name,label in data.get("sources",{}).items():
  if label not in KNOWN_LABELS or name in _BASE_SOURCES|_BASE_SINKS|{x:None for x in _BASE_SANITIZERS}:raise PolicyError(f"invalid or colliding source: {name}")
 for name,cap in data.get("sinks",{}).items():
  if not isinstance(cap,str) or not cap or name in _BASE_SOURCES|_BASE_SINKS|{x:None for x in _BASE_SANITIZERS}:raise PolicyError(f"invalid or colliding sink: {name}")
 for name,labels in data.get("sanitizers",{}).items():
  if not isinstance(labels,list) or not set(labels)<=KNOWN_LABELS or name in _BASE_SOURCES|_BASE_SINKS|{x:None for x in _BASE_SANITIZERS}:raise PolicyError(f"invalid or colliding sanitizer: {name}")
 return data
def apply_policy(data):
 reset_policy();runtime.SOURCES.update(data.get("sources",{}));runtime.SINKS.update(data.get("sinks",{}))
 for name,labels in data.get("sanitizers",{}).items():
  runtime.SANITIZERS.add(name)
  for label in labels:runtime.COMPLIANCE.setdefault(label,set()).add(name)
 compiler.SYSTEM_API_ARITY.update({n:0 for n in data.get("sources",{})});compiler.SYSTEM_API_ARITY.update({n:1 for n in data.get("sinks",{})});compiler.SYSTEM_API_ARITY.update({n:1 for n in data.get("sanitizers",{})});compiler.SYSTEM_API=set(compiler.SYSTEM_API_ARITY)
def diagnostic(error,path):
 text=str(error);match=re.search(r"line (\d+)",text);return {"tool":"yadro-guard","version":VERSION,"path":str(Path(path).resolve()),"code":getattr(error,"code","YADRO-SOURCE"),"line":int(match.group(1)) if match else 1,"message":text}
def sarif(item=None):
 rules=[];results=[]
 if item:rules=[{"id":item["code"],"name":item["code"]}];results=[{"ruleId":item["code"],"level":"error","message":{"text":item["message"]},"locations":[{"physicalLocation":{"artifactLocation":{"uri":Path(item["path"]).as_uri()},"region":{"startLine":item["line"]}}}]}]
 return {"$schema":"https://json.schemastore.org/sarif-2.1.0.json","version":"2.1.0","runs":[{"tool":{"driver":{"name":"Yadro Guard","version":VERSION,"rules":rules}},"results":results}]}
def emit(value,fmt,stream):
 if fmt=="json":print(json.dumps(value,ensure_ascii=False,indent=2),file=stream)
 elif fmt=="sarif":print(json.dumps(sarif(value if "message" in value else None),ensure_ascii=False,indent=2),file=stream)
 else:print(f'{value["path"]}:{value["line"]}: {value["message"]}' if "message" in value else value,file=stream)
def prepare(args):
 reset_policy()
 if getattr(args,"policy",None):apply_policy(load_policy(args.policy))
 return Path(args.source).read_text(encoding="utf-8")
def classify(error):
 if isinstance(error,EthicalError):return EXIT_POLICY
 if isinstance(error,(OSError,UnicodeError,json.JSONDecodeError,PolicyError,compiler.EntryPointError,compiler.SemanticError,ParserError,LexerError)):return EXIT_SOURCE
 return EXIT_INTERNAL
def execute(args,stdout):
 source=prepare(args)
 if args.command=="scan":compiler.compile(source);emit({"status":"ok","path":str(Path(args.source).resolve()),"version":VERSION},args.format,stdout)
 elif args.command=="compile":
  ir=compiler.compile(source,emit_ir=args.ir)
  if not args.ir:compiler.build_native(ir,args.output)
 else:
  ast=Parser(Lexer(source).tokens()).parse();compiler._check_unique_functions(ast);compiler._check_entry_point(ast);compiler._check_calls(ast);compiler._check_expressions(ast);analyzer=EthicalAnalyzer();analyzer.check(ast)
  emit({"status":"ok","findings":[entry.__dict__ for entry in analyzer.audit_trail]},args.format,stdout) if args.format!="text" else print(analyzer.generate_audit_report(),file=stdout)
def parser():
 root=argparse.ArgumentParser(prog="yadro-guard");root.add_argument("--version",action="store_true");sub=root.add_subparsers(dest="command");common=argparse.ArgumentParser(add_help=False);common.add_argument("source");common.add_argument("--policy");common.add_argument("--format",choices=("text","json","sarif"),default="text");sub.add_parser("scan",parents=[common]);cp=sub.add_parser("compile",parents=[common]);cp.add_argument("-o","--output",default="kernel.o");cp.add_argument("--ir",action="store_true");sub.add_parser("audit",parents=[common]);pp=sub.add_parser("policy");ps=pp.add_subparsers(dest="policy_command",required=True);check=ps.add_parser("check");check.add_argument("path");sub.add_parser("version");return root
def run(argv=None,stdout=sys.stdout,stderr=sys.stderr):
 args=parser().parse_args(argv)
 if args.version or args.command=="version":print(VERSION,file=stdout);return EXIT_OK
 if not args.command:parser().print_help(stderr);return EXIT_SOURCE
 if args.command=="policy":
  try:load_policy(args.path);print(f"valid policy: {args.path}",file=stdout);return EXIT_OK
  except Exception as error:print(f"invalid policy: {error}",file=stderr);return classify(error)
 try:execute(args,stdout);return EXIT_OK
 except BrokenPipeError:return EXIT_OK
 except Exception as error:emit(diagnostic(error,args.source),args.format,stderr);return classify(error)
 finally:reset_policy()
def main():raise SystemExit(run())
