#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock
import logging
import attach_eni
import utils


class NetworkInterfaceAttachmentTest(unittest.TestCase):
    def setUp(self):
        self.logger_name = NetworkInterfaceAttachmentTest.__name__
        self.instance_id = 'i-abc123'
        self.subnet_id = 'subnet-abc123'
        self.role = 'ntp'
        self.device_index = 2
        self.conn = MagicMock()
        self.instance_metadata = {
            'instance-id': self.instance_id,
            'network': {
                'interfaces': {
                    'macs': {
                        'abc123': {
                            'subnet-id': self.subnet_id
                        }
                    }
                }
            }
        }

        self.instance_tags = MagicMock()

        self.instance_tags.get_role = MagicMock(return_value=self.role)

        self.network_attachment = attach_eni.NetworkInterfaceAttachment(self.conn,
                                                                        self.instance_tags,
                                                                        self.instance_metadata,
                                                                        self.device_index)
        self.network_interface = MagicMock()
        self.network_interface.attach = MagicMock()
        self.conn.get_all_network_interfaces = MagicMock(
            return_value=[self.network_interface])

    def test_init(self):
        self.assertEqual(self.network_attachment.ec2_conn, self.conn)
        self.assertEqual(self.network_attachment.role, self.role)
        self.assertEqual(self.network_attachment.subnet_id, self.subnet_id)
        self.assertEqual(self.network_attachment.instance_id, self.instance_id)
        self.assertEqual(
            self.network_attachment.device_index, self.device_index)

    def test_attach(self):
        self.network_attachment.attach()
        self.conn.get_all_network_interfaces.assert_called_with(
            filters={'status': 'available', 'tag:Role': self.role,
                     'subnet-id': self.subnet_id})
        self.network_interface.attach.assert_called_with(
            self.instance_id, self.device_index)


if __name__ == '__main__':
    unittest.main()
