import boto3, os, time, json, asyncio

from abc import ABC, abstractmethod
from dotenv import load_dotenv
from bson import json_util

from pymongo import MongoClient

load_dotenv()

class BaseStorage(ABC):
    def __init__(self, dbname):
        self.dbname = dbname

    @abstractmethod
    def store(self, data):
        pass

class AwsStorage(BaseStorage):
    def __init__(self, bucket_name):
        super(AwsStorage, self).__init__(bucket_name)
        self.client = boto3.client('s3', 
                                    aws_access_key_id = os.getenv("AWS_ACCESS", ""),
                                    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS", ""))

    async def store(self, data):
        key = str(data.get("id", "NoWasherId")) + "/" + str(data.get("time", time.time())) 
        bucket_name = self.dbname
        serialized_data = json.dumps(data)
        try:
            self.client.put_object(Body=serialized_data, Bucket=bucket_name, Key=key) 
        except Exception as e:
            print(e)
            return False
        return True

class MongoStorage(BaseStorage):
    def __init__(self, dbname, port = 27017, host = "localhost"):
        super(MongoStorage, self).__init__(dbname)
        self.port = int(os.getenv("MONGO_PORT", port))
        self.host = host
        self.client = MongoClient(self.host, self.port)
        self.db = self.client[os.getenv("MONGO_DBNAME", dbname)]
        self.collection = self.db[os.getenv("MONGO_COLLECTION_NAME", "laundry_network")] 

    async def store(self, data):
        try:
            self.collection.insert_one(data)
        except Exception as e:
            print(e)
            return False
        return True

dbname = "cse520"
mongodb = MongoStorage(dbname)
s3 = AwsStorage(dbname)

def get_store(name):
    data_stores = {"s3": s3, "mongo": mongodb}

    name = name.lower()
    if name not in ("mongo", "s3"):
        raise ValueError("invalid data storage service requested")
    return data_stores[name] 

if __name__ == "__main__":
    data = {"time": 1, "current": 0.3232, "washer_id": 20}

    async def test():
        aws_store = AwsStorage("test")
        print("Success AWS =", await aws_store.store(data))
        mongo_store = MongoStorage("test")
        print("Success MongoDB =", await mongo_store.store(data))

    asyncio.run(test())
