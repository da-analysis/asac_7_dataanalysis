# Databricks notebook source
# Databricks notebook source
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, ArrayType
from datetime import datetime, timezone, timedelta
import requests 
import time 

# 서울시 주요 상권 82장소 AREA_CD 리스트
area_codes = [
    "POI001", "POI002", "POI003", "POI004", "POI005", "POI006", "POI007", "POI009",
    "POI010", "POI013", "POI014", "POI015", "POI016", "POI017", "POI018", "POI019",
    "POI020", "POI021", "POI023", "POI024", "POI025", "POI026", "POI027", "POI029",
    "POI031", "POI032", "POI033", "POI034", "POI035", "POI036", "POI037", "POI038",
    "POI039", "POI040", "POI041", "POI042", "POI043", "POI044", "POI045", "POI046",
    "POI047", "POI048", "POI049", "POI050", "POI051", "POI052", "POI053", "POI054",
    "POI055", "POI056", "POI058", "POI059", "POI060", "POI061", "POI063", "POI064",
    "POI066", "POI067", "POI068", "POI070", "POI071", "POI072", "POI073", "POI074",
    "POI076", "POI077", "POI078", "POI079", "POI080", "POI081", "POI082", "POI083",
    "POI084", "POI114", "POI115", "POI116", "POI117", "POI118", "POI119", "POI120",
    "POI121", "POI122"
]

# 수집 데이터 평탄화 함수 
def flatten_citydata(citydata, collected_time): 
    flat = {
        "AREA_NM": citydata.get("AREA_NM"),
        "AREA_CD": citydata.get("AREA_CD"),
        "AREA_CMRCL_LVL": citydata.get("LIVE_CMRCL_STTS", {}).get("AREA_CMRCL_LVL"),
        "AREA_SH_PAYMENT_CNT": citydata.get("LIVE_CMRCL_STTS", {}).get("AREA_SH_PAYMENT_CNT"),
        "AREA_SH_PAYMENT_AMT_MIN": citydata.get("LIVE_CMRCL_STTS", {}).get("AREA_SH_PAYMENT_AMT_MIN"),
        "AREA_SH_PAYMENT_AMT_MAX": citydata.get("LIVE_CMRCL_STTS", {}).get("AREA_SH_PAYMENT_AMT_MAX"),
        "CMRCL_10_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_10_RATE"),
        "CMRCL_20_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_20_RATE"),
        "CMRCL_30_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_30_RATE"),
        "CMRCL_40_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_40_RATE"),
        "CMRCL_50_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_50_RATE"),
        "CMRCL_60_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_60_RATE"),
        "CMRCL_MALE_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_MALE_RATE"),
        "CMRCL_FEMALE_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_FEMALE_RATE"),
        "CMRCL_PERSONAL_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_PERSONAL_RATE"),
        "CMRCL_CORPORATION_RATE": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_CORPORATION_RATE"),
        "CMRCL_TIME": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_TIME"),
        "collected_time": collected_time
    }
    return flat

def flatten_rsb_list(citydata, collected_time):
    rsbs = citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_RSB", [])
    flat_rsb_rows = [] 
    for rsb in rsbs:
        flat_rsb_rows.append({
            "AREA_NM": citydata.get("AREA_NM"),
            "AREA_CD": citydata.get("AREA_CD"),
            "RSB_LRG_CTGR": rsb.get("RSB_LRG_CTGR"),
            "RSB_MID_CTGR": rsb.get("RSB_MID_CTGR"),
            "RSB_PAYMENT_LVL": rsb.get("RSB_PAYMENT_LVL"),
            "RSB_SH_PAYMENT_CNT": rsb.get("RSB_SH_PAYMENT_CNT"),
            "RSB_SH_PAYMENT_AMT_MIN": rsb.get("RSB_SH_PAYMENT_AMT_MIN"),
            "RSB_SH_PAYMENT_AMT_MAX": rsb.get("RSB_SH_PAYMENT_AMT_MAX"),
            "RSB_MCT_CNT": rsb.get("RSB_MCT_CNT"),
            "RSB_MCT_TIME": rsb.get("RSB_MCT_TIME"),
            "CMRCL_TIME": citydata.get("LIVE_CMRCL_STTS", {}).get("CMRCL_TIME"),
            "collected_time": collected_time
        })
    return flat_rsb_rows

