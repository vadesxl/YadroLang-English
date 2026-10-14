from src.proof_seal import *
ZERO="0"*64
ONE="1"*64
def minimal_core():
 compiler=CompilerIdentity("yadro-guard","2.1.0","en","1.0")
 subject=SubjectBinding(POLICY_VERSION,LLVM_NORMALIZATION_VERSION,ZERO,ZERO,ZERO,ZERO,"x86_64-unknown-linux-gnu","elf-object")
 return ProofSealCore(compiler,subject,make_analysis())
def rich_core(order=False):
 assumption=make_assumption("yadro_ext_v1_send","i64(i64)","NetworkAccess","identity",False,"call",True)
 span=SourceSpan("src/example.yad",1,4,0);mid=module_id("en",b"source")
 values=("PII","Health") if order else ("Health","PII")
 call=make_call_site("en",mid,"call","caller","callee",span,required_capabilities=("NetworkAccess",),incoming_labels=values,assumption_ids=(assumption.id,),reachable_entries=("entry",))
 compiler=CompilerIdentity("yadro-guard","2.1.0","en","1.0")
 subject=SubjectBinding(POLICY_VERSION,LLVM_NORMALIZATION_VERSION,ZERO,ONE,ZERO,ONE,"x86_64-pc-windows-msvc","coff-object")
 lattice=canonical_strings(values,"lattice_labels")
 return ProofSealCore(compiler,subject,make_analysis(("entry",),(call,),(assumption,),FixpointEvidence("bounded-monotone-1.0",lattice,1,5)))
