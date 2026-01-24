import unittest
from unittest.mock import Mock, patch
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

    @patch('multiplexer.pane.subprocess.Popen')
    def test_start_and_stop(self, mock_popen):
        mock_process = Mock()
        mock_popen.return_value = mock_process
        mock_process.stdout = Mock()
        mock_process.stdout.readline = Mock(side_effect=['output\n', ''])
        self.pane.start()
        self.pane.stop()
        mock_popen.assert_called_once()
        mock_process.terminate.assert_called_once()


if __name__ == '__main__':
    unittest.main()