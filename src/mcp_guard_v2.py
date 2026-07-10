# -*- coding: utf-8 -*-
"""Resource-bounded deterministic scanner for Yadro Guard MCP schema v1.0."""
import argparse,json,sys
from collections import deque
from pathlib import Path

EXIT_OK,EXIT_POLICY,EXIT_SOURCE,EXIT_INTERNAL=0,2,3,4
LABELS=frozenset({"PII","Financial","Health","Credentials","Location"})
CAPABILITIES=frozenset({"NetworkAccess","DiskWrite","DatabaseWrite","DatabaseRead","ToolExecution","SecretAccess","LogAccess"})
ROOT_KEYS=frozenset({"version","tools","flows","policy"});TOOL_KEYS=frozenset({"name","labels","sanitizes","capabilities"});POLICY_KEYS=frozenset({"privileged_capabilities","max_capabilities_per_tool"})
MAX_BYTES=1_048_576;MAX_TOOLS=500;MAX_FLOWS=10_000;MAX_NAME=128;MAX_VALUES=32;MAX_FINDINGS=MAX_TOOLS*2
class ManifestError(ValueError):pass

def _reject_unknown(mapping,allowed,where):
 unknown=sorted(set(mapping)-allowed)
 if unknown:raise ManifestError(f"unknown {where} field(s): {', '.join(unknown)}")
def _string_set(value,allowed,where):
 if not isinstance(value,list) or len(value)>MAX_VALUES or not all(isinstance(item,str) for item in value):raise ManifestError(f"{where} must be a string array with at most {MAX_VALUES} items")
 if len(value)!=len(set(value)):raise ManifestError(f"duplicate value in {where}")
 result=set(value)
 if not result<=allowed:raise ManifestError(f"unknown value in {where}: {', '.join(sorted(result-allowed))}")
 return result
def _load_json(path):
 raw=Path(path).read_bytes()
 if len(raw)>MAX_BYTES:raise ManifestError(f"manifest is too large (max {MAX_BYTES} bytes)")
 return json.loads(raw.decode("utf-8"))

def load(path):
 data=_load_json(path)
 if not isinstance(data,dict):raise ManifestError("manifest root must be an object")
 _reject_unknown(data,ROOT_KEYS,"manifest")
 if data.get("version")!="1.0" or not isinstance(data.get("tools"),list):raise ManifestError("manifest requires version '1.0' and a tools array")
 if len(data["tools"])>MAX_TOOLS:raise ManifestError(f"too many tools (max {MAX_TOOLS})")
 tools={}
 for raw in data["tools"]:
  if not isinstance(raw,dict):raise ManifestError("every tool must be an object")
  _reject_unknown(raw,TOOL_KEYS,"tool");name=raw.get("name")
  if not isinstance(name,str) or not name.strip() or len(name)>MAX_NAME:raise ManifestError(f"every tool requires a non-empty name of at most {MAX_NAME} characters")
  if name in tools:raise ManifestError(f"duplicate tool: {name}")
  tools[name]={"labels":_string_set(raw.get("labels",[]),LABELS,f"labels on {name}"),"sanitizes":_string_set(raw.get("sanitizes",[]),LABELS,f"sanitizes on {name}"),"capabilities":_string_set(raw.get("capabilities",[]),CAPABILITIES,f"capabilities on {name}")}
 raw_flows=data.get("flows",[])
 if not isinstance(raw_flows,list) or len(raw_flows)>MAX_FLOWS:raise ManifestError(f"flows must be an array with at most {MAX_FLOWS} edges")
 edges=[];seen=set()
 for edge in raw_flows:
  if not isinstance(edge,list) or len(edge)!=2 or not all(isinstance(item,str) for item in edge) or edge[0] not in tools or edge[1] not in tools:raise ManifestError(f"invalid flow edge: {edge!r}")
  pair=(edge[0],edge[1])
  if pair in seen:raise ManifestError(f"duplicate flow edge: {edge!r}")
  seen.add(pair);edges.append(pair)
 policy_raw=data.get("policy",{})
 if not isinstance(policy_raw,dict):raise ManifestError("policy must be an object")
 _reject_unknown(policy_raw,POLICY_KEYS,"policy")
 privileged=_string_set(policy_raw.get("privileged_capabilities",sorted(CAPABILITIES)),CAPABILITIES,"policy privileged_capabilities")
 max_caps=policy_raw.get("max_capabilities_per_tool",3)
 if not isinstance(max_caps,int) or isinstance(max_caps,bool) or not 1<=max_caps<=len(CAPABILITIES):raise ManifestError(f"max_capabilities_per_tool must be between 1 and {len(CAPABILITIES)}")
 return tools,sorted(edges),{"privileged_capabilities":privileged,"max_capabilities_per_tool":max_caps}

