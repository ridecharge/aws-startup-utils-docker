#!/usr/bin/env python3
import boto
import boto.vpc
import boto.ec2
import boto.utils
import logging
import loggly.handlers


class NatInstance(object):
    TAKE_OVER_AZ = {
        'us-east-1a': 'us-east-1c',
        'us-east-1c': 'us-east-1a',
        'us-west-1a': 'us-west-1b',
        'us-west-1b': 'us-west-1a'
    }

    def __init__(self, vpc_conn, ec2_conn, instance_metadata, logger):
        self.vpc_conn = vpc_conn
        self.ec2_conn = ec2_conn

        self.vpc_id = list(instance_metadata['network']['interfaces']['macs'].values())[0][
            'vpc-id']
        self.az = instance_metadata['placement']['availability-zone']
        self.instance_id = instance_metadata['instance-id']
        self.route_table_id = self.find_route_table_id()
        self.take_over_route_table_id = self.find_takeover_route_table_id()

        self.logger = logger
        self.logger.info(
            "Initialized NatInstance for {0.instance_id} {0.route_table_id}".format(self))

    def find_takeover_route_table_id(self):
        """ Looks up the route table id for the other AZ in the vpc """
        take_over_az = NatInstance.TAKE_OVER_AZ[self.az]
        return find_route_table_id(self.vpc_conn, self.vpc_id, take_over_az)

    def find_route_table_id(self):
        """ Finds the route_table_id for the az our instance is in. """
        return find_route_table_id(self.vpc_conn, self.vpc_id, self.az)

    def update_route(self):
        """ Creates or replaces the route for our NAT instance """
        self.logger.info(
            "Updating Route for {0.instance_id} {0.route_table_id}".format(self))
        update_route(self.vpc_conn, self.route_table_id, self.instance_id)
        self.logger.info(
            "Successfully updated route for {0.instance_id} {0.route_table_id}".format(self))

    def disable_source_dest_check(self):
        """ Sets the sourceDestCheck property on the ec2 instance """
        self.ec2_conn.modify_instance_attribute(self.instance_id, 'sourceDestCheck', False)
        self.logger.info("sourceDestCheck disabled for {0.instance_id}".format(self))

    def monitor(self):
        print('monitoring')


LOGGLY_URL = "https://logs-01.loggly.com/inputs/" + \
             "e8bcd155-264b-4ec0-88be-fcb023f76a89/tag/python,boot,cloudformation"


def build_logger(name, instance_id):
    """ Sets up a logger to send files to Loggly with dynamic tags """
    logger = logging.getLogger(name)
    url = ",".join([LOGGLY_URL, instance_id])
    handler = loggly.handlers.HTTPSHandler(url)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger


def find_route_table_id(vpc_conn, vpc_id, az):
    """ Finds a route table id for a given vpc and az with the tag network:private  """
    subnet_id = vpc_conn.get_all_subnets(
        filters={'vpcId': vpc_id, 'availabilityZone': az, 'tag:network': 'private'})[0].id
    return vpc_conn.get_all_route_tables(filters={'association.subnet-id': subnet_id})[0].id


def update_route(vpc_conn, route_table_id, instance_id):
    try:
        vpc_conn.create_route(route_table_id, '0.0.0.0/0',
                              instance_id=instance_id)
    except boto.exception.EC2ResponseError as err:
        if err.error_code == 'RouteAlreadyExists':
            vpc_conn.replace_route(route_table_id, '0.0.0.0/0',
                                   instance_id=instance_id)
        else:
            raise err


def configure_nat_instance(vpc_conn, ec2_conn, instance_metadata, logger):
    nat_instance = NatInstance(vpc_conn, ec2_conn, instance_metadata, logger)
    nat_instance.disable_source_dest_check()
    nat_instance.update_route()
    return nat_instance


def create_aws_connections(region):
    ec2_conn = boto.ec2.connect_to_region(region)
    vpc_conn = boto.vpc.connect_to_region(region)
    return vpc_conn, ec2_conn


def main():
    # AWS Instance metadata
    region = boto.utils.get_instance_identity()['document']['region']
    instance_metadata = boto.utils.get_instance_metadata()

    vpc_conn, ec2_conn = create_aws_connections(region)

    logger = build_logger(NatInstance.__name__, instance_metadata['instance-id'])
    try:
        nat_instance = configure_nat_instance(vpc_conn, ec2_conn, instance_metadata, logger)
        nat_instance.monitor()
    except:
        logger.exception("Failed to configure NAT and Monitoring")


if __name__ == '__main__':
    main()
