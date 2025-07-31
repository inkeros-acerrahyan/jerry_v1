from typing import List
from google.cloud import storage, documentai_v1
from google.cloud.storage import Blob
from google.cloud.sql.connector import Connector
# import psycopg

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

connector = Connector()
conn = connector.connect(
    connection_name,
    pg_driver,
    user=user,
    password=password,
    db=db_name
)
cur = conn.cursor()
cur.execute("SELECT * FROM test_table")
rows = cur.fetchall()
for row in rows:
    print(row)

cur.close()
conn.close()






# # create client with creds
# pg_connection = psycopg.connect(
#     conninfo="postgresql://postgres:gamalziplockshisfartstomarinateinthefridgebeforereleasingthemintheoffice@localhost:5435/jerry_v1_extracted_db"
# )
# # create table if not exists query
# cur = pg_connection.cursor()
# cur.execute(
#     query="SELECT * FROM test_table"
# )

# rows = cur.fetchall()
# for row in rows:
#     print(row)

# cur.close()
# pg_connection.close()






def job_processor(request=None):
    # get all files to be processed from bucket gs://bucket/to-be-processed

    client = documentai_v1.DocumentProcessorServiceClient()

    name = f"projects/{project}/locations/{location}/processors/{processor_id}"

    storageClient = storage.Client()

    bucket = storage.Bucket.from_uri("gs://jerry_v1_upload", client=storageClient)

    blobs: List[Blob] = bucket.list_blobs(max_results=3, prefix="to_process/")
    # --------------------------------------------------------------------------

    # for each file move from to-be-processed to processing and send to document ai for extraction
    # if success
    #   move file from to-be-processed to processed inside a directory of current date the job is running on 
    #       and insert data into db with url of the file inside the processed
    # else
    #   move file from processing to failed, go next


    for blob in blobs:
        filename = blob.name.split("/")[1]
        new_blob = bucket.copy_blob(blob, bucket, f"processing/{filename}")
        # blob.delete()

        gcsDocument = documentai_v1.GcsDocument(
            gcs_uri=f"gs://{bucket.name}/{new_blob.name}",
            mime_type=new_blob.content_type
        )

        request = documentai_v1.ProcessRequest(
            name=name,
            gcs_document=gcsDocument
        )

        response = client.process_document(request=request)
        document = response.document

        found_labels = {}

        for entity in document.entities:
            found_labels[entity.type_] = entity.mention_text

        missing_labels = [label for label in required_labels if not found_labels.get(label)]

        if len(missing_labels) >= 1:
            print(f"File `{filename}` has failed\n")
            bucket.copy_blob(new_blob, bucket, f"failed/{filename}")
        else:
            print(f"File `{filename}` was successfully extracted")
            print(f"{found_labels}\n")
            bucket.copy_blob(new_blob, bucket, f"succeded/{filename}")
            # insert data into db

        new_blob.delete()
















    # return "OK"

# job_processor()