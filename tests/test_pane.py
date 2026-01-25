import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch
from multiplexer.pane import Pane


class TestPane(unittest.TestCase):

    def setUp(self):
        self.terminal = Mock()
        self.pane = Pane('echo test', self.terminal, 0, 0, 80, 24)

    def test_pane_initialization(self):
        self.assertEqual(self.pane.command, 'echo test')
        self.assertEqual(self.pane.x, 0)
        self.assertEqual(self.pane.y, 0)
        self.assertEqual(self.pane.width, 80)
        self.assertEqual(self.pane.height, 24)
        self.assertIsNone(self.pane.process)
        self.assertEqual(self.pane.output, [])

    @patch('multiplexer.pane.asyncio.create_subprocess_shell')
    def test_start_and_stop(self, mock_create):
        async def run_test():
            mock_process = AsyncMock()
            mock_create.return_value = mock_process
            mock_process.stdout = AsyncMock()
            mock_process.stdout.readline = AsyncMock(side_effect=[b'output\n', b''])
            await self.pane.start()
            await self.pane.stop()
            mock_create.assert_called_once()
            mock_process.terminate.assert_called_once()
        asyncio.run(run_test())

    @patch('multiplexer.pane.asyncio.create_subprocess_shell')
    def test_pane_finished(self, mock_create):
        async def run_test():
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.stdout = AsyncMock()
            mock_process.stdout.readline = AsyncMock(side_effect=[b'output\n', b''])
            mock_create.return_value = mock_process
            await self.pane.start()
            await asyncio.sleep(0.1)  # Allow task to run
            self.assertTrue(self.pane.finished)
            self.assertEqual(self.pane.exit_code, 0)
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()