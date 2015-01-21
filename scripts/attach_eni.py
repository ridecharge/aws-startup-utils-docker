#!/usr/bin/env python3
import boto
import boto.ec2
import boto.utils
import logging
import loggly.handlers
import sys


class NetworkInterfaceAttachment(object):
    def __init__(self, conn, logger, role, subnet_id, instance_id, device_index=1):
        self.conn = conn
        self.logger = logger
        self.role = role
        self.subnet_id = subnet_id
        self.instance_id = instance_id
        self.device_index = device_index
        self.logger.info(
            "Initializing NetworkInterfaceAttachment {0.role} in subnet {0.subnet_id} to instance {0.instance_id} on index {0.device_index}".format(
                self))

    def find_network_interface(self):
        return self.conn.get_all_network_interfaces(
            filters={'tag:Role': self.role, 'subnet-id': self.subnet_id}
        )[0]

    def attach(self):
        network_interface = self.find_network_interface()
        self.logger.info("Attaching Network Interface {0} to {1}".
                         format(network_interface, self.instance_id))
        network_interface.attach(self.instance_id, self.device_index)


LOGGLY_URL = "https://logs-01.loggly.com/inputs/" + \
             "e8bcd155-264b-4ec0-88be-fcb023f76a89/tag/python,boot,networkinterface,cloudformation"


def get_role(ec2_conn, instance_id):
    return ec2_conn.get_only_instances(instance_id)[0].tags['Role'].lower()


def build_logger(name, instance_id, role):
    """ Sets up a logger to send files to Loggly with dynamic tags """
    logger = logging.getLogger(name)
    url = ",".join([LOGGLY_URL, instance_id, role])
    handler = loggly.handlers.HTTPSHandler(url)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger


def main():
    instance_metadata = boto.utils.get_instance_metadata()
    instance_id = instance_metadata['instance-id']
    subnet_id = list(instance_metadata['network']['interfaces']['macs'].values())[0]['subnet-id']
    conn = boto.ec2.connect_to_region(boto.utils.get_instance_identity()['document']['region'])
    role = get_role(conn, instance_id)

    logger = build_logger(NetworkInterfaceAttachment.__name__, instance_id, role)
    try:
        NetworkInterfaceAttachment(conn, logger, role, subnet_id, instance_id).attach()
    except:
        logger.exception("Failed to attach network interface.")


if __name__ == '__main__':
    main()
