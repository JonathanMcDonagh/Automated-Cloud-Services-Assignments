#!/usr/bin/python
#!/usr/bin/env python3
import boto3
import sys
import subprocess
import check_webserver
import time


ec2 = boto3.resource('ec2')
client = boto3.client('s3')
s3 = boto3.resource("s3")


#Creates the s3 Bucket 
bucket_name = input("What do you want to name your s3 bucket?\n") #Allows the user to create the bucket name
bucket_name = bucket_name.lower()
try: 
    client.create_bucket(
    Bucket = bucket_name,
    ACL ='public-read-write',
    CreateBucketConfiguration={
        'LocationConstraint':'eu-west-1'
    },
    ObjectLockEnabledForBucket=False
    )
    print(bucket_name, ' was created')
except Exception as error:
    print(error)
time.sleep(5)


#To add a image to the s3 Bucket, user picks the image from the folder I give an example photo to use that has my student details
image_name = input("\nWhat image do you want to upload to your bucket? It must be in the same folder as this python script \ne.g studentdetails.jpg \n")
try:
    s3.Object(bucket_name, image_name).put(
        ContentType='image/jpeg', 
        ACL='public-read-write', 
        Body=open(image_name, 'rb'))
    print(image_name, ' was added to ', bucket_name, '\n')
except Exception as error:
    print(error)
time.sleep(5)


#For the web server
user_data = """#!/bin/bash
yum install python3 -y
yum update -y
yum install httpd -y
systemctl enable httpd
systemctl start httpd
echo "<h2>Assignment 1</h2>Instance ID: " > /var/www/html/index.html
curl --silent http://169.254.169.254/latest/meta-data/instance-id/ >> /var/www/html/index.html
echo "<br>Availability zone: " >> /var/www/html/index.html
curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone/ >> /var/www/html/index.html
echo "<br>IP address: " >> /var/www/html/index.html
curl --silent http://169.254.169.254/latest/meta-data/public-ipv4 >> /var/www/html/index.html
echo "<hr>Here is an image that I have stored on my S3 Bucket: <br>" >> /var/www/html/index.html
echo "<img src=https://s3-eu-west-1.amazonaws.com/%s/studentdetails.jpg>" >> /var/www/html/index.html""" %bucket_name


#Creates the ec2 instance 
instance = ec2.create_instances(
    UserData= user_data,
    ImageId='ami-0bdb1d6c15a40392c',
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName='JohnnysKey',
    SecurityGroupIds=['sg-0e42b1c535bc76147'], #HTTP & SSH
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'Automated Cloud Assignment 1'
                },
            ]
        }
    ],   
)
instance[0].wait_until_running()
instance[0].reload()
print ('Created instance id=', instance[0].id, ' ip=', instance[0].public_ip_address, '\n')
time.sleep(20)


#check_webserver
print("Starting Web Server... ")
time.sleep(10)
print("Completed...\n")

ip_address = instance[0].public_ip_address 

try:
    cmd1 = "scp -i JohnnysKey.pem check_webserver.py ec2-user@" + ip_address + ":." #scp
    cmd2 = "ssh -i JohnnysKey.pem ec2-user@" + ip_address + "' python3 check_webserver.py'" #ssh

    subprocess.run(cmd1, shell = True)
    subprocess.run(cmd2, shell = True)
except Exception as error:
    print(error)     

