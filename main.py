from typing import List
from google.cloud import storage, documentai_v1
from google.cloud.storage import Blob
from google.cloud.sql.connector import Connector

project = 757764650459
location = "us"
processor_id = "a7b2010ff0cf6502"

required_labels = [
    "client_address",
    "client_name",
    "order_number"
]


connection_name = "ari-dev-463216:us-central1:jerry-v1-db-instance"
pg_driver = "pg8000"
user = "postgres"
password = "gamalziplockshisfartstomarinateinthefridgebeforereleasingthemintheoffice"
db_name = "jerry_v1_extracted_db"





def _get_connection():
    try:
        connector = Connector()
        return connector.connect(
            connection_name,
            pg_driver,
            user=user,
            password=password,
            db=db_name
        )
    except Exception as e:
        raise RuntimeError(f"Connection Failed\nERROR: {e}")





def _store_extracted_data(conn, contents):

    insert_query = """
        INSERT INTO orders (
            order_id, client_name, client_address
        )   
        VALUES (%s, %s, %s);
    """
    
    try:
        cur = conn.cursor()
        values = [(data["order_id"], data["client_name"], data["client_address"]) for content in contents if (data:=content["extracted_data"])]
        cur.execute(insert_query, (data['order_number'], data['client_name'], data['client_address']))
        conn.commit()
        print("Inserted order")
    except Exception as e:
        print(f"Insert Query Failed\nERROR: {e}")


def _extract_data(blobs, bucket_name):
    client = documentai_v1.DocumentProcessorServiceClient()
    name = f"projects/{project}/locations/{location}/processors/{processor_id}"
    data = {
        "contents": [],
        "failed": [],
    }
    # data =  {
    #             contents: [{
    #                 blob: blob,
    #                 extracted_data: {
    #                     order_id: str
    #                     client_name: str
    #                     client_address: str
    #                 }
    #             }]
    #             failed: [blob]
    #         }
    
    for blob in blobs:
        gcsDocument = documentai_v1.GcsDocument(
            gcs_uri=f"gs://{bucket_name}/{blob.name}",
            mime_type=blob.content_type
        )

        request = documentai_v1.ProcessRequest(
            name=name,
            gcs_document=gcsDocument
        )

        resp = client.process_document(request=request)
        document = resp.document

        extracted_data={}

        for entity in document.entities:
            extracted_data[entity.type_] = entity.mention_text

        missing_labels = [label for label in required_labels if not extracted_data.get(label)]

        if len(missing_labels) >= 1:
            data["failed"].append(blob)
        else:
            data["contents"].append({
                "blob": blob,
                "extracted_data": {
                    "order_id": extracted_data["order_number"],
                    "client_name": extracted_data["client_name"],
                    "client_address": extracted_data["client_address"]
                }
            })
    return data


def job_processor(request=None):

    try:
        conn = _get_connection()
    except RuntimeError as e:
        print(f"[FATAL] {e}")
        return "Database connection failed", 500

    storageClient = storage.Client()
    bucket = storage.Bucket.from_uri("gs://jerry_v1_upload", client=storageClient)
    blobs: List[Blob] = bucket.list_blobs(prefix="to_process/")
    
    new_blobs: List[Blob] = []
    for blob in blobs:
        filename = blob.name.split("/")[1]
        new_blobs.append(bucket.copy_blob(blob, bucket, f"processing/{filename}"))
        # blob.delete()
    
    data = _extract_data(new_blobs, bucket.name)
    if len(data["failed"]) >= 1:
        for blob in data["failed"]:
            # MOVE TO FAIL
            filename = blob.name.split("/")[1]
            print(f"[FAIL] File `{filename}` has failed")
            bucket.copy_blob(blob, bucket, f"failed/{filename}")
            blob.delete()

    if len(data["contents"]) >=1:
        try:
            _store_extracted_data(conn, data["contents"])
        except Exception as e:
            return
        for content in data["contents"]:
            filename = content["blob"].name.split("/")[1]
            print(f"[SUCCESS] File `{filename}` was successfuly extracted")
            blob = content["blob"]
            bucket.copy_blob(blob, bucket, f"succeded/{filename}")
            blob.delete()

















        # print(f"{found_labels}\n")
        # insert data into db
        # try:
        #     _store_extracted_data(conn, found_labels)
        #     # bucket.copy_blob(new_blob, bucket, f"succeded/{filename}")
        # finally:
        #     conn.close()
    # print(found_labels)



        # gcsDocument = documentai_v1.GcsDocument(
        #     gcs_uri=f"gs://{bucket.name}/{new_blob.name}",
        #     mime_type=new_blob.content_type
        # )

        # request = documentai_v1.ProcessRequest(
        #     name=name,
        #     gcs_document=gcsDocument
        # )

        # response = client.process_document(request=request)
        # document = response.document

        # found_labels = {}

        # for entity in document.entities:
        #     found_labels[entity.type_] = entity.mention_text

        # missing_labels = [label for label in required_labels if not found_labels.get(label)]

        # if len(missing_labels) >= 1:
        #     print(f"File `{filename}` has failed\n")
        #     # bucket.copy_blob(new_blob, bucket, f"failed/{filename}")
        # else:
        #     print(f"File `{filename}` was successfully extracted")
        #     # print(f"{found_labels}\n")
        #     # insert data into db
        #     # try:
        #     #     _store_extracted_data(conn, found_labels)
        #     #     # bucket.copy_blob(new_blob, bucket, f"succeded/{filename}")
        #     # finally:
        #     #     conn.close()
        # print(found_labels)

        # new_blob.delete()
















    # return "OK"

job_processor()