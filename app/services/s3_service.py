from pathlib import Path
import boto3
from botocore.config import Config
from app.config import S3Config


class S3Service:
    def __init__(self):
        cfg = S3Config()
        client_kwargs = {
            "aws_access_key_id": cfg.access_key,
            "aws_secret_access_key": cfg.secret_key,
            "config": Config(
                region_name=cfg.region,
                signature_version="s3v4",
            ),
        }
        if cfg.endpoint_url:
            client_kwargs["endpoint_url"] = cfg.endpoint_url

        self.client = boto3.client("s3", **client_kwargs)
        self.bucket = cfg.bucket_name
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            try:
                self.client.create_bucket(Bucket=self.bucket)
            except Exception as e:
                print(f"Note: Could not create bucket '{self.bucket}': {e}")

    def upload_file(self, local_path: str | Path, s3_key: str | None = None) -> str:
        local_path = Path(local_path)
        key = s3_key or local_path.name
        self.client.upload_file(str(local_path), self.bucket, key)
        return key

    def download_file(self, s3_key: str, local_path: str | Path) -> Path:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, s3_key, str(local_path))
        return local_path

    def list_files(self, prefix: str = "") -> list[str]:
        resp = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [obj["Key"] for obj in resp.get("Contents", [])]

    def file_exists(self, s3_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except Exception:
            return False

    def delete_file(self, s3_key: str):
        self.client.delete_object(Bucket=self.bucket, Key=s3_key)
