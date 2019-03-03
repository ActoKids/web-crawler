import boto3
import time

region = ('us-east-1')

instances = ['i-0a9c5fe477ab2c1cb']

def main():
    ec2 = boto3.client('ec2', region_name=region)
    ec2.stop_instances(InstanceIds=instances)
#Wait 2 minutes before shutting down. For admin purposes.
time.sleep(120)
main()