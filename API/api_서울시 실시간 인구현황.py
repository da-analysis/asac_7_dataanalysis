# Databricks notebook source
# Databricks notebook source
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType 
from datetime import datetime, timezone, timedelta
import requests
import time 

# 서울시 주요 상권 120장소 AREA_CD 리스트
area_codes_population = [
    "POI001", "POI002", "POI003", "POI004", "POI005", "POI006", "POI007", "POI008",
    "POI009", "POI010", "POI011", "POI012", "POI013", "POI014", "POI015", "POI016",
    "POI017", "POI018", "POI019", "POI020", "POI021", "POI023", "POI024", "POI025",
    "POI026", "POI027", "POI029", "POI030", "POI031", "POI032", "POI033", "POI034",
    "POI035", "POI036", "POI037", "POI038", "POI039", "POI040", "POI041", "POI042",
    "POI043", "POI044", "POI045", "POI046", "POI047", "POI048", "POI049", "POI050",
    "POI051", "POI052", "POI053", "POI054", "POI055", "POI056", "POI058", "POI059",
    "POI060", "POI061", "POI063", "POI064", "POI066", "POI067", "POI068", "POI070",
    "POI071", "POI072", "POI073", "POI074", "POI076", "POI077", "POI078", "POI079",
    "POI080", "POI081", "POI082", "POI083", "POI084", "POI085", "POI086", "POI087",
    "POI088", "POI089", "POI090", "POI091", "POI092", "POI093", "POI094", "POI095",
    "POI096", "POI098", "POI099", "POI100", "POI101", "POI102", "POI103", "POI104",
    "POI105", "POI106", "POI107", "POI108", "POI109", "POI110", "POI111", "POI112",
    "POI113", "POI114", "POI115", "POI116", "POI117", "POI118", "POI119", "POI120",
    "POI121", "POI122", "POI123", "POI124", "POI125", "POI126", "POI127", "POI128"
]

# 수집 데이터 평탄화 함수 
def flatten_live_ppltn(citydata, collected_time):
    row = citydata.get("SeoulRtd.citydata_ppltn", [{}])[0]
    flat = {
        "AREA_NM": row.get("AREA_NM"),
        "AREA_CD": row.get("AREA_CD"),
        "AREA_CONGEST_LVL": row.get("AREA_CONGEST_LVL"),
        "AREA_CONGEST_MSG": row.get("AREA_CONGEST_MSG"),
        "AREA_PPLTN_MIN": row.get("AREA_PPLTN_MIN"),
        "AREA_PPLTN_MAX": row.get("AREA_PPLTN_MAX"),
        "MALE_PPLTN_RATE": row.get("MALE_PPLTN_RATE"),
        "FEMALE_PPLTN_RATE": row.get("FEMALE_PPLTN_RATE"),
        "PPLTN_RATE_0": row.get("PPLTN_RATE_0"),
        "PPLTN_RATE_10": row.get("PPLTN_RATE_10"),
        "PPLTN_RATE_20": row.get("PPLTN_RATE_20"),
        "PPLTN_RATE_30": row.get("PPLTN_RATE_30"),
        "PPLTN_RATE_40": row.get("PPLTN_RATE_40"),
        "PPLTN_RATE_50": row.get("PPLTN_RATE_50"),
        "PPLTN_RATE_60": row.get("PPLTN_RATE_60"),
        "PPLTN_RATE_70": row.get("PPLTN_RATE_70"),
        "RESNT_PPLTN_RATE": row.get("RESNT_PPLTN_RATE"),
        "NON_RESNT_PPLTN_RATE": row.get("NON_RESNT_PPLTN_RATE"),
        "REPLACE_YN": row.get("REPLACE_YN"),
        "PPLTN_TIME": row.get("PPLTN_TIME"),
        "FCST_YN": row.get("FCST_YN"),
        "collected_time": collected_time
    }
    return flat 

def flatten_fcst_ppltn(citydata, collected_time):
    row = citydata.get("SeoulRtd.citydata_ppltn", [{}])[0]
    area_nm = row.get("AREA_NM") 
    area_cd = row.get("AREA_CD")
    fcst_list = row.get("FCST_PPLTN", [])
    flat_list = []
    for fcst in fcst_list:
        flat_list.append({
            "AREA_NM": area_nm,
            "AREA_CD": area_cd,
            "FCST_TIME": fcst.get("FCST_TIME"),
            "FCST_CONGEST_LVL": fcst.get("FCST_CONGEST_LVL"),
            "FCST_PPLTN_MIN": fcst.get("FCST_PPLTN_MIN"),
            "FCST_PPLTN_MAX": fcst.get("FCST_PPLTN_MAX"),
            "PPLTN_TIME": row.get("PPLTN_TIME"), 
            "collected_time": collected_time
        }) 
    return flat_list

# PySpark 세션 생성
spark = SparkSession.builder \
    .appName("API Data Collection") \
    .getOrCreate()

# 한국 시간대 설정 
KST = timezone(timedelta(hours=9))

# Delta 테이블 이름 
catalog_table_1 = "bronze.api_seoulcity.`서울시_실시간_인구현황`"
catalog_table_2 = "bronze.api_seoulcity.`서울시_실시간_인구_예측정보`"

