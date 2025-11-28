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

    async def upload_profile_image(self, user_id_code: str, file_data: bytes) -> str:
        """Upload user profile image to agape/users/<user_id_code>/profile/"""
        prefix = f"agape/users/{user_id_code}/profile/"
        return await self.upload_image(
            file_data=file_data,
            prefix=prefix,
            max_width=800,
            max_height=800,
            quality=90,
        )

    async def upload_post_image(self, user_id: int, file_data: bytes, filename: Optional[str] = None) -> dict:
        """Upload post image - temporarily stored, will be organized when post is created"""
        import uuid
        from datetime import datetime

        # Generate unique identifier for this upload session
        upload_id = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Use temporary structure: agape/posts/temp/<upload_id>/
        temp_prefix = f"agape/posts/temp/{upload_id}/"

        # Get file extension
        ext = "jpg"
        if filename:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"

        # Upload with compression (quality=85 for good balance)
        url = await self.upload_image(
            file_data=file_data,
            prefix=temp_prefix,
            max_width=1920,  # Max 1920px width
            max_height=1920,  # Max 1920px height
            quality=85,  # Good quality, reasonable file size
        )

        # Extract the S3 key from the URL
        key = url.split(f"{self.bucket}.s3.{self.region}.amazonaws.com/")[-1]

        return {
            "url": url,
            "key": key,
            "upload_id": upload_id,
            "temp_path": True
        }

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

    async def upload_channel_image(self, channel_id_code: str, file_data: bytes) -> str:
        """Upload channel profile image to agape/channels/<channel_id_code>/profile/"""
        prefix = f"agape/channels/{channel_id_code}/profile/"
        return await self.upload_image(
            file_data=file_data,
            prefix=prefix,
            max_width=800,
            max_height=800,
        )

    async def upload_event_image(self, user_id: int, file_data: bytes, filename: Optional[str] = None) -> dict:
        """Upload event image - temporarily stored, will be organized when event is created"""
        import uuid
        from datetime import datetime

        # Generate unique identifier for this upload session
        upload_id = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # Use temporary structure: agape/events/temp/<upload_id>/
        temp_prefix = f"agape/events/temp/{upload_id}/"

        # Get file extension
        ext = "jpg"
        if filename:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"

        # Upload with compression
        url = await self.upload_image(
            file_data=file_data,
            prefix=temp_prefix,
            max_width=1920,  # Max 1920px width
            max_height=1920,  # Max 1920px height
            quality=85,  # Good quality, reasonable file size
        )

        # Extract the S3 key from the URL
        key = url.split(f"{self.bucket}.s3.{self.region}.amazonaws.com/")[-1]

        return {
            "url": url,
            "key": key,
            "upload_id": upload_id,
            "temp_path": True
        }

    async def reorganize_post_images(self, post_id_code: str, temp_image_urls: list[str]) -> list[str]:
        """
        Reorganize post images from temporary location to final structure

        Args:
            post_id_code: The post's unique id_code
            temp_image_urls: List of temporary image URLs

        Returns:
            list[str]: List of new URLs in final structure
        """
        final_urls = []

        for temp_url in temp_image_urls:
            try:
                # Extract the temporary key from URL
                temp_key = temp_url.split(f"{self.bucket}.s3.{self.region}.amazonaws.com/")[-1]

                # Extract filename from temp key (e.g., agape/posts/temp/20250128-abc123/uuid.jpg -> uuid.jpg)
                filename = temp_key.split("/")[-1]

                # Create final key with structure: agape/posts/<post_id_code>/images/<filename>
                final_key = f"agape/posts/{post_id_code}/images/{filename}"

                # Copy file to new location
                self.s3_client.copy_object(
                    Bucket=self.bucket,
                    CopySource={'Bucket': self.bucket, 'Key': temp_key},
                    Key=final_key,
                    ACL='public-read'
                )

                # Delete temporary file
                self.s3_client.delete_object(Bucket=self.bucket, Key=temp_key)

                # Create final URL
                final_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{final_key}"
                final_urls.append(final_url)

                logger.info(f"Image reorganized: {temp_key} -> {final_key}")

            except ClientError as e:
                logger.error(f"Error reorganizing image {temp_url}: {e}")
                # Keep the temp URL if reorganization fails
                final_urls.append(temp_url)

        return final_urls

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
