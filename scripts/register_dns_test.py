#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock
import logging
import boto
import register_dns


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
        self.record_sets = boto.route53.record.ResourceRecordSets(self.conn, self.hosted_zone)
        self.logger = register_dns.build_logger(self.logger_name, self.instance_id, self. role)
        self.logger.setLevel(logging.ERROR)
        self.registration = register_dns.DnsRegistration(self.record_sets,
                                                         self.role,
                                                         self.az,
                                                         self.hosted_zone_name,
                                                         self.ip,
                                                         self.logger)

    def test_build_logger(self):
        self.assertEqual(self.logger.name, self.logger_name)
        self.assertIn(self.instance_id, self.logger.handlers[0].url)

    def test_dns_registration_init(self):
        self.assertEqual(self.record_sets, self.registration.record_sets)
        self.assertEqual(self.record, self.registration.record)
        self.assertEqual(self.ip, self.registration.ip)
        self.assertEqual(self.logger, self.registration.logger)

    def test_dns_registration_register(self):
        change = MagicMock()
        record_sets = MagicMock()
        record_sets.add_change = MagicMock(return_value=change)
        self.registration.record_sets = record_sets
        self.registration.register()
        record_sets.add_change.assert_called_with('UPSERT', self.registration.record, 'A')
        change.add_value.assert_called_with(self.ip)
        record_sets.commit.assert_called()


if __name__ == '__main__':
    unittest.main()
