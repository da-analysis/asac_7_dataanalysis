# Databricks notebook source
# MAGIC %md
# MAGIC # 1. 업로드

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, LongType
from pyspark.sql.functions import row_number
from pyspark.sql.window import Window
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import time

# PySpark 세션 생성
spark = SparkSession.builder \
    .appName("API Data Collection for 행정동 단위 상가업소 조회") \
    .config("spark.databricks.delta.schema.autoMerge.enabled", "true") \
    .getOrCreate()

# API URL 및 테이블
url = "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInDong"
catalog_table = "bronze.api_public.`행정동_단위_상가업소_조회`"

# KST 설정
KST = timezone(timedelta(hours=9))

# 스키마 정의
schema = StructType([
    StructField("ID", LongType(), True),
    StructField("bizesId", StringType(), True),
    StructField("bizesNm", StringType(), True),
    StructField("brchNm", StringType(), True),
    StructField("indsLclsCd", StringType(), True),
    StructField("indsLclsNm", StringType(), True),
    StructField("indsMclsCd", StringType(), True),
    StructField("indsMclsNm", StringType(), True),
    StructField("indsSclsCd", StringType(), True),
    StructField("indsSclsNm", StringType(), True),
    StructField("ksicCd", StringType(), True),
    StructField("ksicNm", StringType(), True),
    StructField("ctprvnCd", StringType(), True),
    StructField("ctprvnNm", StringType(), True),
    StructField("signguCd", StringType(), True),
    StructField("signguNm", StringType(), True),
    StructField("adongCd", StringType(), True),
    StructField("adongNm", StringType(), True),
    StructField("ldongCd", StringType(), True),
    StructField("ldongNm", StringType(), True),
    StructField("lnnoCd", StringType(), True),
    StructField("plotSctCd", StringType(), True),
    StructField("plotSctNm", StringType(), True),
    StructField("lnoMnno", StringType(), True),
    StructField("lnoSlno", StringType(), True),
    StructField("lnnoAdr", StringType(), True),
    StructField("rdnmCd", StringType(), True),
    StructField("rdnm", StringType(), True),
    StructField("bldMnno", StringType(), True),
    StructField("bldSlno", StringType(), True),
    StructField("bldMngNo", StringType(), True),
    StructField("bldNm", StringType(), True),
    StructField("rdnmAdr", StringType(), True),
    StructField("oldZipcd", StringType(), True),
    StructField("newZipcd", StringType(), True),
    StructField("dongNo", StringType(), True),
    StructField("flrNo", StringType(), True),
    StructField("hoNo", StringType(), True),
    StructField("lon", StringType(), True),
    StructField("lat", StringType(), True),
    StructField("x", StringType(), True),
    StructField("y", StringType(), True),
    StructField("collected_time", StringType(), True)
])

# Delta 테이블 초기화
def initialize_delta_table():
    try:
        spark.table(catalog_table)
        print(f"Delta 테이블 '{catalog_table}'이 이미 존재합니다.")
    except Exception:
        print(f"Delta 테이블 '{catalog_table}'이 존재하지 않습니다. 생성합니다.")
        empty_df = spark.createDataFrame([], schema)
        empty_df.write.format("delta").mode("overwrite").saveAsTable(catalog_table)
        print(f"Delta 테이블 '{catalog_table}' 생성 완료.")

# 데이터 저장 함수
def save_to_delta(data):
    if data:
        df = spark.createDataFrame(data, schema=schema).dropDuplicates()
        if "ID" in df.columns:
            df = df.drop("ID")
        window_spec = Window.orderBy("bizesId")
        df = df.withColumn("ID", row_number().over(window_spec).cast(LongType()))
        cols = df.columns
        cols.remove("ID")
        df = df.select(["ID"] + cols)
        df.write.format("delta") \
            .option("mergeSchema", "true") \
            .mode("append") \
            .saveAsTable(catalog_table)
        print(f"Delta 테이블 저장 완료: {len(data)} 개")

# API 수집 함수
def collect_data(divId, key):
    page = 1
    all_data = []
    print(f"\n🚀 '{divId}' - '{key}' 수집 시작")
    while True:
        params = {
            'serviceKey': "TdB+le3iJsraWH2A+djC2/JyhLNKTj7Q7OSyWcR4t93CLpothF5v5ccho4tiaT4/s9Ws9WWNEDQ/dQcpbi7C6A==",
            'type': 'json',
            'pageNo': page,
            'numOfRows': 1000,
            'divId': divId,
            'key': key
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get("body", {}).get("items", [])
            if not items:
                print(f"📭 Page {page}: 데이터 없음.")
                break
            collected_time = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
            for item in items:
                item['collected_time'] = collected_time
            all_data.extend(items)
            print(f"📄 Page {page}: {len(items)}개 수집, 누적 {len(all_data)}")
            if len(items) < 1000:
                break
            page += 1
            time.sleep(0.5)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 오류 - {e}. 재시도...")
            time.sleep(2)

    if all_data:
        save_to_delta(all_data)
        print(f"✅ '{divId}' - '{key}' 저장 완료.")
    else:
        print(f"❌ '{divId}' - '{key}' 데이터 없음.")

# 병렬 수집 실행 함수
def run_parallel_collection(divId, keys, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(collect_data, divId, key): key for key in keys}
        for future in as_completed(futures):
            key = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"❌ '{divId}' - '{key}' 처리 중 예외 발생: {e}")

