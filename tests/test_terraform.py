import unittest
from tfparse import load_from_path


REQUIRED_PROVIDER = {
    "required_providers": {
        "aws": {
            "source": "hashicorp/aws",
            "version": "~> 5.0"
        }
    }
}

PROVIDER = {
    "provider": [
        {
            "region": "us-east-1",
            "shared_credentials_files": ["./credentials"]
        }
    ]
}

EXPECTED_SECURITY_GROUP = {
    "name": "hextris-server",
    "description": "Hextris HTTP and SSH access",
    "ingress": [
        {
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    "egress": 
        {
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
}

USER_DATA = """#!/bin/bash
yum install -y httpd
systemctl enable httpd
systemctl start httpd

yum install -y git
cd /var/www/html
git clone https://github.com/Hextris/hextris .
"""

EXPECTED_INSTANCE = {
    "ami": "ami-0e731c8a588258d0d",
    "instance_type": "t2.micro",
    "user_data": USER_DATA,
    "security_groups": {
        '__attributes__': ['aws_security_group.hextris-server.name']
    },
    "tags": {
        "Name": "hextris"
    }
}

EXPECTED_OUTPUT = {
    "value": {
        '__attribute__': 'aws_instance.hextris-server.public_ip'
    }
}

class TestTerraform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tf = load_from_path(".")

    def assertResource(self, resource, expected):
        for key, value in expected.items():
            if isinstance(value, dict):
                self.assertResource(resource[key], value)
            elif isinstance(value, list):
                self.assertResourceList(resource[key], value)
            else:
                self.assertIn(key, resource)
                self.assertEqual(resource[key], value)

    def assertResourceList(self, resource_list, expected):
        self.assertEqual(len(resource_list), len(expected), "Wrong number of resources")
        for resource, expected in zip(resource_list, expected):
            if isinstance(expected, dict):
                self.assertResource(resource, expected)
            else:
                self.assertEqual(resource, expected)

    def resurce_by_name(self, resource_list, name):
        for resource in resource_list:
            if resource["__tfmeta"]["path"] == name:
                return resource
        return None

    def test_required_provider(self):
        self.assertIn("terraform", self.tf, "No terraform block found")
        terraform = self.tf["terraform"][0]
        self.assertResource(terraform, REQUIRED_PROVIDER)
   
    def test_provider(self):
        self.assertResource(self.tf, PROVIDER)

        provider = self.tf["provider"][0]
        self.assertEqual(provider["__tfmeta"]["label"], "aws", "Wrong provider")
    
    def test_security_group(self):
        self.assertIn("aws_security_group", self.tf, "No aws_security_group block found")
        security_groups = self.tf["aws_security_group"]

        security_group = self.resurce_by_name(security_groups, "aws_security_group.hextris-server")
        self.assertIsNotNone(security_group, "No security group named hextris-server")

        self.assertResource(security_group, EXPECTED_SECURITY_GROUP)

    def test_instance(self):
        self.assertIn("aws_instance", self.tf, "No aws_instance block found")
        instances = self.tf["aws_instance"]

        instance = self.resurce_by_name(instances, "aws_instance.hextris-server")
        self.assertIsNotNone(instance, "No instance named hextris-server")

        self.assertResource(instance, EXPECTED_INSTANCE)

    def test_output(self):
        self.assertIn("output", self.tf, "No output block found")
        outputs = self.tf["output"]

        output = self.resurce_by_name(outputs, "output.hextris-url")
        self.assertIsNotNone(output, "No output named hextris-url")

        self.assertResource(output, EXPECTED_OUTPUT)

