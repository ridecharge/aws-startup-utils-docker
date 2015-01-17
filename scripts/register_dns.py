#!/usr/bin/env python3
import boto.utils
import boto.route53
import logging
import loggly.handlers
import sys


class DnsRegistration(object):
    def __init__(self, record_sets, record, ip, logger):
        self.record_sets = record_sets
        self.record = record
        self.ip = ip
        self.logger = logger
        self.logger.info(
            "DnsRegistration init with {0.record_sets.hosted_zone_id} {0.ip}.".format(self))


    def register(self):
        """ Upserts the A record """
        change = self.record_sets.add_change('UPSERT', self.record, 'A')
        change.add_value(self.ip)
        self.record_sets.commit()
        self.logger.info("Successful set {0.ip} to {0.record}.".format(self))


LOGGLY_URL = "https://logs-01.loggly.com/inputs/" + \
             "e8bcd155-264b-4ec0-88be-fcb023f76a89/tag/python,boot,dns,cloudformation"


def build_logger(name, instance_id):
    """ Sets up a logger to send files to Loggly with dynamic tags """
    logger = logging.getLogger(name)
    url = ",".join([LOGGLY_URL, instance_id])
    handler = loggly.handlers.HTTPSHandler(url)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def main(hosted_zone, record):
    instance_metadata = boto.utils.get_instance_metadata()
    region = boto.utils.get_instance_identity()['document']['region']
    conn = boto.route53.connect_to_region(region)
    record_sets = boto.route53.record.ResourceRecordSets(conn, hosted_zone)

    logger = build_logger(DnsRegistration.__name__, instance_metadata['instance-id'])
    try:
        DnsRegistration(
            record_sets,
            record,
            instance_metadata['local-ipv4'],
            logger
        ).register()
    except:
        logger.exception('Error Registering DNS')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
