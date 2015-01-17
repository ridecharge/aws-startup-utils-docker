#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock
import logging
import attach_eni


class NetworkInterfaceAttachmentTest(unittest.TestCase):
    def setUp(self):
        self.logger_name = NetworkInterfaceAttachmentTest.__name__
        self.instance_id = 'i-abc123'
        self.role = 'ntp'
        self.logger = attach_eni.build_logger(self.logger_name, self.instance_id, self.role)
        self.logger.setLevel(logging.ERROR)

    def test_build_logger(self):
        self.assertEqual(self.logger.name, self.logger_name)
        self.assertIn(self.instance_id, self.logger.handlers[0].url)
        self.assertIn(self.role, self.logger.handlers[0].url)


if __name__ == '__main__':
    unittest.main()
