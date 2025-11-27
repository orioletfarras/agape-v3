"""AWS S3 Service for file uploads"""
import logging
from io import BytesIO
from typing import Optional
from uuid import uuid4
import boto3
from botocore.exceptions import ClientError
from PIL import Image

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for uploading files to AWS S3"""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.AWS_S3_BUCKET
        self.region = settings.AWS_S3_REGION

    async def upload_file(
        self,
        file_data: bytes,
        prefix: str,
        content_type: str,
        filename: Optional[str] = None,
    ) -> str:
        """
        Upload a file to S3 and return the URL

        Args:
            file_data: File bytes
            prefix: S3 prefix (folder)
            content_type: MIME type
            filename: Optional filename, generates UUID if not provided

        Returns:
            str: Public URL of uploaded file
        """
        try:
            # Generate filename if not provided
            if not filename:
                ext = content_type.split("/")[-1]
                filename = f"{uuid4()}.{ext}"

            # Full S3 key
            key = f"{prefix}{filename}"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                ACL="public-read",
            )

            # Return public URL
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
            logger.info(f"File uploaded successfully to S3: {url}")
            return url

        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")

    async def upload_image(
        self,
        file_data: bytes,
        prefix: str,
        max_width: int = 1920,
        max_height: int = 1920,
        quality: int = 85,
    ) -> str:
        """
        Upload and optimize an image to S3

        Args:
            file_data: Image file bytes
            prefix: S3 prefix (folder)
            max_width: Maximum width for resizing
            max_height: Maximum height for resizing
            quality: JPEG quality (1-100)

        Returns:
            str: Public URL of uploaded image
        """
        try:
            # Open image
            img = Image.open(BytesIO(file_data))

            # Convert RGBA to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background

            # Resize if needed
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Save optimized image to bytes
            output = BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            output.seek(0)

            # Upload to S3
            return await self.upload_file(
                file_data=output.read(),
                prefix=prefix,
                content_type="image/jpeg",
            )

        except Exception as e:
            logger.error(f"Error processing and uploading image: {e}")
            raise Exception(f"Failed to process image: {str(e)}")

    async def upload_profile_image(self, file_data: bytes) -> str:
        """Upload profile image"""
        return await self.upload_image(
            file_data=file_data,
            prefix=settings.AWS_S3_PROFILE_IMAGES_PREFIX,
            max_width=800,
            max_height=800,
            quality=90,
        )

    async def upload_post_image(self, user_id: int, file_data: bytes, filename: Optional[str] = None) -> dict:
        """Upload post image"""
        url = await self.upload_image(
            file_data=file_data,
            prefix=settings.AWS_S3_POST_IMAGES_PREFIX,
        )
        return {"url": url, "key": url.split(f"{self.bucket}.s3.{self.region}.amazonaws.com/")[-1]}

    async def upload_post_video(self, user_id: int, file_data: bytes, filename: Optional[str] = None) -> dict:
        """Upload post video"""
        # Determine content type from filename
        content_type = "video/mp4"  # default
        if filename:
            if filename.lower().endswith(".mov") or filename.lower().endswith(".quicktime"):
                content_type = "video/quicktime"
            elif filename.lower().endswith(".avi"):
                content_type = "video/x-msvideo"

        url = await self.upload_file(
            file_data=file_data,
            prefix=settings.AWS_S3_POST_VIDEOS_PREFIX,
            content_type=content_type,
        )
        return {"url": url, "key": url.split(f"{self.bucket}.s3.{self.region}.amazonaws.com/")[-1]}

    async def upload_channel_image(self, file_data: bytes) -> str:
        """Upload channel image"""
        return await self.upload_image(
            file_data=file_data,
            prefix=settings.AWS_S3_CHANNEL_IMAGES_PREFIX,
            max_width=800,
            max_height=800,
        )

    async def upload_event_image(self, file_data: bytes) -> str:
        """Upload event image"""
        return await self.upload_image(
            file_data=file_data,
            prefix=settings.AWS_S3_EVENT_IMAGES_PREFIX,
        )

    async def delete_file(self, url: str) -> bool:
        """
        Delete a file from S3 by its URL

        Args:
            url: Full S3 URL

        Returns:
            bool: True if deleted successfully
        """
        try:
            # Extract key from URL
            key = url.split(f"{self.bucket}.s3.{self.region}.amazonaws.com/")[-1]

            # Delete from S3
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"File deleted successfully from S3: {key}")
            return True

        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False


# Singleton instance
s3_service = S3Service()
