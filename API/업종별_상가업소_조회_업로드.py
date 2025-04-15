# Databricks notebook source
# MAGIC %md
# MAGIC # 1. 업로드 

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType
from pyspark.sql.functions import row_number
from pyspark.sql.window import Window
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import time

# ✅ PySpark 세션 생성
spark = SparkSession.builder \
    .appName("API Data Collection for 업종별 상가업소 조회") \
    .config("spark.databricks.delta.schema.autoMerge.enabled", "true") \
    .getOrCreate()

# ✅ API URL 및 Delta 테이블
url = "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInUpjong"
catalog_table = "bronze.api_public.`업종별_상가업소_조회`"

# ✅ 데이터 스키마 정의
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
    StructField("lnoCd", StringType(), True),
    StructField("plotSctCd", StringType(), True),
    StructField("plotSctNm", StringType(), True),
    StructField("lnoMnno", StringType(), True),
    StructField("lnoSlno", StringType(), True),
    StructField("lnoAdr", StringType(), True),
    StructField("rdnmCd", StringType(), True),
    StructField("rdnm", StringType(), True),
    StructField("bldMnno", StringType(), True),
    StructField("bldSlno", StringType(), True),
    StructField("bldMngNo", StringType(), True),
    StructField("bldMngNm", StringType(), True),
    StructField("rdnmAdr", StringType(), True),
    StructField("oldZipcd", StringType(), True),
    StructField("newZipcd", StringType(), True),
    StructField("dongNo", StringType(), True),
    StructField("flrNo", StringType(), True),
    StructField("hoNo", StringType(), True),
    StructField("lon", StringType(), True),
    StructField("lat", StringType(), True),
    StructField("x", DoubleType(), True),
    StructField("y", DoubleType(), True),
    StructField("collected_time", StringType(), True)
])

# ✅ Delta 테이블 초기화 함수
def initialize_delta_table():
    try:
        spark.table(catalog_table)
        print(f"Delta 테이블 '{catalog_table}'이 이미 존재합니다.")
    except Exception:
        print(f"Delta 테이블 '{catalog_table}'이 존재하지 않습니다. 새로 생성합니다.")
        empty_df = spark.createDataFrame([], schema)
        empty_df.write.format("delta").mode("overwrite").saveAsTable(catalog_table)
        print(f"Delta 테이블 '{catalog_table}' 생성 완료.")

# ✅ 안전한 float 변환
def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# ✅ 페이지별 저장 함수
def save_to_delta(data):
    if data:
        for item in data:
            item["x"] = safe_float(item.get("x"))
            item["y"] = safe_float(item.get("y"))

        df = spark.createDataFrame(data, schema=schema)

        # ID 컬럼 제거 후 재생성
        if "ID" in df.columns:
            df = df.drop("ID")

        window_spec = Window.orderBy("bizesId")
        df = df.withColumn("ID", row_number().over(window_spec).cast(LongType()))

        # 컬럼 순서 정리: ID가 맨 앞
        columns = df.columns
        columns.remove("ID")
        df = df.select(["ID"] + columns)

        # 전체 중복 제거
        df = df.dropDuplicates(df.columns)

        df.write.format("delta") \
            .option("mergeSchema", "true") \
            .mode("append") \
            .saveAsTable(catalog_table)

        print(f"✅ Delta 테이블 저장 완료: {len(data)}개 저장됨.")

# ✅ 시간대 설정
KST = timezone(timedelta(hours=9))

# ✅ API 수집 함수
def collect_data(key):
    page = 1
    print(f"\n📦 '{key}' 업종 데이터 수집 시작")

    while True:
        params = {
            'serviceKey': "입력하세요",
            'type': 'json',
            'pageNo': page,
            'numOfRows': 1000,
            'divId': 'indsLclsCd',
            'key': key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get("body", {}).get("items", [])

            if not items:
                print(f"📭 Page {page}: 데이터 없음. 종료.")
                break

            collected_time = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
            for item in items:
                item["collected_time"] = collected_time

            save_to_delta(items)
            print(f"📄 Page {page}: {len(items)}개 저장 완료.")

            if len(items) < 1000:
                print("✅ 마지막 페이지 도달.")
                break

            page += 1
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Page {page} 오류 - {e}. 재시도...")
            time.sleep(2)

# ✅ 병렬 수집 실행 함수
def run_parallel_collection(keys, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {executor.submit(collect_data, key): key for key in keys}

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                future.result()
                print(f"✅ '{key}' 업종 수집 완료.")
            except Exception as e:
                print(f"❌ '{key}' 업종 수집 중 오류: {e}")

# ✅ 업종 코드 리스트
industry_keys = ["G2", "I1", "I2", "L1", "M1", "N1", "P1", "Q1", "R1", "S2"]

# ✅ 실행
initialize_delta_table()
run_parallel_collection(industry_keys, max_workers=5)


# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM  bronze.api_public.`업종별_상가업소_조회`;

# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC

# COMMAND ----------

from pyspark.sql.functions import col, to_timestamp
from pyspark.sql.types import DoubleType

# Bronze 테이블에서 데이터 로드
bronze_df = spark.table("bronze.api_public.`업종별_상가업소_조회`")

# 전처리 및 스키마 정리
silver_df = bronze_df \
    .dropDuplicates(["bizesId"]) \
    .withColumn("x", col("x").cast(DoubleType())) \
    .withColumn("y", col("y").cast(DoubleType())) \
    .withColumn("lon", col("lon").cast(DoubleType())) \
    .withColumn("lat", col("lat").cast(DoubleType())) \
    .withColumn("collected_time", to_timestamp("collected_time", "yyyy-MM-dd HH:mm:ss"))

# Silver 테이블로 저장 (스키마 자동 병합 허용)
silver_df.write \
    .format("delta") \
    .option("mergeSchema", "true") \
    .mode("overwrite") \
    .saveAsTable("silver.public.`업종별_상가업소_조회`")

print("✅ Silver Layer 저장 완료: 'silver.public.업종별_상가업소_조회'")

