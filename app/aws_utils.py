import os
import json
import boto3
from datetime import datetime
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

class AWSManager:
    def __init__(self):
        # Initialize AWS clients
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        
        # Create resources if they don't exist
        self.setup_resources()
        
    def setup_resources(self):
        """Initialize required AWS resources"""
        try:
            # Create S3 bucket for detection results
            self.bucket_name = 'smart-traffic-detections'
            try:
                self.s3.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'BucketAlreadyOwnedByYou':
                    raise

            # Create DynamoDB table for traffic statistics
            self.table_name = 'traffic_statistics'
            try:
                self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {'AttributeName': 'timestamp', 'KeyType': 'HASH'},
                        {'AttributeName': 'location_id', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                        {'AttributeName': 'location_id', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceInUseException':
                    raise

            # Create SNS topic for alerts
            self.topic_name = 'traffic_alerts'
            try:
                response = self.sns.create_topic(Name=self.topic_name)
                self.topic_arn = response['TopicArn']
            except ClientError as e:
                if 'TopicAlreadyExists' not in str(e):
                    raise

        except Exception as e:
            print(f"Error setting up AWS resources: {str(e)}")

    def store_detection_frame(self, frame, detections, timestamp):
        """Store detection frame and results in S3"""
        try:
            # Save frame as JPEG
            frame_key = f"frames/{timestamp.strftime('%Y/%m/%d/%H/%M_%S')}.jpg"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=frame_key,
                Body=frame.tobytes(),
                ContentType='image/jpeg'
            )

            # Save detection results as JSON
            detection_key = f"detections/{timestamp.strftime('%Y/%m/%d/%H/%M_%S')}.json"
            detection_data = {
                'timestamp': timestamp.isoformat(),
                'detections': detections
            }
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=detection_key,
                Body=json.dumps(detection_data),
                ContentType='application/json'
            )

            return frame_key, detection_key
        except Exception as e:
            print(f"Error storing detection data: {str(e)}")
            return None, None

    def update_traffic_stats(self, location_id, vehicle_count, congestion_level, timestamp):
        """Store traffic statistics in DynamoDB"""
        try:
            table = self.dynamodb.Table(self.table_name)
            table.put_item(
                Item={
                    'timestamp': timestamp.isoformat(),
                    'location_id': location_id,
                    'vehicle_count': vehicle_count,
                    'congestion_level': congestion_level
                }
            )
        except Exception as e:
            print(f"Error updating traffic stats: {str(e)}")

    def publish_cloudwatch_metrics(self, location_id, vehicle_count, congestion_level):
        """Publish metrics to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='SmartTraffic',
                MetricData=[
                    {
                        'MetricName': 'VehicleCount',
                        'Value': vehicle_count,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'LocationId',
                                'Value': location_id
                            }
                        ]
                    },
                    {
                        'MetricName': 'CongestionLevel',
                        'Value': len(congestion_level),  # Convert level to numeric value
                        'Unit': 'None',
                        'Dimensions': [
                            {
                                'Name': 'LocationId',
                                'Value': location_id
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            print(f"Error publishing CloudWatch metrics: {str(e)}")

    def send_congestion_alert(self, location_id, congestion_level, vehicle_count):
        """Send SNS alert for high congestion"""
        try:
            if congestion_level in ['high', 'severe']:
                message = {
                    'location_id': location_id,
                    'congestion_level': congestion_level,
                    'vehicle_count': vehicle_count,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.sns.publish(
                    TopicArn=self.topic_arn,
                    Message=json.dumps(message),
                    Subject=f'Traffic Alert: {congestion_level.upper()} congestion detected'
                )
        except Exception as e:
            print(f"Error sending congestion alert: {str(e)}")
