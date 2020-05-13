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
PATH_KAFKA = os.environ["KAFKA"]
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

query2 = sdf \
         .selectExpr("CAST(PhoneId AS STRING) AS key", "to_json(struct(*)) AS value") \
         .writeStream \
         .format("kafka") \
         .outputMode("update") \
         .trigger(processingTime='5 seconds') \
         .option("checkpointLocation", "/home/cerezamo/kafka/kafka/checkpoint") \
         .option("kafka.bootstrap.servers", "localhost:9092") \
         .option("topic", "antennesOutput") \
         .start()



# query1 = sdf.withColumn("key", lit(0)) \
#          .selectExpr("CAST(key AS STRING) AS key", "to_json(struct(*)) AS value") \
#          .writeStream \
#          .format("console") \
#          .outputMode("complete") \
#          .option("truncate", "false") \
#          .trigger(processingTime='20 seconds') \
#          .option("checkpointLocation", "/home/cerezamo/kafka/kafka/checkpoint") \
#          .start()

# query1 = sdf \
#          .selectExpr("CAST(PhoneId AS STRING) AS key", "to_json(struct(*)) AS value") \
#          .writeStream \
#          .format("console") \
#          .outputMode("complete") \
#          .trigger(processingTime='10 seconds') \
#          .option("checkpointLocation", os.path.join(PATH_KAFKA, "checkpoint")) \
#          .start()


# query2 = sdf \
#          .selectExpr("CAST(PhoneId AS STRING) AS key", "to_json(struct(*)) AS value") \
#          .write \
#          .format("kafka") \
#          .outputMode("update") \
# <<<<<<< HEAD
#          .trigger(processingTime='20 seconds') \
#          .option("checkpointLocation", "/home/cerezamo/kafka/kafka/checkpoint") \
# =======
#          .option("checkpointLocation", os.path.join(PATH_KAFKA, "checkpoint")) \
# >>>>>>> 35cd79e7790b8e986ad49f31184b79f2a358bdac
#          .option("kafka.bootstrap.servers", "localhost:9092") \
#          .option("topic", "antennesOutput") \
#          .start()


# query2 = sdf \
#          .map(_.toString.getBytes).toDF("x") \
#          .writeStream \
#          .format("kafka") \
#          .outputMode("complete") \
#          .trigger(processingTime='20 seconds') \
#          .option("checkpointLocation", "$KAFKA/checkpoint") \
#          .option("kafka.bootstrap.servers", "localhost:9092") \
#          .option("topic", "antennesOutput") \
#          .start()


# # .trigger(processingTime='2 seconds')
# #  query1 = sdf_loc.withColumnRenamed(['avg(x)', 'x'], ['avg(y)', 'y']) \
# #          .selectExpr("CAST(t AS STRING) AS key", "to_json(struct(*)) AS value")
# #          .writeStream.format("console").outputMode("update").start()