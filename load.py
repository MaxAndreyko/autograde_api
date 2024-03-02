import logging
import os

import boto3

log = logging.getLogger(__name__)


def s3_load_folder(bucket_name, s3_folder, local_folder):
    # Инициализация клиента S3
    session = boto3.session.Session()
    s3 = session.client(
        service_name="s3",
        endpoint_url="https://storage.yandexcloud.net",
        region_name="ru-central1",
        aws_access_key_id=os.environ["Key_id"],
        aws_secret_access_key=os.environ["Access_key"],
    )

    objects = s3.list_objects(Bucket=bucket_name, Prefix=s3_folder)["Contents"]

    for obj in objects[1:]:  # Пропустим первый пустой файл
        s3_file = os.path.basename(obj["Key"])
        local_file_path = os.path.join(local_folder, os.path.basename(obj["Key"]))
        log.info(
            f"=============== Downloading {s3_file} to {local_folder} ==============="
        )
        s3.download_file(bucket_name, obj["Key"], local_file_path)
        log.info(f"=============== Downloading {s3_file} completed ===============")
