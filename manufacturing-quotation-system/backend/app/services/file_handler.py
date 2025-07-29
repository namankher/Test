import os
import shutil
import uuid
from typing import Optional
import boto3
from botocore.exceptions import ClientError

class FileHandler:
    def __init__(self):
        self.local_storage_path = os.getenv("UPLOAD_DIR", "uploads")
        self.use_s3 = os.getenv("AWS_ACCESS_KEY_ID") is not None
        
        if self.use_s3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            self.bucket_name = os.getenv("AWS_BUCKET_NAME")
    
    def ensure_directory_exists(self, directory_path: str):
        """Create directory if it doesn't exist"""
        os.makedirs(directory_path, exist_ok=True)
    
    async def save_file_locally(self, file_content: bytes, file_path: str) -> str:
        """Save file to local storage"""
        directory = os.path.dirname(file_path)
        self.ensure_directory_exists(directory)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
    
    async def save_file_to_s3(self, file_content: bytes, s3_key: str) -> str:
        """Save file to S3 storage"""
        if not self.use_s3:
            raise ValueError("S3 configuration not available")
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content
            )
            return f"s3://{self.bucket_name}/{s3_key}"
        except ClientError as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate a URL to access the file"""
        if file_path.startswith("s3://"):
            # Generate presigned URL for S3
            bucket, key = file_path.replace("s3://", "").split("/", 1)
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
            except ClientError as e:
                raise Exception(f"Failed to generate presigned URL: {str(e)}")
        else:
            # Return local file path (would need to be served by web server)
            return f"/static/{os.path.relpath(file_path, self.local_storage_path)}"
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage"""
        try:
            if file_path.startswith("s3://"):
                # Delete from S3
                bucket, key = file_path.replace("s3://", "").split("/", 1)
                self.s3_client.delete_object(Bucket=bucket, Key=key)
            else:
                # Delete from local storage
                if os.path.exists(file_path):
                    os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """Get file information"""
        try:
            if file_path.startswith("s3://"):
                # Get S3 object info
                bucket, key = file_path.replace("s3://", "").split("/", 1)
                response = self.s3_client.head_object(Bucket=bucket, Key=key)
                return {
                    "size": response['ContentLength'],
                    "last_modified": response['LastModified'],
                    "content_type": response.get('ContentType', 'application/octet-stream')
                }
            else:
                # Get local file info
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    return {
                        "size": stat.st_size,
                        "last_modified": stat.st_mtime,
                        "content_type": "application/octet-stream"
                    }
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error getting file info: {str(e)}")
    
    def cleanup_quote_files(self, quote_id: str) -> bool:
        """Clean up all files for a specific quote"""
        try:
            if self.use_s3:
                # List and delete S3 objects with quote_id prefix
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=f"quotes/{quote_id}/"
                )
                if 'Contents' in response:
                    objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                    if objects_to_delete:
                        self.s3_client.delete_objects(
                            Bucket=self.bucket_name,
                            Delete={'Objects': objects_to_delete}
                        )
            
            # Also clean up local files
            local_quote_dir = os.path.join(self.local_storage_path, quote_id)
            if os.path.exists(local_quote_dir):
                shutil.rmtree(local_quote_dir)
            
            return True
        except Exception as e:
            print(f"Error cleaning up files for quote {quote_id}: {str(e)}")
            return False