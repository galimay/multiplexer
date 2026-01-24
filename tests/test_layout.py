import unittest
from unittest.mock import Mock
from multiplexer.layout import LayoutManager
from multiplexer.pane import Pane


class TestLayoutManager(unittest.TestCase):

    def setUp(self):
        self.terminal = Mock()
        self.terminal.width = 80
        self.terminal.height = 24
        self.layout_manager = LayoutManager(self.terminal)

    def test_single_pane_layout(self):
        pane = Pane('echo test', self.terminal)
        self.layout_manager.update_layout([pane])
        self.assertEqual(pane.x, 0)
        self.assertEqual(pane.y, 0)
        self.assertEqual(pane.width, 80)
        self.assertEqual(pane.height, 24)

    def test_two_pane_layout(self):
        pane1 = Pane('echo test1', self.terminal)
        pane2 = Pane('echo test2', self.terminal)
        self.layout_manager.update_layout([pane1, pane2])
        self.assertEqual(pane1.x, 0)
        self.assertEqual(pane1.y, 0)
        self.assertEqual(pane1.width, 40)
        self.assertEqual(pane1.height, 24)
        self.assertEqual(pane2.x, 40)
        self.assertEqual(pane2.y, 0)
        self.assertEqual(pane2.width, 40)
        self.assertEqual(pane2.height, 24)


if __name__ == '__main__':
    unittest.main()