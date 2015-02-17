#!/usr/bin/env python3
import boto
import boto.vpc
import boto.ec2
import boto.ec2.elb
import boto.utils
import utils
import time


class NatMonitor(object):
    def __init__(self, elb_conn, nat_instance, logger):
        self.elb_conn = elb_conn
        self.nat_instance = nat_instance
        self.logger = logger

        # Only take over when we've seen a healthy instance come up once
        self.allow_take_over = False
        # Instance Id of the nat route we've taken over
        self.other_instance_id = None

    def __get_other_instance_health(self):
        # Get all healths of instances for our ELB
        healths = self.elb_conn.describe_instance_health(
            self.nat_instance.name_tag)
        # Find the health of the instance that is not us
        for health in healths:
            if health.instance_id != self.nat_instance.instance_id:
                return health
        return None

    def __attempt_take_over(self, other_instance_health):
        """ Has the instance take over the other route if necessary """
        # If the instance is not InService then
        if not other_instance_health or other_instance_health.state != 'InService':
            self.logger.info(
                "NAT Monitoring instance {} unhealthy.".format(self.other_instance_id))
            # take over its route
            self.nat_instance.take_over_route()
            # and don't allow it to be taken over again
            self.allow_take_over = False

    def __check_instance(self, other_instance_health):
        """ Attempt to reset the state of our monitor when a healthy instance returns """
        if other_instance_health and other_instance_health.state == 'InService':
            # allow it to be taken over again
            self.allow_take_over = True
            # is the same instance we took over for
            if other_instance_health.instance_id == self.other_instance_id:
                self.nat_instance.restore_taken_over_route(
                    self.other_instance_id)
            else:
                self.other_instance_id = other_instance_health.instance_id

            self.logger.info(
                "NAT Monitoring instance {} healthy.".format(self.other_instance_id))

    def monitor(self):
        """ Monitor the other NAT Instance via the our ELB """
        self.logger.info(
            "NAT Monitoring instance {} running.".format(self.other_instance_id))
        # Get all health of instances for the elb with our name tag
        other_instance_health = self.__get_other_instance_health()

        # See if we are able to take over the route
        if self.allow_take_over:
            self.__attempt_take_over(other_instance_health)
        else:
            self.__check_instance(other_instance_health)


class NatInstance(object):
    TAKE_OVER_AZ = {
        'us-east-1a': 'us-east-1c',
        'us-east-1c': 'us-east-1a',
        'us-west-1a': 'us-west-1b',
        'us-west-1b': 'us-west-1a'
    }

    def __init__(self, vpc_conn, ec2_conn, instance_tags, instance_metadata, logger):
        self.vpc_conn = vpc_conn
        self.ec2_conn = ec2_conn

        self.vpc_id = list(
            instance_metadata['network']['interfaces']['macs'].values())[0]['vpc-id']
        self.az = instance_metadata['placement']['availability-zone']
        self.instance_id = instance_metadata['instance-id']
        self.my_route_table_id = self.__find_my_route_table_id()
        self.take_over_route_table_id = self.__find_takeover_route_table_id()
        self.name_tag = instance_tags.get_name()

        self.logger = logger
        self.logger.info(
            "Initialized NatInstance for {0.instance_id} {0.my_route_table_id}".format(self))

    def __find_takeover_route_table_id(self):
        """ Looks up the route table id for the other AZ in the vpc """
        take_over_az = NatInstance.TAKE_OVER_AZ[self.az]
        return self.__find_route_table_id(self.vpc_id, take_over_az)

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
        self.logger.info(
            "Setting Route for {0.instance_id} {0.my_route_table_id}".format(self))
        self.__update_route(self.my_route_table_id, self.instance_id)
        self.logger.info(
            "Successfully updated route for {0.instance_id} {0.my_route_table_id}".format(self))

    def disable_source_dest_check(self):
        """ Sets the sourceDestCheck property on the ec2 instance """
        self.ec2_conn.modify_instance_attribute(
            self.instance_id, 'sourceDestCheck', False)
        self.logger.info(
            "sourceDestCheck disabled for {0.instance_id}".format(self))

    def take_over_route(self):
        """ Takes over the other AZ's route """
        self.logger.info(
            "Taking over route {0.take_over_route_table_id}".format(self))
        self.__update_route(self.take_over_route_table_id, self.instance_id)

    def restore_taken_over_route(self, taken_instance_id):
        """ Restores the other AZ's route """
        self.logger.info(
            "Restoring route {0.take_over_route_table_id}".format(self))
        self.__update_route(self.take_over_route_table_id, taken_instance_id)

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


def configure_nat_instance(vpc_conn, ec2_conn, instance_metadata, logger):
    nat_instance = NatInstance(vpc_conn, ec2_conn, instance_metadata, logger)
    nat_instance.disable_source_dest_check()
    nat_instance.set_route()
    return nat_instance


def configure_nat_monitor(elb_conn, nat_instance, logger):
    nat_monitor = NatMonitor(elb_conn, nat_instance, logger)
    return nat_monitor


def create_aws_connections(region):
    ec2_conn = boto.ec2.connect_to_region(region)
    vpc_conn = boto.vpc.connect_to_region(region)
    elb_conn = boto.ec2.elb.connect_to_region(region)
    return vpc_conn, ec2_conn, elb_conn


def main():
    # AWS Instance metadata
    region = boto.utils.get_instance_identity()['document']['region']
    instance_metadata = boto.utils.get_instance_metadata()

    vpc_conn, ec2_conn, elb_conn = create_aws_connections(region)
    instance_tags = utils.InstanceTags(ec2_conn, instance_metadata['instance-id'])
    logger = utils.get_logger(
        NatMonitor.__name__,
        [instance_metadata['instance-id'],
         instance_tags.get_role(),
         instance_tags.get_environment()])

    try:
        nat_instance = configure_nat_instance(
            vpc_conn, ec2_conn, instance_tags, instance_metadata, logger)
        nat_monitor = configure_nat_monitor(elb_conn, nat_instance, logger)

        while True:
            nat_monitor.monitor()
            time.sleep(10)
    except:
        logger.exception("NAT Take Over Monitoring Failed")


if __name__ == '__main__':
    main()
