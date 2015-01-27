#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock
import logging
import attach_eni
import os

os.environ["LOGGLY_TOKEN"] = "abc"
class NetworkInterfaceAttachmentTest(unittest.TestCase):
    def setUp(self):
        self.logger_name = NetworkInterfaceAttachmentTest.__name__
        self.instance_id = 'i-abc123'
        self.subnet_id = 'subnet-abc123'
        self.role = 'ntp'
        self.device_index = 2
        self.conn = MagicMock()
        self.logger = attach_eni.build_logger(self.logger_name, self.instance_id, self.role)
        self.logger.setLevel(logging.ERROR)
        self.network_attachment = attach_eni.NetworkInterfaceAttachment(self.conn, self.logger,
                                                                        self.role,
                                                                        self.subnet_id,
                                                                        self.instance_id,
                                                                        self.device_index)
        self.network_interface = MagicMock()
        self.network_interface.attach = MagicMock()
        self.conn.get_all_network_interfaces = MagicMock(return_value=[self.network_interface])

    def test_build_logger(self):
        self.assertEqual(self.logger.name, self.logger_name)
        self.assertIn(self.instance_id, self.logger.handlers[0].url)
        self.assertIn(self.role, self.logger.handlers[0].url)

    def test_init(self):
        self.assertEqual(self.network_attachment.conn, self.conn)
        self.assertEqual(self.network_attachment.logger, self.logger)
        self.assertEqual(self.network_attachment.role, self.role)
        self.assertEqual(self.network_attachment.subnet_id, self.subnet_id)
        self.assertEqual(self.network_attachment.instance_id, self.instance_id)
        self.assertEqual(self.network_attachment.device_index, self.device_index)

    def test_find_network_interface(self):
        network_interface = self.network_attachment.find_network_interface()
        self.assertEqual(network_interface, self.network_interface)
        self.conn.get_all_network_interfaces.assert_called_with(
            filters={'tag:Role': self.role, 'subnet-id': self.subnet_id})

    def test_attach(self):
        self.network_attachment.attach()
        self.network_interface.attach.assert_called_with(self.instance_id, self.device_index)


if __name__ == '__main__':
    unittest.main()
