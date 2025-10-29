import unittest

import src.main as mainmod


class TestMainSmoke(unittest.TestCase):
    def test_load_config_returns_dict(self):
        cfg = mainmod.load_config()
        self.assertIsInstance(cfg, dict)


if __name__ == "__main__":
    unittest.main()
