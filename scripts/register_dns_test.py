#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock
import logging
import boto
import register_dns
import utils


class DnsRegistrationTest(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.hosted_zone = 'ASAFSDF1231231'
        self.instance_id = 'i-abc123'
        self.logger_name = 'name'
        self.ip = '1.1.1.1'
        self.role = 'dns'
        self.az = 'us-east-1a'
        self.hosted_zone_name = 'test.gc'
        self.record = "-".join([self.role, self.az, self.hosted_zone_name])

        self.logger = utils.build_logger(
            self.logger_name, 'abc123', [self.instance_id, self.role])
        self.logger.setLevel(logging.ERROR)

        self.tags = MagicMock()
        self.tags.get_public_internal_domain = MagicMock(return_value=self.hosted_zone_name)
        self.tags.get_public_internal_hosted_zone = MagicMock(return_value=self.hosted_zone)
        self.tags.get_role = MagicMock(return_value=self.role)

        self.metadata = {'local-ipv4': self.ip,
                         'instance-id': self.instance_id,
                         'placement': {'availability-zone': self.az}}

        self.registration = register_dns.DnsRegistration(self.conn,
                                                         self.tags,
                                                         self.metadata,
                                                         self.logger)

    def test_dns_registration_init(self):
        self.conn.get_all_rrsets.assert_called_once_with(self.hosted_zone, 'A')
        self.assertEqual(self.record, self.registration.record)
        self.assertEqual(self.ip, self.registration.ip)
        self.assertEqual(self.logger, self.registration.logger)

    def test_dns_registration_register(self):
        change = MagicMock()
        records = MagicMock()
        records.add_change = MagicMock(return_value=change)
        self.registration.records = records
        self.registration.register()
        records.add_change.assert_called_with(
            'UPSERT', self.registration.record, 'A')
        change.add_value.assert_called_with(self.ip)
        records.commit.assert_called()


if __name__ == '__main__':
    unittest.main()