# 스키마 정의 
live_schema = StructType([
    StructField("AREA_NM", StringType(), True),
    StructField("AREA_CD", StringType(), True),
    StructField("AREA_CONGEST_LVL", StringType(), True),
    StructField("AREA_CONGEST_MSG", StringType(), True),
    StructField("AREA_PPLTN_MIN", StringType(), True),
    StructField("AREA_PPLTN_MAX", StringType(), True),
    StructField("MALE_PPLTN_RATE", StringType(), True),
    StructField("FEMALE_PPLTN_RATE", StringType(), True),
    StructField("PPLTN_RATE_0", StringType(), True),
    StructField("PPLTN_RATE_10", StringType(), True),
    StructField("PPLTN_RATE_20", StringType(), True),
    StructField("PPLTN_RATE_30", StringType(), True),
    StructField("PPLTN_RATE_40", StringType(), True),
    StructField("PPLTN_RATE_50", StringType(), True), 
    StructField("PPLTN_RATE_60", StringType(), True), 
    StructField("PPLTN_RATE_70", StringType(), True), 
    StructField("RESNT_PPLTN_RATE", StringType(), True), 
    StructField("NON_RESNT_PPLTN_RATE", StringType(), True), 
    StructField("REPLACE_YN", StringType(), True), 
    StructField("PPLTN_TIME", StringType(), True), 
    StructField("FCST_YN", StringType(), True), 
    StructField("collected_time", StringType(), True), # 수집 시간 필드 
    StructField("id", IntegerType(), True)             # ID 필드 
])

fcst_schema = StructType([
    StructField("AREA_NM", StringType(), True),
    StructField("AREA_CD", StringType(), True),
    StructField("FCST_TIME", StringType(), True),
    StructField("FCST_CONGEST_LVL", StringType(), True),
    StructField("FCST_PPLTN_MIN", StringType(), True),
    StructField("FCST_PPLTN_MAX", StringType(), True),
    StructField("PPLTN_TIME", StringType(), True), 
    StructField("collected_time", StringType(), True),  # 수집 시간 필드 
    StructField("id", IntegerType(), True)              # ID 필드 
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
                "AREA_NM", "AREA_CD", "AREA_CONGEST_LVL", "AREA_CONGEST_MSG",
                "AREA_PPLTN_MIN", "AREA_PPLTN_MAX", "MALE_PPLTN_RATE", "FEMALE_PPLTN_RATE",
                "PPLTN_RATE_0", "PPLTN_RATE_10", "PPLTN_RATE_20", "PPLTN_RATE_30",
                "PPLTN_RATE_40", "PPLTN_RATE_50", "PPLTN_RATE_60", "PPLTN_RATE_70",
                "RESNT_PPLTN_RATE", "NON_RESNT_PPLTN_RATE", "REPLACE_YN", "PPLTN_TIME", "FCST_YN", "collected_time"
            ] 
        elif table_name == catalog_table_2:
            dedup_columns = [
                "AREA_NM", "AREA_CD", "FCST_TIME", "FCST_CONGEST_LVL",
                "FCST_PPLTN_MIN", "FCST_PPLTN_MAX", "PPLTN_TIME", "collected_time"
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

# 인구현황 데이터 수집 함수 
def collect_seoul_population_data(api_keys, area_codes_population):

    # 수집 데이터 리스트
    all_live_population_rows = []
    all_fcst_population_rows = []

    # id 초기화 & api 요청 횟수 카운트  
    live_id = 0
    fcst_id = 0
    request_count = 0

    for area_code in area_codes_population:
        if request_count >= len(api_keys) * 1000:
            print("모든 API 키의 일일 호출 한도를 초과했습니다.")
            break

        api_key = api_keys[min(request_count // 1000, len(api_keys) - 1)]
        url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/citydata_ppltn/1/5/{area_code}"

        try:
            response = requests.get(url, timeout=10)
            request_count += 1
            response.raise_for_status()
            data = response.json()

            # 유효성 검사
            result_code = data.get("RESULT", {}).get("RESULT.CODE", "") 
            if result_code != "INFO-000":
                print(f"[{area_code}] 응답 코드 오류")
                continue

            ppltn_list = data.get("SeoulRtd.citydata_ppltn", [])
            if not ppltn_list:
                print(f"[{area_code}] 인구 데이터 없음.")
                continue

            # 수집 시간 추가
            collected_time = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
            data["collected_time"] = collected_time

            # 평탄화 함수 적용 및 ID 값 부여
            live_population_row = flatten_live_ppltn(data, collected_time)
            live_id += 1
            live_population_row["id"] = live_id

            fcst_population_rows = flatten_fcst_ppltn(data, collected_time)
            for row in fcst_population_rows:
                fcst_id += 1
                row["id"] = fcst_id

            all_live_population_rows.append(live_population_row)
            all_fcst_population_rows.extend(fcst_population_rows)

            print(f"[{area_code}] 수집 완료")
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"[{area_code}] 요청 실패: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"[{area_code}] 오류 발생: {e}")
            time.sleep(2)

    return all_live_population_rows, all_fcst_population_rows

# API 키 리스트 (최대 1000건//키)
api_keys = [
    "API_KEY_1",
    "API_KEY_2",
    "API_KEY_3"
] 

# 데이터 수집 
all_live_population_rows, all_fcst_population_rows = collect_seoul_population_data(api_keys, area_codes_population) 

# dalta table 초기화 
initialize_delta_table(catalog_table_1, live_schema)
initialize_delta_table(catalog_table_2, fcst_schema)

if all_live_population_rows:
    live_df = spark.createDataFrame(all_live_population_rows, schema=live_schema)
    save_to_delta(live_df, catalog_table_1)
    print("[INFO] Delta 테이블에 최종 데이터 저장 완료.") 
else: 
    print("수집된 데이터가 없습니다.")

if all_fcst_population_rows:
    fcst_df = spark.createDataFrame(all_fcst_population_rows, schema=fcst_schema)  
    save_to_delta(fcst_df, catalog_table_2) 
    print("[INFO] Delta 테이블에 최종 데이터 저장 완료.") 
else: 
    print("수집된 데이터가 없습니다.") 

# 중복 제거 후 업데이트
remove_duplicates(catalog_table_1)
remove_duplicates(catalog_table_2) 
