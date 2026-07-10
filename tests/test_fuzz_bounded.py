import random
import string
import unittest
from src.lexer import Lexer, LexerError
from src.syntax import Parser, ParserError

class BoundedFuzzTests(unittest.TestCase):
 def test_deterministic_lexer_corpus(self):
  rng=random.Random(20260710);alphabet=string.ascii_letters+string.digits+' _#\n{}()[],+-*/<>=\".Жя'
  for _ in range(300):
   text=''.join(rng.choice(alphabet) for _ in range(rng.randrange(0,160)))
   try:Lexer(text).tokens()
   except (LexerError,ValueError,IndexError):pass
 def test_parser_progress_on_malformed_corpus(self):
  corpus=['fn main( {','fn main() {','fn main() { return (1 + 2 }','fn main() { let x = "unterminated','fn '*200]
  for text in corpus:
   try:Parser(Lexer(text).tokens()).parse()
   except (LexerError,ParserError,ValueError,IndexError,RecursionError):pass

if __name__=='__main__':unittest.main()
