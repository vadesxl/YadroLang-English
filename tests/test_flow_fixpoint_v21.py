import unittest
from src.main import compile
from src.ethics import EthicalError


class FlowFixpointTests(unittest.TestCase):
    def test_zero_iteration_loop_state_is_joined(self):
        source = """
        fn main() requires [NetworkAccess] {
          let value = 0
          while value { value = user.data() }
          return net.send(value)
        }
        """
        with self.assertRaisesRegex(EthicalError, "PII"):
            compile(source)

    def test_branch_state_is_joined_after_if(self):
        source = """
        fn main() requires [NetworkAccess] {
          let value = 0
          if 1 { value = env.secret() }
          return net.send(value)
        }
        """
        with self.assertRaisesRegex(EthicalError, "Credentials"):
            compile(source)


if __name__ == "__main__":
    unittest.main()
