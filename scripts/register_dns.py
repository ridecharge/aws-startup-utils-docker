#!/usr/bin/env python3
import boto.utils
import boto.ec2
import boto.route53
import utils


class DnsRegistration(object):
    def __init__(self, route53_conn, instance_tags, instance_metadata, logger):
        role = instance_tags.get_role()
        hosted_zone_name = instance_tags.get_public_internal_domain()
        hosted_zone_id = instance_tags.get_public_internal_hosted_zone()
        az = instance_metadata['placement']['availability-zone']

        self.records = route53_conn.get_all_rrsets(hosted_zone_id)
        self.record = "-".join([role, az, hosted_zone_name]).lower()
        self.ip = instance_metadata['local-ipv4']
        self.logger = logger

        self.logger.info(
            "DnsRegistration init with {0.ip} {0.record}.".format(self))

    def register(self):
        """ Upserts the A record """
        change = self.records.add_change('UPSERT', self.record, 'A')
        change.add_value(self.ip)
        self.records.commit()
        self.logger.info("Successful set {0.ip} to {0.record}.".format(self))


def create_aws_connections(region):
    route53_conn = boto.route53.connect_to_region(region)
    ec2_conn = boto.ec2.connect_to_region(region)
    return ec2_conn, route53_conn


def main():
    region = boto.utils.get_instance_identity()['document']['region']
    ec2_conn, route53_conn = create_aws_connections(region)

    instance_metadata = boto.utils.get_instance_metadata()
    instance_tags = utils.InstanceTags(ec2_conn, instance_metadata['instance-id'])

    logger = utils.get_logger(
        DnsRegistration.__name__,
        [instance_metadata['instance-id'],
         instance_tags.get_role(),
         instance_tags.get_environment()]
    )

    try:
        DnsRegistration(
            route53_conn,
            instance_tags,
            instance_metadata,
            logger
        ).register()
    except:
        logger.exception('Error Registering DNS')


if __name__ == '__main__':
    main()