def analyze(tools,edges,policy=None):
 policy=policy or {"privileged_capabilities":set(CAPABILITIES),"max_capabilities_per_tool":3}
 state={name:set(tool["labels"]) for name,tool in tools.items()};outgoing={name:[] for name in tools}
 for source,target in edges:outgoing[source].append(target)
 queue=deque(sorted(name for name,labels in state.items() if labels));queued=set(queue);updates=0;bound=max(1,len(tools)*len(LABELS))
 while queue:
  source=queue.popleft();queued.discard(source)
  for target in outgoing[source]:
   merged=state[target]|(state[source]-tools[target]["sanitizes"])
   if merged!=state[target]:
    state[target]=merged;updates+=1
    if updates>bound:raise RuntimeError("MCP graph fixpoint bound exceeded")
    if target not in queued:queue.append(target);queued.add(target)
 incoming={name:0 for name in tools}
 for _,target in edges:incoming[target]+=1
 findings=[];privileged=policy["privileged_capabilities"]
 for name in sorted(tools):
  dangerous=tools[name]["capabilities"]&privileged
  if state[name] and dangerous:findings.append({"code":"YADRO-MCP-2301","severity":"error","tool":name,"labels":sorted(state[name]),"capabilities":sorted(dangerous),"message":f"Sensitive data reaches privileged MCP tool '{name}'"})
  if len(tools[name]["capabilities"])>=policy["max_capabilities_per_tool"]:findings.append({"code":"YADRO-MCP-2401","severity":"error","tool":name,"capabilities":sorted(tools[name]["capabilities"]),"message":f"MCP tool '{name}' has excessive agency"})
 findings.sort(key=lambda item:(item["code"],item["tool"]))
 if len(findings)>MAX_FINDINGS:raise RuntimeError("MCP finding bound exceeded")
 return findings,{"tools":len(tools),"flows":len(edges),"cycles_supported":True,"roots":sorted(name for name,count in incoming.items() if count==0),"unreachable":sorted(name for name,count in incoming.items() if count==0 and not tools[name]["labels"]),"fixpoint_updates":updates}

def sarif(findings,path):
 rules=[{"id":code,"name":code} for code in sorted({item["code"] for item in findings})];results=[{"ruleId":item["code"],"level":item["severity"],"message":{"text":item["message"]},"locations":[{"physicalLocation":{"artifactLocation":{"uri":Path(path).resolve().as_uri()},"region":{"startLine":1}}}]} for item in findings]
 return {"$schema":"https://json.schemastore.org/sarif-2.1.0.json","version":"2.1.0","runs":[{"tool":{"driver":{"name":"Yadro Guard MCP","version":"2.1.0","rules":rules}},"results":results}]}
def run(argv=None,stdout=sys.stdout,stderr=sys.stderr):
 parser=argparse.ArgumentParser(prog="yadro-guard mcp");parser.add_argument("command",choices=("scan",));parser.add_argument("manifest");parser.add_argument("--format",choices=("text","json","sarif"),default="text");parser.add_argument("--quiet",action="store_true");args=parser.parse_args(argv)
 try:findings,summary=analyze(*load(args.manifest))
 except (OSError,UnicodeError,json.JSONDecodeError,ManifestError) as error:print(f"invalid MCP manifest: {error}",file=stderr);return EXIT_SOURCE
 except Exception as error:print(f"internal MCP scanner error: {error}",file=stderr);return EXIT_INTERNAL
 if not args.quiet:
  if args.format=="json":print(json.dumps({"findings":findings,"summary":summary},indent=2),file=stdout)
  elif args.format=="sarif":print(json.dumps(sarif(findings,args.manifest),indent=2),file=stdout)
  else:
   for item in findings:print(f'{item["code"]}: {item["message"]}',file=stdout)
   if not findings:print("MCP tool graph is policy-clean",file=stdout)
 return EXIT_POLICY if findings else EXIT_OK
def main():raise SystemExit(run())
if __name__=="__main__":main()
