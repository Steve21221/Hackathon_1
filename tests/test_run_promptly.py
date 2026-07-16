import os
import socket
import unittest
from unittest.mock import patch

import run_promptly


class RunPromptlyTestCase(unittest.TestCase):
    def test_requested_port_uses_default_for_invalid_value(self):
        with patch.dict(os.environ, {"PROMPTLY_PORT": "not-a-port"}):
            self.assertEqual(run_promptly.requested_port(), run_promptly.DEFAULT_PORT)

    def test_find_available_port_skips_a_port_that_is_in_use(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind((run_promptly.HOST, 0))
            occupied.listen()
            occupied_port = occupied.getsockname()[1]

            if occupied_port == 65_535:
                self.skipTest("No higher port is available for this test.")

            selected_port = run_promptly.find_available_port(occupied_port, attempts=2)

        self.assertEqual(selected_port, occupied_port + 1)


if __name__ == "__main__":
    unittest.main()
