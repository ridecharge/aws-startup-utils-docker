#!/usr/bin/env python3
import boto
import boto.ec2
import boto.utils
import logging
import utils


class NetworkInterfaceAttachment(object):
    def __init__(self, ec2_conn, instance_tags, instance_metadata, device_index=1):
        self.ec2_conn = ec2_conn
        self.role = instance_tags.get_role()
        self.subnet_id = list(instance_metadata['network']['interfaces']['macs'].values())[
            0]['subnet-id']
        self.instance_id = instance_metadata['instance-id']
        self.device_index = device_index
        logging.info(
            "Initializing NetworkInterfaceAttachment" +
            "{0.role} in subnet {0.subnet_id} to instance {0.instance_id} on index {0.device_index}"
            .format(self))

    def __find_network_interface(self):
        return self.ec2_conn.get_all_network_interfaces(
            filters={'tag:Role': self.role,
                     'subnet-id': self.subnet_id,
                     'status': 'available'}
        )[0]

    def attach(self):
        network_interface = self.__find_network_interface()
        logging.info("Attaching Network Interface {0} to {1}".
                         format(network_interface, self.instance_id))
        network_interface.attach(self.instance_id, self.device_index)


def main():
    instance_metadata = boto.utils.get_instance_metadata()
    ec2_conn = boto.ec2.connect_to_region(
        boto.utils.get_instance_identity()['document']['region'])
    instance_tags = utils.InstanceTags(ec2_conn, instance_metadata['instance-id'])
    NetworkInterfaceAttachment(
        ec2_conn, instance_tags, instance_metadata).attach()


if __name__ == '__main__':
    main()
