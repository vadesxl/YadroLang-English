from src.typesys import TypeChecker,TypeCheckError
class SoundTypeChecker(TypeChecker):
 def _function(self,function):
  signature=self.signatures[function.name];env=dict(zip(function.parameters,signature["params"]));returns=[];terminated=self._body(function.body,env,returns)
  for value,line in returns:signature["return"]=self._merge(signature["return"],value,line,f"return type of '{function.name}'")
  if function.name!="main" and not terminated:raise TypeCheckError(f"function '{function.name}' does not return on every path",function.string,"YADRO-T2204")