# 수집 대상 리스트
ctprvnCd_values = ["11", "26", "27", "28", "29", "30", "31", "36", "41", "42", "43", "44", "45", "46", "47", "48", "50"]
indsLclsCd_values = ["A1", "A2", "A3", "A4", "A5", "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "B1"]
indsMclsCd_values = [
    "G202","G203","G204","G205","G206","G207","G208","G209","G210","G211",
    "G212","G213","G214","G215","G216","G217","G218","G219","G220","G221",
    "G222","I101","I102","I201","I202","I203","I204","I205","I206","I207",
    "I210","I211","I212","L102","M103","M104","M105","M106","M107","M109",
    "M111","M112","M113","M114","M115","N101","N102","N103","N104","N105",
    "N107","N108","N109","N110","N111","P105","P106","P107","Q101","Q102",
    "Q104","R102","R103","R104","S201","S202","S203","S204","S205","S206",
    "S207","S208","S209","S210","S211"
]

indsSclsCd_values = [
    "G20201","G20202","G20301","G20404","G20405","G20499","G20501","G20502",
    "G20503","G20504","G20505","G20506","G20507","G20508","G20509","G20601",
    "G20602","G20603","G20604","G20701","G20801","G20802","G20803","G20901",
    "G20902","G20903","G20904","G20905","G20906","G20907","G20908","G20909",
    "G20910","G20911","G21001","G21002","G21003","G21099","G21101","G21201",
    "G21202","G21203","G21301","G21302","G21303","G21304","G21305","G21306",
    "G21401","G21402","G21403","G21501","G21502","G21503","G21601","G21602",
    "G21603","G21701","G21801","G21802","G21901","G22001","G22199","G22201",
    "I10101","I10102","I10103","I10104","I10201","I10299","I20101","I20102",
    "I20103","I20104","I20105","I20106","I20107","I20108","I20109","I20110",
    "I20111","I20112","I20113","I20199","I20201","I20202","I20301","I20302",
    "I20303","I20399","I20401","I20402","I20403","I20499","I20501","I20599",
    "I20601","I20701","I20702","I21001","I21002","I21003","I21004","I21005",
    "I21006","I21007","I21008","I21099","I21101","I21102","I21103","I21104",
    "I21201","L10203","M10301","M10302","M10303","M10306","M10307","M10399",
    "M10401","M10402","M10499","M10501","M10502","M10503","M10504","M10599",
    "M10601","M10703","M10901","M10902","M10903","M10904","M10999","M11101",
    "M11201","M11202","M11203","M11204","M11301","M11401","M11502","M11504",
    "N10101","N10201","N10202","N10203","N10301","N10401","N10402","N10403",
    "N10501","N10599","N10703","N10799","N10802","N10805","N10901","N10999",
    "N11001","N11002","N11003","N11004","N11099","N11101","N11102","N11199",
    "P10501","P10601","P10603","P10605","P10607","P10609","P10611","P10613",
    "P10615","P10617","P10619","P10621","P10623","P10625","P10627","P10629",
    "P10701","P10799","Q10101","Q10102","Q10103","Q10104","Q10105","Q10201",
    "Q10202","Q10203","Q10204","Q10205","Q10206","Q10207","Q10208","Q10209",
    "Q10210","Q10211","Q10212","Q10402","R10202","R10306","R10307","R10308",
    "R10309","R10310","R10311","R10312","R10313","R10314","R10316","R10402",
    "R10404","R10405","R10406","R10407","R10408","R10409","R10410","R10414",
    "R10499","S20101","S20201","S20301","S20302","S20401","S20501","S20601",
    "S20602","S20603","S20699","S20701","S20702","S20703","S20801","S20802",
    "S20803","S20901","S20902","S21001","S21002","S21101","S21105"]

# 실행
initialize_delta_table()

run_parallel_collection("ctprvnCd", ctprvnCd_values)
run_parallel_collection("indsLclsCd", indsLclsCd_values)
run_parallel_collection("indsMclsCd", indsMclsCd_values)
run_parallel_collection("indsSclsCd", indsSclsCd_values)


# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM  bronze.api_public.`행정동_단위_상가업소_조회`;

# COMMAND ----------

# MAGIC %md
# MAGIC

# COMMAND ----------

from pyspark.sql.functions import col, to_timestamp
from pyspark.sql.types import DoubleType

# Bronze 테이블에서 데이터 불러오기
bronze_df = spark.table("bronze.api_public.`행정동_단위_상가업소_조회`")

# 전처리: 중복 제거 및 형 변환
silver_df = bronze_df \
    .dropDuplicates(["bizesId"]) \
    .withColumn("x", col("x").cast(DoubleType())) \
    .withColumn("y", col("y").cast(DoubleType())) \
    .withColumn("lon", col("lon").cast(DoubleType())) \
    .withColumn("lat", col("lat").cast(DoubleType())) \
    .withColumn("collected_time", to_timestamp("collected_time", "yyyy-MM-dd HH:mm:ss"))

# Silver Layer 저장 (Delta + schema auto merge)
silver_df.write \
    .format("delta") \
    .option("mergeSchema", "true") \
    .mode("overwrite") \
    .saveAsTable("silver.public.`행정동_단위_상가업소_조회`")

print("✅ Silver Layer 저장 완료: 'silver.public.행정동_단위_상가업소_조회'")

