#!/usr/bin/env python3
import boto.utils
import boto.ec2
import boto.route53
import logging
import loggly.handlers
import sys


class DnsRegistration(object):
    def __init__(self, record_sets, role, az, hosted_zone_name, ip, logger):
        self.record_sets = record_sets
        self.role = role
        self.record = "-".join([role, az, hosted_zone_name]).lower()
        self.logger = logger
        self.ip = ip
        self.logger.info(
            "DnsRegistration init with {0.record_sets.hosted_zone_id} {0.ip}.".format(self))
        self.logger.info("Built dns record {0}".format(self.record))

    def register(self):
        """ Upserts the A record """
        change = self.record_sets.add_change('UPSERT', self.record, 'A')
        change.add_value(self.ip)
        self.record_sets.commit()
        self.logger.info("Successful set {0.ip} to {0.record}.".format(self))


LOGGLY_URL = "https://logs-01.loggly.com/inputs/" + \
             "e8bcd155-264b-4ec0-88be-fcb023f76a89/tag/python,boot,dns,cloudformation"


def build_logger(name, instance_id, role):
    """ Sets up a logger to send files to Loggly with dynamic tags """
    logger = logging.getLogger(name)
    url = ",".join([LOGGLY_URL, instance_id, role])
    handler = loggly.handlers.HTTPSHandler(url)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger


def create_aws_connections(region):
    route53_conn = boto.route53.connect_to_region(region)
    ec2_conn = boto.ec2.connect_to_region(region)
    return ec2_conn, route53_conn


def get_role(ec2_conn, instance_id):
    return ec2_conn.get_only_instances(instance_id)[0].tags['Role'].lower()


def main(hosted_zone_id, hosted_zone_name):
    instance_metadata = boto.utils.get_instance_metadata()
    az = instance_metadata['placement']['availability-zone']
    region = boto.utils.get_instance_identity()['document']['region']
    instance_id = instance_metadata['instance-id']

    ec2_conn, route53_conn = create_aws_connections(region)

    role = get_role(ec2_conn, instance_id)
    record_sets = boto.route53.record.ResourceRecordSets(route53_conn, hosted_zone_id)
    logger = build_logger(DnsRegistration.__name__, instance_id, role)
    try:
        DnsRegistration(
            record_sets, role, az, hosted_zone_name,
            instance_metadata['local-ipv4'],
            logger
        ).register()
    except:
        logger.exception('Error Registering DNS')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
