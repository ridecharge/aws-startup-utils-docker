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


def get_role(ec2_conn, instance_id):
    return ec2_conn.get_only_instances(instance_id)[0].tags['Role'].lower()


def get_name_tag(ec2_conn, instance_id):
    return ec2_conn.get_only_instances(instance_id)[0].tags['Name']