# PySpark 세션 생성
spark = SparkSession.builder \
    .appName("API Data Collection for Commercial district status data") \
    .getOrCreate()

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

# Delta 테이블 이름 
catalog_table_1 = "bronze.api_seoulcity.`서울시_실시간_상권현황`"
catalog_table_2= "bronze.api_seoulcity.`서울시_실시간_업종별_상권현황`"

# 데이터 스키마 정의
area_schema = StructType([
    StructField("AREA_NM", StringType(), True),
    StructField("AREA_CD", StringType(), True), 
    StructField("AREA_CMRCL_LVL", StringType(), True),
    StructField("AREA_SH_PAYMENT_CNT", StringType(), True),
    StructField("AREA_SH_PAYMENT_AMT_MIN", StringType(), True),
    StructField("AREA_SH_PAYMENT_AMT_MAX", StringType(), True),
    StructField("CMRCL_10_RATE", FloatType(), True),
    StructField("CMRCL_20_RATE", FloatType(), True),
    StructField("CMRCL_30_RATE", FloatType(), True),
    StructField("CMRCL_40_RATE", FloatType(), True),
    StructField("CMRCL_50_RATE", FloatType(), True),
    StructField("CMRCL_60_RATE", FloatType(), True),
    StructField("CMRCL_MALE_RATE", FloatType(), True),
    StructField("CMRCL_FEMALE_RATE", FloatType(), True),
    StructField("CMRCL_PERSONAL_RATE", FloatType(), True),
    StructField("CMRCL_CORPORATION_RATE", FloatType(), True),
    StructField("CMRCL_TIME", StringType(), True),
    StructField("collected_time", StringType(), True), # 수집 시간 필드 
    StructField("id", IntegerType(), True)             # ID 필드 
])

rsb_schema = StructType([
    StructField("AREA_NM", StringType(), True),
    StructField("AREA_CD", StringType(), True),
    StructField("RSB_LRG_CTGR", StringType(), True),
    StructField("RSB_MID_CTGR", StringType(), True),
    StructField("RSB_PAYMENT_LVL", StringType(), True),
    StructField("RSB_SH_PAYMENT_CNT", IntegerType(), True),
    StructField("RSB_SH_PAYMENT_AMT_MIN", IntegerType(), True),
    StructField("RSB_SH_PAYMENT_AMT_MAX", IntegerType(), True),
    StructField("RSB_MCT_CNT", IntegerType(), True),
    StructField("RSB_MCT_TIME", StringType(), True),
    StructField("CMRCL_TIME", StringType(), True),
    StructField("collected_time", StringType(), True), # 수집 시간 필드 
    StructField("id", IntegerType(), True)             # ID 필드 
])

# Delta 테이블 초기화 함수 
def initialize_delta_table(table_name, schema):
    try: 
        spark.table(table_name)
        print(f"Delta 테이블 '{table_name}'이 이미 존재합니다.")
    except Exception:
        print(f"Delta 테이블 '{table_name}'이 존재하지 않습니다. 새로 생성합니다.")
        empty_df = spark.createDataFrame([], schema)
        empty_df.write.format("delta").mode("overwrite").saveAsTable(table_name)
        print(f"Delta 테이블 '{table_name}' 생성 완료.")

# 데이터 저장 함수
def save_to_delta(df, table_name):
    df.write.format("delta").mode("append").saveAsTable(table_name)
    print(f"[INFO] Delta 테이블 '{table_name}'에 {df.count()}개 데이터 저장 완료.")

