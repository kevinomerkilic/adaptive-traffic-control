import boto3
import json
from datetime import datetime
import io
from PIL import Image
import os
from botocore.exceptions import ClientError

class AWSHandler:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name
        
    def upload_detection_results(self, frame, detections, location_id="camera_1"):
        """
        Upload detection results and frame to S3
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save detection results as JSON
            detection_data = {
                "timestamp": timestamp,
                "location_id": location_id,
                "detections": detections
            }
            
            # Upload JSON results
            json_key = f"detections/{location_id}/{timestamp}.json"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=json_key,
                Body=json.dumps(detection_data)
            )
            
            # Convert frame to bytes and upload
            img_byte_arr = io.BytesIO()
            Image.fromarray(frame).save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            image_key = f"frames/{location_id}/{timestamp}.jpg"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=image_key,
                Body=img_byte_arr,
                ContentType='image/jpeg'
            )
            
            return {
                "status": "success",
                "json_path": json_key,
                "image_path": image_key
            }
            
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_recent_detections(self, location_id="camera_1", limit=100):
        """
        Retrieve recent detection results from S3
        """
        try:
            # List objects in the detections folder
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"detections/{location_id}/",
                MaxKeys=limit
            )
            
            results = []
            for obj in response.get('Contents', []):
                # Get the JSON content
                json_obj = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=obj['Key']
                )
                detection_data = json.loads(json_obj['Body'].read())
                results.append(detection_data)
            
            return {
                "status": "success",
                "results": results
            }
            
        except ClientError as e:
            print(f"Error retrieving from S3: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_traffic_analytics(self, location_id="camera_1", time_range="24h"):
        """
        Generate traffic analytics from stored detection data
        """
        try:
            # Get recent detections
            detections = self.get_recent_detections(location_id)
            if detections["status"] != "success":
                return detections
            
            # Process detection data
            analytics = {
                "total_vehicles": 0,
                "vehicle_types": {},
                "hourly_distribution": {},
                "peak_times": []
            }
            
            for detection in detections["results"]:
                # Count vehicles
                for obj in detection["detections"]:
                    obj_class = obj[5]  # Class index
                    analytics["vehicle_types"][obj_class] = analytics["vehicle_types"].get(obj_class, 0) + 1
                    if obj_class in ["car", "truck", "bus", "motorcycle"]:
                        analytics["total_vehicles"] += 1
                
                # Process timestamp for hourly distribution
                timestamp = datetime.strptime(detection["timestamp"], "%Y%m%d_%H%M%S")
                hour = timestamp.strftime("%H:00")
                analytics["hourly_distribution"][hour] = analytics["hourly_distribution"].get(hour, 0) + 1
            
            return {
                "status": "success",
                "analytics": analytics
            }
            
        except Exception as e:
            print(f"Error generating analytics: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
