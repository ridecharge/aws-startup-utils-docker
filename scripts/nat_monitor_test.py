#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock
import logging
import nat_monitor
import utils


class NatInstanceTest(unittest.TestCase):

    def setUp(self):
        self.vpc_conn = MagicMock()
        self.ec2_conn = MagicMock()
        self.instance_id = 'i-abc123'
        self.subnet = MagicMock()
        self.subnet.id = 'subnetid'
        self.route_table = MagicMock()
        self.route_table.id = 'rt-123'
        self.vpc_conn.get_all_subnets = MagicMock(return_value=[self.subnet])
        self.vpc_conn.get_all_route_tables = MagicMock(
            return_value=[self.route_table])
        self.vpc_conn.create_route = MagicMock()
        self.vpc_id = 'vpc123'
        self.az = 'us-east-1a'
        self.logger = utils.build_logger(
            NatInstanceTest.__name__, 'abc123', [self.instance_id])
        self.logger.setLevel(logging.ERROR)
        self.instance = MagicMock()
        self.role = 'nat'
        self.instance.tags = {
            'Role': self.role, 'Name': NatInstanceTest.__name__}
        self.instance_tags = MagicMock()
        self.name = 'name'
        self.instance_tags.get_name = MagicMock(return_value=self.name)
        self.instances = [self.instance]
        self.ec2_conn.get_only_instances = MagicMock(
            return_value=self.instances)
        self.ec2_conn.modify_instance_attribute = MagicMock()
        self.instance_metadata = {
            'instance-id': self.instance_id,
            'network': {
                'interfaces': {
                    'macs': {
                        '0e:bf:0c:a1:f6:59': {
                            'vpc-id': self.vpc_id
                        }
                    }
                }
            },
            'placement': {
                'availability-zone': self.az
            }
        }

        self.nat_instance = nat_monitor.NatInstance(
            self.vpc_conn, self.ec2_conn, self.instance_tags, self.instance_metadata, self.logger)

    def test_init(self):
        self.assertEqual(self.nat_instance.vpc_conn, self.vpc_conn)
        self.assertEqual(self.nat_instance.ec2_conn, self.ec2_conn)
        self.assertEqual(self.nat_instance.vpc_id, self.vpc_id)
        self.assertEqual(self.nat_instance.az, self.az)
        self.assertEqual(self.nat_instance.instance_id, self.instance_id)
        self.assertEqual(
            self.nat_instance.my_route_table_id, self.route_table.id)
        self.assertEqual(
            self.nat_instance.take_over_route_table_id, self.route_table.id)
        self.assertEqual(self.nat_instance.logger, self.logger)
        self.assertEqual(self.nat_instance.name_tag, self.name)

    def test_disable_source_dest_check(self):
        self.nat_instance.disable_source_dest_check()
        self.ec2_conn.modify_instance_attribute.assert_called_with(
            self.instance_id, 'sourceDestCheck', False)

    def test_set_route(self):
        self.nat_instance.set_route()
        self.vpc_conn.create_route.assert_called_with(
            self.nat_instance.my_route_table_id, '0.0.0.0/0', instance_id=self.nat_instance.instance_id)

    def test_take_over_route(self):
        self.nat_instance.take_over_route()
        self.vpc_conn.create_route.assert_called_with(
            self.route_table.id, '0.0.0.0/0', instance_id=self.instance_id)

    def test_restore_taken_over_route(self):
        self.nat_instance.restore_taken_over_route(self.instance_id)
        self.vpc_conn.create_route.assert_called_with(
            self.route_table.id, '0.0.0.0/0', instance_id=self.instance_id)


class NatMonitorTest(unittest.TestCase):

    def setUp(self):
        self.elb_conn = MagicMock()
        self.elb_conn.describe_instance_health = MagicMock(return_value=[])
        self.instance = MagicMock()
        self.instance.take_over_route = MagicMock()
        self.instance_id = 'i-abc123'
        self.other_instance_id = 'i-123abc'
        self.logger = utils.build_logger(
            NatMonitorTest.__name__, 'abc123', [self.instance_id])
        self.logger.setLevel(logging.ERROR)
        self.allow_take_over_monitor = nat_monitor.NatMonitor(
            self.elb_conn, self.instance, self.logger)
        self.allow_take_over_monitor.allow_take_over = True
        self.allow_take_over_monitor.other_instance_id = self.other_instance_id
        self.check_instance_monitor = nat_monitor.NatMonitor(
            self.elb_conn, self.instance, self.logger)
        self.other_health_out_of_service = MagicMock()
        self.other_health_out_of_service.state = 'OutOfService'
        self.other_health_out_of_service.instance_id = self.other_instance_id
        self.other_health_in_of_service = MagicMock()
        self.other_health_in_of_service.state = 'InService'
        self.other_health_in_of_service.instance_id = self.other_instance_id

    def test_init(self):
        self.assertEqual(self.check_instance_monitor.elb_conn, self.elb_conn)
        self.assertEqual(self.check_instance_monitor.logger, self.logger)
        self.assertEqual(
            self.check_instance_monitor.nat_instance, self.instance)
        self.assertFalse(self.check_instance_monitor.allow_take_over)
        self.assertIsNone(self.check_instance_monitor.other_instance_id)

    def test_monitor_allow_take_over_no_instance(self):
        self.allow_take_over_monitor.monitor()
        self.assertFalse(self.allow_take_over_monitor.allow_take_over)
        self.instance.take_over_route.assert_called()

    def test_monitor_allow_take_over_has_instance_not_inservice(self):
        self.elb_conn.describe_instance_health = MagicMock(
            return_value=[self.other_health_out_of_service])
        self.allow_take_over_monitor.monitor()
        self.assertFalse(self.allow_take_over_monitor.allow_take_over)
        self.instance.take_over_route.assert_called()

    def test_monitor_allow_take_over_has_instance_inservice(self):
        self.elb_conn.describe_instance_health = MagicMock(
            return_value=[self.other_health_in_of_service])
        self.allow_take_over_monitor.monitor()
        self.assertTrue(self.allow_take_over_monitor.allow_take_over)
        self.instance.take_over_route.assert_not_called()

    def test_monitor_check_instance_no_instance(self):
        self.check_instance_monitor.monitor()
        self.assertFalse(self.check_instance_monitor.allow_take_over)

    def test_monitor_check_instance_no_instance_inservice(self):
        self.elb_conn.describe_instance_health = MagicMock(
            return_value=[self.other_health_out_of_service])
        self.check_instance_monitor.monitor()
        self.assertFalse(self.check_instance_monitor.allow_take_over)

    def test_monitor_check_instance_new_instance_inservice(self):
        self.elb_conn.describe_instance_health = MagicMock(
            return_value=[self.other_health_in_of_service])
        self.check_instance_monitor.other_instance_id = self.other_instance_id
        self.check_instance_monitor.monitor()
        self.assertTrue(self.check_instance_monitor.allow_take_over)
        self.instance.restore_taken_over_route.assert_called_with(
            self.other_instance_id)

    def test_monitor_check_instance_recovered_instance_inservice(self):
        self.elb_conn.describe_instance_health = MagicMock(
            return_value=[self.other_health_in_of_service])
        self.check_instance_monitor.monitor()
        self.assertTrue(self.check_instance_monitor.allow_take_over)
        self.instance.restore_taken_over_route.assert_not_called()


if __name__ == '__main__':
    unittest.main()
