import os
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.5 pyspark-shell'
import pyspark
import os
import re
from kafka import SimpleProducer, KafkaClient
from kafka import KafkaProducer
from pyspark.streaming import StreamingContext
from pyspark.sql import Column, DataFrame, Row, SparkSession
from pyspark.streaming.kafka import KafkaUtils
from pyspark import SparkConf, SparkContext
import time 
from pyspark.sql import SparkSession
from pyspark.sql.functions import unix_timestamp, col
from pyspark.sql import Window
from pyspark.sql.functions import *
spark = SparkSession.builder \
  .appName("Spark Structured Streaming from Kafka") \
  .getOrCreate()
receiveAntennes = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", "localhost:9092") \
  .option("subscribe", "antennesInput") \
  .option("startingOffsets", "latest") \
  .load() \
  .selectExpr("CAST(value AS STRING)")
from pyspark.sql.types import *
schema_ant = StructType([StructField("t", IntegerType()),
                     StructField("AntennaId", IntegerType()),
                     StructField("EventCode", IntegerType()),
                     StructField("PhoneId", IntegerType()),
                     StructField("x", FloatType()),
                     StructField("y", FloatType()),
                     StructField("TileId", IntegerType()),
                     StructField("timestamp", StringType()),])
def parse_data_from_kafka_message(sdf, schema):
    from pyspark.sql.functions import split
    assert sdf.isStreaming == True, "DataFrame doesn't receive streaming data"
    col = split(sdf['value'], ',')
    for idx, field in enumerate(schema):
        sdf = sdf.withColumn(field.name, col.getItem(idx).cast(field.dataType))
    return sdf.select([field.name for field in schema])
sdfAntennes = parse_data_from_kafka_message(receiveAntennes, schema_ant)
sdfAntennes = sdfAntennes.withColumn('timestamp',unix_timestamp(sdfAntennes.timestamp, 'MM-dd-yyyy HH:mm:ss').cast(TimestampType()).alias("timestamp"))
sdfAntennes = sdfAntennes.where("EventCode!=1")
sdfAntennes = sdfAntennes.withColumn('x', sdfAntennes.x/1000).withColumn('y', sdfAntennes.y/1000)

#sdfLoc = sdfAntennes.withWatermark("time", "2 minutes").groupBy("PhoneId", window("timestamp", "1 minute","1 minute")).avg()
#sdfLoc3 = sdfAntennes.groupBy("PhoneId", window("timestamp", "2 minutes","1 minutes")).mean()
# Marche en notebook mais pas la ????????? WHYYYYY 
sdf = sdfAntennes.groupBy("PhoneId").mean()
sdf = sdf.select(col("PhoneId").alias("PhoneId"),col("avg(x)").alias("x"),col("avg(y)").alias("y"))
#sdf = sdf.withColumn("key", lit(0))
# sdf = sdf.groupBy('key').agg(collect_list("PhoneId").alias("PhoneId"), collect_list("x").alias("x"),collect_list("y").alias("y"))


def send_df_to_dashboard(df):
  import requests
  import json
  x = [str(t.x) for t in df.select("x").collect()]
  y = [p.y for p in df.select("y").collect()]
  PhoneId = [p.PhoneId for p in df.select("PhoneId").collect()]
  url = 'http://localhost:5001/updateData'
  request_data = {'PhoneId': str(PhoneId), 'x': str(x), 'y': str(y)}
  response = requests.post(url, data=request_data)

send_df_to_dashboard(sdf)



sdf.writeStream.format('console').start()