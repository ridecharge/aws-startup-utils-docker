class InstanceTags(object):
    def __init__(self, ec2_conn, instance_id):
        self.tags = ec2_conn.get_only_instances(instance_id)[0].tags

    def get(self, tag_name):
        return self.tags[tag_name]

    def get_role(self):
        return self.get('Role').lower()

    def get_name(self):
        return self.get('Name')

    def get_environment(self):
        return self.get('Environment')
