import io,json,platform,statistics,tempfile,time
from pathlib import Path
from src.main import compile
from src.lexer import Lexer
from src.syntax import Parser
from src.ethics import EthicalAnalyzer
from src.mcp_guard import run as run_mcp

SOURCE='''fn helper(x) { if x > 2 { return x * 2 } else { return x + 1 } } fn main() { let n = 7 while n < 9 { n = n + 1 } return helper(n) }'''
ETHICS='''fn helper(x) { return x + 1 } fn main() { let p = user.data() let q = anonymize(p) return helper(q) }'''
MCP={"version":"1.0","tools":[{"name":"crm.read","labels":["PII"]},{"name":"privacy.redact","sanitizes":["PII"]},{"name":"net.send","capabilities":["NetworkAccess"]}],"flows":[["crm.read","privacy.redact"],["privacy.redact","net.send"]]}

def measure(fn,rounds):
 values=[]
 for _ in range(rounds):
  start=time.perf_counter_ns();fn();values.append((time.perf_counter_ns()-start)/1_000_000)
 return {"median_ms":round(statistics.median(values),4),"p95_ms":round(sorted(values)[int(len(values)*.95)-1],4),"rounds":rounds}

def analyze():
 ast=Parser(Lexer(ETHICS).tokens()).parse();EthicalAnalyzer().check(ast)

def mcp():
 path=Path(tempfile.gettempdir())/'yadro-benchmark-mcp.json';path.write_text(json.dumps(MCP));run_mcp(['scan',str(path)],io.StringIO(),io.StringIO())

result={"schema":"yadro-benchmark-1.0","python":platform.python_version(),"platform":platform.platform(),"compile":measure(lambda:compile(SOURCE),40),"ethical_analysis":measure(analyze,80),"mcp_scan":measure(mcp,120)}
print(json.dumps(result,indent=2,sort_keys=True))
