import boto3
import io


class msgController:
    def __init__(self, bucket):
        self.s3 = boto3.client("s3")
        self.bucket = bucket

    def getJSON(self, aws_fullPath, result):
        self.s3.download_file(self.bucket, aws_fullPath, result)

    def setJSON(self, inputStr, aws_fullPath):
        input = io.BytesIO(inputStr.encode("utf-8"))
        self.s3.upload_fileobj(input, self.bucket, aws_fullPath)

    def setFile(self, aws_fullPath, filePath):
        with open(filePath, "rb") as f:
            self.s3.upload_fileobj(f, self.bucket, aws_fullPath)
