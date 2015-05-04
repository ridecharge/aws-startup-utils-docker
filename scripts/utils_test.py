#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock
import utils


class UtilsTest(unittest.TestCase):
    def setUp(self):
        self.logger_name = UtilsTest.__name__
        self.instance_id = 'i-abc123'
        self.role = 'role'
        self.tags = [self.instance_id, self.role]
        self.conn = MagicMock()
        self.instance = MagicMock()
        self.instance.tags = {'Role': self.role, 'Name': self.logger_name}
        self.instances = [self.instance]
        self.conn.get_only_instances = MagicMock(return_value=self.instances)
        self.instance_tags = utils.InstanceTags(self.conn, self.instance_id)

    def test_get_role(self):
        role = self.instance_tags.get_role()
        self.conn.get_only_instances.assert_called_with(self.instance_id)
        self.assertEqual(role, self.role)

    def test_get_name(self):
        name = self.instance_tags.get_name()
        self.conn.get_only_instances.assert_called_with(self.instance_id)
        self.assertEqual(name, self.logger_name)


if __name__ == '__main__':
    unittest.main()
