#!/usr/bin/env python3
import boto
import boto.vpc
import boto.ec2
import boto.ec2.elb
import boto.utils
import logging
import utils


class NatInstance(object):
    def __init__(self, vpc_conn, ec2_conn, instance_tags, instance_metadata):
        self.vpc_conn = vpc_conn
        self.ec2_conn = ec2_conn

        self.vpc_id = list(
            instance_metadata['network']['interfaces']['macs'].values())[0]['vpc-id']
        self.az = instance_metadata['placement']['availability-zone']
        self.instance_id = instance_metadata['instance-id']
        self.my_route_table_id = self.__find_my_route_table_id()
        self.name_tag = instance_tags.get_name()

        logging.info(
            "Initialized NatInstance for {0.instance_id} {0.my_route_table_id}".format(self))

    def __find_my_route_table_id(self):
        """ Finds the route_table_id for the az our instance is in. """
        return self.__find_route_table_id(self.vpc_id, self.az)

    def __find_route_table_id(self, vpc_id, az):
        """ Finds a route table id for a given vpc and az with the tag network:private  """
        subnet_id = self.vpc_conn.get_all_subnets(
            filters={'vpcId': vpc_id, 'availabilityZone': az, 'tag:network': 'private'})[0].id
        return self.vpc_conn.get_all_route_tables(filters={'association.subnet-id': subnet_id})[
            0].id

    def set_route(self):
        """ Creates or replaces the route for our NAT instance """
        logging.info(
            "Setting Route for {0.instance_id} {0.my_route_table_id}".format(self))
        self.__update_route(self.my_route_table_id, self.instance_id)
        logging.info(
            "Successfully updated route for {0.instance_id} {0.my_route_table_id}".format(self))

    def disable_source_dest_check(self):
        """ Sets the sourceDestCheck property on the ec2 instance """
        self.ec2_conn.modify_instance_attribute(
            self.instance_id, 'sourceDestCheck', False)
        logging.info(
            "sourceDestCheck disabled for {0.instance_id}".format(self))

    def __update_route(self, route_table_id, instance_id):
        try:
            self.vpc_conn.create_route(route_table_id, '0.0.0.0/0',
                                       instance_id=instance_id)
        except boto.exception.EC2ResponseError as err:
            if err.error_code == 'RouteAlreadyExists':
                self.vpc_conn.replace_route(route_table_id, '0.0.0.0/0',
                                            instance_id=instance_id)
            else:
                raise err


def configure_nat_instance(vpc_conn, ec2_conn, instance_tags, instance_metadata):
    nat_instance = NatInstance(vpc_conn, ec2_conn, instance_tags, instance_metadata)
    nat_instance.disable_source_dest_check()
    nat_instance.set_route()
    return nat_instance


def create_aws_connections(region):
    ec2_conn = boto.ec2.connect_to_region(region)
    vpc_conn = boto.vpc.connect_to_region(region)
    elb_conn = boto.ec2.elb.connect_to_region(region)
    return vpc_conn, ec2_conn, elb_conn


def main():
    region = boto.utils.get_instance_identity()['document']['region']
    instance_metadata = boto.utils.get_instance_metadata()

    vpc_conn, ec2_conn, elb_conn = create_aws_connections(region)
    instance_tags = utils.InstanceTags(ec2_conn, instance_metadata['instance-id'])

    configure_nat_instance(
        vpc_conn, ec2_conn, instance_tags, instance_metadata)


if __name__ == '__main__':
    main()
