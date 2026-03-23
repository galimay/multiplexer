import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from multiplexer.pane import Pane


class TestPane(unittest.TestCase):

    def setUp(self):
        self.terminal = Mock()
        self.pane = Pane("echo test", self.terminal, 0, 0, 80, 24)

    def test_pane_initialization(self):
        self.assertEqual(self.pane.command, "echo test")
        self.assertEqual(self.pane.x, 0)
        self.assertEqual(self.pane.y, 0)
        self.assertEqual(self.pane.width, 80)
        self.assertEqual(self.pane.height, 24)
        self.assertIsNone(self.pane.process)
        self.assertEqual(self.pane.output, [])
        self.assertEqual(self.pane.input_buffer, "")

    def test_content_dimensions(self):
        pane = Pane("cmd", self.terminal, 0, 0, 40, 12)
        self.assertEqual(pane.content_width, 38)  # width - 2
        self.assertEqual(pane.content_height, 9)  # height - 3

    def test_content_height_minimum(self):
        pane = Pane("cmd", self.terminal, 0, 0, 10, 3)
        self.assertEqual(pane.content_height, 0)

    def test_output_trimmed_to_content_height(self):
        """Output buffer must not exceed content_height lines."""

        async def run_test():
            lines = [f"line{i}\n".encode() for i in range(30)] + [b""]
            with patch("multiplexer.pane.asyncio.create_subprocess_shell") as mc:
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.stdout = AsyncMock()
                mock_process.stdout.readline = AsyncMock(side_effect=lines)
                mc.return_value = mock_process
                await self.pane.start()
                await asyncio.sleep(0.2)
            self.assertLessEqual(len(self.pane.output), self.pane.content_height)

        asyncio.run(run_test())

    @patch("multiplexer.pane.asyncio.create_subprocess_shell")
    def test_start_and_stop(self, mock_create):
        async def run_test():
            mock_process = MagicMock()
            mock_create.return_value = mock_process
            mock_process.stdout = AsyncMock()
            mock_process.stdout.readline = AsyncMock(side_effect=[b"output\n", b""])
            await self.pane.start()
            await asyncio.sleep(0.1)  # Allow task to run
            await self.pane.stop()
            mock_create.assert_called_once()

        asyncio.run(run_test())

    @patch("multiplexer.pane.asyncio.create_subprocess_shell")
    def test_pane_finished(self, mock_create):
        async def run_test():
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.stdout = AsyncMock()
            mock_process.stdout.readline = AsyncMock(side_effect=[b"output\n", b""])
            mock_create.return_value = mock_process
            await self.pane.start()
            await asyncio.sleep(0.1)  # Allow task to run
            self.assertTrue(self.pane.finished)
            self.assertEqual(self.pane.exit_code, 0)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