# 중복 제거 함수 
def remove_duplicates(table_name):
    try: 
        # delta 테이블 불러오기 
        df = spark.table(table_name)

        # 테이블별 중복 제거 기준 컬럼 지정 
        if table_name == catalog_table_1:
            dedup_columns = [
                "AREA_NM", "AREA_CD", "AREA_CMRCL_LVL", "AREA_SH_PAYMENT_CNT",
                "AREA_SH_PAYMENT_AMT_MIN", "AREA_SH_PAYMENT_AMT_MAX",
                "CMRCL_10_RATE", "CMRCL_20_RATE", "CMRCL_30_RATE",
                "CMRCL_40_RATE", "CMRCL_50_RATE", "CMRCL_60_RATE",
                "CMRCL_MALE_RATE", "CMRCL_FEMALE_RATE", "CMRCL_PERSONAL_RATE",
                "CMRCL_CORPORATION_RATE", "CMRCL_TIME", "collected_time"
            ]
        elif table_name == catalog_table_2:
            dedup_columns = [
                "AREA_NM", "AREA_CD", "RSB_LRG_CTGR", "RSB_MID_CTGR",
                "RSB_PAYMENT_LVL", "RSB_SH_PAYMENT_CNT", "RSB_SH_PAYMENT_AMT_MIN",
                "RSB_SH_PAYMENT_AMT_MAX", "RSB_MCT_CNT", "RSB_MCT_TIME",
                "CMRCL_TIME", "collected_time"
            ]
        else:
            print(f"[WARNING] 중복 제거 기준이 정의되지 않은 테이블입니다: {table_name}")
            return 

        # 중복 제거 및 delta table 업데이트 
        deduplicated_df = df.dropDuplicates(dedup_columns)
        deduplicated_df.write.format("delta").mode("overwrite").saveAsTable(table_name)
        print(f"[INFO] 중복 제거 완료: {deduplicated_df.count()}개 데이터가 남았습니다.")

    except Exception as e:
        print(f"[ERROR] 중복 제거 중 오류 발생: {e}")

# 상권현황 데이터 수집 함수 
def collect_seoul_commercial_data(api_keys, area_codes): 
    
    # 수집 데이터 리스트
    all_location_status_rows = [] 
    all_location_industry_rows = [] 

    # id 초기화 & api 요청 횟수 카운트  
    location_id = 0
    industry_id = 0
    request_count = 0
    
    for area_code in area_codes:
        if request_count >= len(api_keys) * 1000: 
            print("모든 API 키의 일일 호출 한도를 초과했습니다.")
            break 

        api_key = api_keys[min(request_count // 1000, len(api_keys) - 1)]  
        url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/citydata_cmrcl/1/5/{area_code}"

        try:
            response = requests.get(url, timeout=10)
            request_count += 1
            response.raise_for_status()
            data = response.json()

            # 유효성 검사
            if data.get("RESULT", {}).get("CODE") == "ERROR-500":
                print(f"[{area_code}] 유효하지 않은 장소코드 또는 서버 오류입니다.")
                continue 
            
            # LIVE_CMRCL_STTS(상권현황) 존재 여부 확인  
            elif "LIVE_CMRCL_STTS" not in data:
                print(f"[{area_code}] 상권 정보(LIVE_CMRCL_STTS)가 없습니다.")
                continue

            # 수집 시간 추가 
            collected_time = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
            data["collected_time"] = collected_time

            # 평탄화 함수 적용 및 ID 값 부여 
            location_status_row = flatten_citydata(data, collected_time)
            location_id += 1
            location_status_row["id"] = location_id

            location_industry_rows = flatten_rsb_list(data, collected_time)
            for row in location_industry_rows:
                industry_id += 1
                row["id"] = industry_id

            all_location_status_rows.append(location_status_row)
            all_location_industry_rows.extend(location_industry_rows)

            print(f"[{area_code}] 수집 완료")
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"[{area_code}] 요청 실패: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"[{area_code}] 오류 발생: {e}")
            time.sleep(2)

    return all_location_status_rows, all_location_industry_rows

# API 키 리스트 (최대 1000건/키)
api_keys = [
    "API_KEY_1",
    "API_KEY_2"
] 

# 데이터 수집 
all_location_status_rows, all_location_industry_rows = collect_seoul_commercial_data(api_keys, area_codes) 

# dalta table 초기화 
initialize_delta_table(catalog_table_1, area_schema)
initialize_delta_table(catalog_table_2, rsb_schema)

# 수집된 데이터 저장 
if all_location_status_rows:
    area_df = spark.createDataFrame(all_location_status_rows, schema=area_schema) 
    save_to_delta(area_df, catalog_table_1)
    print("[INFO] Delta 테이블에 최종 데이터 저장 완료.")
else: 
    print("수집된 데이터가 없습니다.")

if all_location_industry_rows:
    rsb_df = spark.createDataFrame(all_location_industry_rows, schema=rsb_schema)  
    save_to_delta(rsb_df, catalog_table_2) 
    print("[INFO] Delta 테이블에 최종 데이터 저장 완료.") 
else: 
    print("수집된 데이터가 없습니다.") 

# 중복 제거 후 업데이트
remove_duplicates(catalog_table_1)
remove_duplicates(catalog_table_2) 
