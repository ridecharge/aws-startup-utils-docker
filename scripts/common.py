import logging
import loggly.handlers

LOGGLY_URL = "https://logs-01.loggly.com/inputs/" + \
             "{}/tag/python,boot,cloudformation,{}"


def build_logger(name, loggly_token, tags):
    """ Sets up a logger to send files to Loggly with dynamic tags """
    logger = logging.getLogger(name)
    url = LOGGLY_URL.format(loggly_token, ",".join(tags))
    handler = loggly.handlers.HTTPSHandler(url)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger

class InstanceTags(object):
    def __init__(self, ec2_conn, instance_id):
        self.tags = ec2_conn.get_only_instances(instance_id)[0].tags

    def get(self, tag_name):
        return self.tags[tag_name]

    def get_role(self):
        return self.get('Role').lower()

    def get_name(self):
        return self.get('Name')

    def get_public_internal_hosted_zone(self):
        return self.get('PublicInternalHostedZone')

    def get_public_internal_domain(self):
        return self.get('PublicInternalDomain')
