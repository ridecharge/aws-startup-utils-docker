#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock
import logging
import attach_eni
import common


class CommonTest(unittest.TestCase):

    def setUp(self):
        self.logger_name = CommonTest.__name__
        self.instance_id = 'i-abc123'
        self.loggly_token = 'abc123'
        self.role = 'role'
        self.tags = [self.instance_id, self.role]
        self.conn = MagicMock()
        self.instance = MagicMock()
        self.instance.tags = {'Role': self.role, 'Name': self.logger_name,
                              'PublicInternalHostedZone': 'PublicInternalHostedZone',
                              'PublicInternalDomain': 'PublicInternalDomain'}
        self.instances = [self.instance]
        self.conn.get_only_instances = MagicMock(return_value=self.instances)
        self.instance_tags = common.InstanceTags(self.conn, self.instance_id)

    def test_build_logger(self):
        logger = common.build_logger(
            self.logger_name, self.loggly_token, self.tags)
        self.assertEqual(self.logger_name, logger.name)
        self.assertIn(self.loggly_token, logger.handlers[0].url)
        for tag in self.tags:
            self.assertIn(tag, logger.handlers[0].url)

    def test_get_role(self):
        role = self.instance_tags.get_role()
        self.conn.get_only_instances.assert_called_with(self.instance_id)
        self.assertEqual(role, self.role)

    def test_get_name(self):
        name = self.instance_tags.get_name()
        self.conn.get_only_instances.assert_called_with(self.instance_id)
        self.assertEqual(name, self.logger_name)

    def test_public_internal_hosted_zone(self):
        name = self.instance_tags.get_public_internal_hosted_zone()
        self.conn.get_only_instances.assert_called_with(self.instance_id)
        self.assertEqual(name, 'PublicInternalHostedZone')

    def test_public_internal_domain(self):
        name = self.instance_tags.get_public_internal_domain()
        self.conn.get_only_instances.assert_called_with(self.instance_id)
        self.assertEqual(name, 'PublicInternalDomain')

if __name__ == '__main__':
    unittest.main()
