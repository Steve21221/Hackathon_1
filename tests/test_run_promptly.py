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

    def test_monitor_shuts_down_after_last_tab_closes(self):
        shutdown_calls = []
        monitor = run_promptly.BrowserSessionMonitor(
            lambda: shutdown_calls.append("shutdown"),
            close_grace_seconds=3,
            heartbeat_timeout_seconds=90,
        )

        monitor.notify("heartbeat", "tab_one", 1, now=10)
        monitor.notify("close", "tab_one", 2, now=12)

        self.assertFalse(monitor.check(now=14.9))
        self.assertTrue(monitor.check(now=15))
        self.assertEqual(shutdown_calls, ["shutdown"])
        self.assertFalse(monitor.check(now=20))

    def test_monitor_keeps_running_when_navigation_opens_a_new_page(self):
        shutdown_calls = []
        monitor = run_promptly.BrowserSessionMonitor(
            lambda: shutdown_calls.append("shutdown"),
            close_grace_seconds=3,
            heartbeat_timeout_seconds=90,
        )

        monitor.notify("heartbeat", "old_page", 1, now=10)
        monitor.notify("close", "old_page", 2, now=11)
        monitor.notify("heartbeat", "new_page", 1, now=12)

        self.assertFalse(monitor.check(now=20))
        self.assertEqual(shutdown_calls, [])

    def test_monitor_ignores_out_of_order_heartbeat_after_close(self):
        shutdown_calls = []
        monitor = run_promptly.BrowserSessionMonitor(
            lambda: shutdown_calls.append("shutdown"),
            close_grace_seconds=1,
            heartbeat_timeout_seconds=90,
        )

        monitor.notify("close", "tab_race", 2, now=10)
        monitor.notify("heartbeat", "tab_race", 1, now=10.1)

        self.assertTrue(monitor.check(now=11))
        self.assertEqual(shutdown_calls, ["shutdown"])


if __name__ == "__main__":
    unittest.main()
