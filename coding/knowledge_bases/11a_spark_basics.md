# 11a: Spark Basics

> **Concept ID**: `11a_spark_basics`
> **Target**: Complete beginner to Palantir Dev/Delta interview level
> **Prerequisites**: SQL fundamentals, Python basics
> **Special Note**: Palantir Foundry의 핵심 기술 - 면접에서 가장 중요한 KB

---

## 1. Universal Concept (Spark의 본질)

### 왜 Spark인가?

**문제**: 데이터가 너무 커서 한 컴퓨터에서 처리할 수 없다.

```
Traditional Processing:
[Single Machine] → 1TB 데이터 → 메모리 부족 → 실패

Distributed Processing (Spark):
[Machine 1] → 250GB ─┐
[Machine 2] → 250GB ─┼→ 결과 합침 → 성공
[Machine 3] → 250GB ─┤
[Machine 4] → 250GB ─┘
```

### Mental Model: "분산 컬렉션"

```python
# 로컬 Python - 한 컴퓨터의 메모리
numbers = [1, 2, 3, 4, 5]
result = [x * 2 for x in numbers]

# Spark - 여러 컴퓨터에 분산된 데이터
# 코드는 비슷하지만, 데이터는 클러스터 전체에 분산
numbers_rdd = spark.parallelize([1, 2, 3, 4, 5])
result_rdd = numbers_rdd.map(lambda x: x * 2)
```

### MapReduce vs Spark

| 특성 | MapReduce | Spark |
|------|-----------|-------|
| 중간 결과 저장 | 디스크 | 메모리 |
| 반복 처리 | 매번 디스크 I/O | 메모리에서 재사용 |
| 속도 | 느림 | 10-100x 빠름 |
| API | Low-level | High-level (SQL, DataFrame) |
| 실시간 처리 | 어려움 | Spark Streaming 지원 |

### In-Memory 처리의 장점

```
MapReduce 방식:
Step 1 → 디스크 저장 → Step 2 → 디스크 저장 → Step 3
         (느림)              (느림)

Spark 방식:
Step 1 → 메모리 유지 → Step 2 → 메모리 유지 → Step 3
         (빠름)               (빠름)
```

---

## 2. Core Concepts (핵심 개념)

### 2.1 RDD (Resilient Distributed Dataset)

**RDD = 분산 불변 컬렉션**

```python
# RDD의 3가지 핵심 속성
# 1. Resilient (복원력) - 장애 시 자동 복구
# 2. Distributed (분산) - 클러스터 전체에 분산
# 3. Dataset (데이터셋) - 데이터 컬렉션

# RDD 생성 방법 1: parallelize
rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5])

# RDD 생성 방법 2: 파일에서 읽기
rdd = spark.sparkContext.textFile("hdfs://data/logs.txt")
```

**불변성 (Immutability)**
```python
# RDD는 변경 불가능 - 새 RDD 생성
original_rdd = spark.sparkContext.parallelize([1, 2, 3])
new_rdd = original_rdd.map(lambda x: x * 2)  # 새 RDD 생성

# original_rdd는 그대로 [1, 2, 3]
# new_rdd는 [2, 4, 6]
```

**Lineage (혈통) - 장애 복구의 핵심**
```python
# Spark는 RDD 변환 과정을 기억 (Lineage)
rdd1 = spark.sparkContext.parallelize([1, 2, 3, 4, 5])  # 원본
rdd2 = rdd1.map(lambda x: x * 2)                        # 변환 1
rdd3 = rdd2.filter(lambda x: x > 4)                     # 변환 2

# 만약 rdd3의 일부 파티션이 손실되면?
# → Lineage를 따라 rdd1부터 재계산하여 복구
```

### 2.2 DataFrame & Dataset

**DataFrame = 스키마가 있는 분산 테이블**

```python
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

# SparkSession 생성 (Spark 2.0+)
spark = SparkSession.builder \
    .appName("DataFrame Demo") \
    .getOrCreate()

# DataFrame 생성 - SQL 테이블처럼 컬럼과 타입이 있음
data = [("Alice", 30), ("Bob", 25), ("Charlie", 35)]
df = spark.createDataFrame(data, ["name", "age"])

df.printSchema()
# root
#  |-- name: string (nullable = true)
#  |-- age: long (nullable = true)
```

**RDD vs DataFrame 비교**

| 특성 | RDD | DataFrame |
|------|-----|-----------|
| 스키마 | 없음 | 있음 (컬럼 이름, 타입) |
| 최적화 | 수동 | Catalyst 자동 최적화 |
| 언어 지원 | Scala, Java, Python | 모든 언어 동일 성능 |
| 사용 용도 | Low-level 제어 | 대부분의 데이터 처리 |
| 성능 | Python에서 느림 | Python에서도 빠름 |

```python
# RDD 방식 - Python UDF로 인해 느림
rdd.map(lambda row: row.age * 2)

# DataFrame 방식 - Catalyst 최적화, 빠름
df.select(df.age * 2)
```

### 2.3 Transformations vs Actions

**이것이 Spark의 핵심 개념!**

```
Transformations (변환)          Actions (실행)
- 새 RDD/DataFrame 생성          - 실제 계산 수행
- Lazy (지연 실행)               - Eager (즉시 실행)
- DAG에 추가만 함                - DAG 실행 트리거
```

**Transformations (Lazy - 실행 지연)**

```python
# 아래 코드들은 실행되지 않음 - DAG에 기록만!
df_filtered = df.filter(df.age > 25)       # 실행 안 됨
df_selected = df_filtered.select("name")   # 실행 안 됨
df_grouped = df.groupBy("dept")            # 실행 안 됨

# 주요 Transformations
df.select("col1", "col2")      # 컬럼 선택
df.filter(df.age > 20)         # 필터링
df.where("age > 20")           # 필터링 (SQL 스타일)
df.groupBy("dept")             # 그룹화
df.join(df2, "key")            # 조인
df.union(df2)                  # 합집합
df.distinct()                  # 중복 제거
df.orderBy("age")              # 정렬
df.withColumn("new", ...)      # 컬럼 추가
```

**Actions (Eager - 즉시 실행)**

```python
# Action을 호출하면 그때서야 전체 DAG 실행!
df.show()                      # 결과 출력 → 실행!
df.count()                     # 행 수 → 실행!
df.collect()                   # 모든 데이터를 드라이버로 → 실행!
df.first()                     # 첫 번째 행 → 실행!
df.take(5)                     # 상위 5개 행 → 실행!
df.write.parquet("output")     # 파일 저장 → 실행!
```

**실행 흐름 예시**

```python
# Step 1-3: 아무것도 실행되지 않음 (Lazy)
df1 = spark.read.parquet("input")      # Transformation
df2 = df1.filter(df1.active == True)   # Transformation
df3 = df2.groupBy("category").count()  # Transformation

# Step 4: Action 호출 → 전체 DAG 실행
df3.show()  # ← 이 순간 모든 계산이 실행됨
```

### 2.4 Lazy Evaluation

**DAG (Directed Acyclic Graph)**

```
                    ┌─────────────┐
                    │  read.csv   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   filter    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐     │     ┌──────▼──────┐
       │  select A   │     │     │  select B   │
       └──────┬──────┘     │     └──────┬──────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │    join     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   show()    │ ← Action: DAG 실행
                    └─────────────┘
```

**왜 Lazy가 좋은가?**

```python
# 예시: 비효율적인 쿼리
df.filter(df.country == "US") \
  .filter(df.age > 20) \
  .filter(df.age < 30) \
  .show()

# Catalyst 최적화 후 (Lazy이기 때문에 가능):
# filter가 하나로 합쳐짐
# → filter((country == "US") AND (age > 20) AND (age < 30))
```

### 2.5 Partitioning & Shuffling

**Partition = 데이터의 물리적 분할**

```
데이터: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

파티션 3개로 분할:
[Partition 1]: [1, 2, 3, 4]    → Worker 1에서 처리
[Partition 2]: [5, 6, 7]       → Worker 2에서 처리
[Partition 3]: [8, 9, 10]      → Worker 3에서 처리
```

**Shuffle = 데이터 재분배 (비용이 큼!)**

```python
# Shuffle이 발생하는 연산들
df.groupBy("category")     # 같은 category를 한 파티션으로 모음
df.join(df2, "key")        # 같은 key를 한 파티션으로 모음
df.repartition(10)         # 파티션 재분배
df.orderBy("amount")       # 전체 정렬
```

```
Shuffle 전:
[P1: A,B,A,C] [P2: B,C,A,B] [P3: C,A,C,B]

groupBy("category") → Shuffle 발생!

Shuffle 후:
[P1: A,A,A,A] [P2: B,B,B,B] [P3: C,C,C,C]
     └──────네트워크 전송──────┘
```

**파티션 수 조절**

```python
# 현재 파티션 수 확인
df.rdd.getNumPartitions()

# repartition: 파티션 늘리기/줄이기 (Shuffle 발생)
df.repartition(100)

# coalesce: 파티션 줄이기만 (Shuffle 최소화)
df.coalesce(10)  # 100 → 10으로 줄일 때 사용

# 권장: 줄일 때는 coalesce, 늘릴 때는 repartition
```

---

## 3. PySpark Quick Reference

### SparkSession 생성

```python
from pyspark.sql import SparkSession

# 기본 생성
spark = SparkSession.builder \
    .appName("My App") \
    .getOrCreate()

# 설정과 함께 생성
spark = SparkSession.builder \
    .appName("My App") \
    .config("spark.executor.memory", "4g") \
    .config("spark.executor.cores", "2") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()
```

### DataFrame 생성

```python
# 방법 1: 리스트에서 생성
data = [
    (1, "Alice", 30),
    (2, "Bob", 25),
    (3, "Charlie", 35)
]
df = spark.createDataFrame(data, ["id", "name", "age"])

# 방법 2: 딕셔너리 리스트에서 생성
data = [
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 25}
]
df = spark.createDataFrame(data)

# 방법 3: 스키마 명시
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

schema = StructType([
    StructField("id", IntegerType(), False),
    StructField("name", StringType(), True),
    StructField("age", IntegerType(), True)
])
df = spark.createDataFrame(data, schema)
```

### 파일 읽기/쓰기

```python
# CSV 읽기
df = spark.read.csv("data.csv", header=True, inferSchema=True)
df = spark.read.option("header", True).csv("data.csv")

# Parquet 읽기 (가장 효율적)
df = spark.read.parquet("data.parquet")

# JSON 읽기
df = spark.read.json("data.json")

# 파일 쓰기
df.write.parquet("output.parquet")
df.write.csv("output.csv", header=True)
df.write.mode("overwrite").parquet("output")  # 덮어쓰기
df.write.mode("append").parquet("output")     # 추가
```

### 기본 연산

```python
# 스키마 확인
df.printSchema()
df.dtypes  # 리스트로 반환

# 데이터 미리보기
df.show()
df.show(10, truncate=False)  # 10행, 잘림 없이

# 통계
df.describe().show()
df.count()  # 행 수

# 컬럼 선택
df.select("name", "age")
df.select(df.name, df.age)
df.select(df["name"], df["age"])

# 컬럼 추가/수정
from pyspark.sql.functions import col, lit

df.withColumn("age_plus_10", col("age") + 10)
df.withColumn("country", lit("Korea"))

# 컬럼 이름 변경
df.withColumnRenamed("name", "full_name")

# 컬럼 삭제
df.drop("age")
```

### 필터링

```python
# 기본 필터
df.filter(df.age > 25)
df.filter("age > 25")  # SQL 스타일
df.where(df.age > 25)  # filter와 동일

# 복합 조건
df.filter((df.age > 20) & (df.age < 30))    # AND
df.filter((df.age < 20) | (df.age > 30))    # OR
df.filter(~(df.age > 25))                    # NOT

# 문자열 조건
df.filter(df.name.like("A%"))               # A로 시작
df.filter(df.name.contains("li"))           # 포함
df.filter(df.name.startswith("A"))
df.filter(df.name.endswith("e"))

# NULL 처리
df.filter(df.age.isNull())
df.filter(df.age.isNotNull())
df.na.drop()  # NULL 행 제거
df.na.fill(0)  # NULL을 0으로 채움
```

### 그룹화 & 집계

```python
from pyspark.sql.functions import count, sum, avg, min, max

# 기본 그룹화
df.groupBy("department").count()
df.groupBy("department").agg({"salary": "avg"})

# 여러 집계
df.groupBy("department").agg(
    count("*").alias("count"),
    avg("salary").alias("avg_salary"),
    max("salary").alias("max_salary")
)

# 윈도우 함수
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank, dense_rank

window = Window.partitionBy("department").orderBy(col("salary").desc())

df.withColumn("rank", rank().over(window))
df.withColumn("row_num", row_number().over(window))
```

### 조인

```python
# Inner Join (기본)
df1.join(df2, df1.id == df2.user_id)
df1.join(df2, df1.id == df2.user_id, "inner")

# Left/Right Join
df1.join(df2, df1.id == df2.user_id, "left")
df1.join(df2, df1.id == df2.user_id, "right")

# Full Outer Join
df1.join(df2, df1.id == df2.user_id, "outer")

# Left Anti Join (df1에만 있는 것)
df1.join(df2, df1.id == df2.user_id, "left_anti")

# Left Semi Join (df2에 매칭되는 df1만)
df1.join(df2, df1.id == df2.user_id, "left_semi")

# 컬럼명이 같을 때
df1.join(df2, "id")  # 자동으로 id 컬럼 매칭
df1.join(df2, ["id", "date"])  # 여러 컬럼
```

### SQL 사용

```python
# 임시 뷰 생성
df.createOrReplaceTempView("users")

# SQL 쿼리 실행
result = spark.sql("""
    SELECT department, AVG(salary) as avg_salary
    FROM users
    WHERE age > 25
    GROUP BY department
    HAVING AVG(salary) > 50000
    ORDER BY avg_salary DESC
""")

result.show()
```

---

## 4. Palantir Foundry Context

### Foundry = Spark 기반 플랫폼

```
┌─────────────────────────────────────────┐
│           Palantir Foundry              │
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Contour │  │ Quiver  │  │Workshop │  │  ← 사용자 인터페이스
│  └────┬────┘  └────┬────┘  └────┬────┘  │
│       │            │            │       │
│  ┌────▼────────────▼────────────▼────┐  │
│  │         Transform (PySpark)       │  │  ← 데이터 변환 레이어
│  └────────────────┬─────────────────┘  │
│                   │                     │
│  ┌────────────────▼─────────────────┐  │
│  │         Apache Spark             │  │  ← 분산 처리 엔진
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Transform 기본 구조

```python
from transforms.api import transform_df, Input, Output

@transform_df(
    Output("/Company/Project/output_dataset"),
    source=Input("/Company/Project/input_dataset")
)
def compute(source):
    """
    Transform 함수
    - source: Input DataFrame
    - return: Output DataFrame
    """
    return source.filter(source.active == True)
```

### 다중 Input Transform

```python
from transforms.api import transform_df, Input, Output

@transform_df(
    Output("/path/to/output"),
    users=Input("/path/to/users"),
    orders=Input("/path/to/orders")
)
def compute(users, orders):
    """여러 데이터셋을 조인하여 처리"""
    return users.join(orders, users.user_id == orders.user_id)
```

### 증분 처리 (Incremental)

```python
from transforms.api import transform, Input, Output, incremental

@incremental()
@transform(
    Output("/path/to/output"),
    source=Input("/path/to/input")
)
def compute(source, output):
    """
    증분 처리: 새로운 데이터만 처리
    - 전체 재처리 대신 변경분만 처리
    - 대용량 데이터에서 성능 향상
    """
    # 새로운 데이터 읽기
    new_data = source.dataframe('added')

    # 기존 출력에 추가
    output.write_dataframe(new_data, mode='append')
```

### Foundry 특화 개념

**1. 데이터 계보 (Data Lineage)**
```
[Raw Data] → [Transform 1] → [Transform 2] → [Final Dataset]
     │             │               │               │
     └─────────────┴───────────────┴───────────────┘
                  자동으로 추적됨 (Provenance)
```

**2. 브랜치 (Branching)**
```python
# Git처럼 데이터도 브랜치 가능
# main 브랜치: 프로덕션 데이터
# feature 브랜치: 실험/개발용

# 브랜치에서 Transform 테스트 후 main에 머지
```

**3. 스키마 관리**
```python
# Foundry는 스키마 변경을 추적
# 스키마 변경 시 하위 Transform에 영향 분석 가능
```

### 면접에서 자주 나오는 Foundry 질문

| 질문 | 핵심 답변 |
|------|-----------|
| Transform이란? | PySpark 기반 데이터 변환 파이프라인 |
| 증분 처리 장점? | 전체 재처리 대신 변경분만 처리하여 성능 향상 |
| Lineage 중요성? | 데이터 출처 추적, 영향도 분석, 디버깅 |
| 브랜치 사용 이유? | 프로덕션 영향 없이 실험/테스트 가능 |

---

## 5. Common Pitfalls (흔한 실수)

### 5.1 collect() 남용

```python
# WRONG: 모든 데이터를 드라이버로 가져옴 → 메모리 부족
all_data = df.collect()
for row in all_data:
    print(row)

# RIGHT: 일부만 가져오기
sample = df.take(10)
# 또는
df.limit(10).show()
```

### 5.2 불필요한 Shuffle

```python
# WRONG: 작은 테이블도 shuffle join
small_df = spark.createDataFrame([(1, "A"), (2, "B")], ["id", "name"])
big_df.join(small_df, "id")  # Shuffle 발생

# RIGHT: Broadcast Join (작은 테이블을 모든 노드에 복제)
from pyspark.sql.functions import broadcast
big_df.join(broadcast(small_df), "id")  # Shuffle 없음
```

### 5.3 캐싱 미사용

```python
# WRONG: 같은 DataFrame을 여러 번 계산
filtered = df.filter(df.age > 25)
count1 = filtered.count()      # 계산 1
count2 = filtered.filter(df.gender == "M").count()  # 처음부터 다시 계산

# RIGHT: 캐싱으로 재사용
filtered = df.filter(df.age > 25).cache()  # 메모리에 저장
count1 = filtered.count()      # 계산 후 캐시
count2 = filtered.filter(df.gender == "M").count()  # 캐시에서 읽음

# 사용 후 해제
filtered.unpersist()
```

### 5.4 파티션 수 문제

```python
# WRONG: 파티션이 너무 적음 (병렬성 낮음)
df.coalesce(1).write.parquet("output")  # 1개 파티션 → 1개 태스크

# WRONG: 파티션이 너무 많음 (오버헤드)
df.repartition(10000)  # 작은 파일 10000개 생성

# RIGHT: 적절한 파티션 수 (일반적으로 코어 수의 2-4배)
df.repartition(200)  # 또는 기본값 사용
```

### 5.5 Python UDF 과다 사용

```python
# WRONG: Python UDF (직렬화/역직렬화 오버헤드)
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

@udf(StringType())
def upper_name(name):
    return name.upper()

df.withColumn("upper", upper_name(df.name))

# RIGHT: Spark 내장 함수 사용
from pyspark.sql.functions import upper
df.withColumn("upper", upper(df.name))  # 10-100x 빠름
```

### 5.6 스키마 추론 비용

```python
# WRONG: 매번 스키마 추론 (대용량에서 느림)
df = spark.read.json("huge_data.json")  # 전체 파일 스캔

# RIGHT: 스키마 명시
schema = StructType([...])
df = spark.read.schema(schema).json("huge_data.json")
```

### Pitfall 요약 표

| Pitfall | 증상 | 해결책 |
|---------|------|--------|
| collect() 남용 | OOM Error | take(n), limit() 사용 |
| 불필요한 Shuffle | 느린 조인 | broadcast() 사용 |
| 캐싱 미사용 | 반복 계산 | cache(), persist() |
| 파티션 수 부적절 | 병렬성 문제 | repartition() 조정 |
| Python UDF | 느린 처리 | Spark 내장 함수 선호 |
| 스키마 미지정 | 느린 읽기 | schema 명시 |

---

## 6. Interview Focus (면접 포인트)

### 개념 질문

**Q1: "Transformation과 Action의 차이는?"**
```
Transformation:
- 새 RDD/DataFrame 생성
- Lazy 실행 (즉시 실행 안 함)
- 예: filter, select, groupBy, join

Action:
- 실제 계산 수행
- Eager 실행 (즉시 실행)
- 예: show, count, collect, write
```

**Q2: "Lazy Evaluation의 장점은?"**
```
1. 최적화 기회: 전체 DAG를 보고 최적화 가능
   - 필터 조건 합치기
   - 불필요한 컬럼 제거
   - 조인 순서 최적화

2. 파이프라인 효율성: 중간 결과 저장 불필요
   - 메모리 절약
   - I/O 감소
```

**Q3: "Shuffle이 발생하는 상황은?"**
```
1. groupBy(): 같은 키를 한 파티션으로 모음
2. join(): 같은 키를 한 파티션으로 모음
3. repartition(): 파티션 재분배
4. orderBy(): 전체 정렬
5. distinct(): 중복 제거

해결책:
- Broadcast Join (작은 테이블)
- 파티셔닝 전략 최적화
- coalesce() 사용 (줄일 때)
```

**Q4: "RDD vs DataFrame의 차이는?"**
```
RDD:
- Low-level API
- 스키마 없음
- Python에서 느림 (직렬화)
- 세밀한 제어 가능

DataFrame:
- High-level API
- 스키마 있음 (컬럼, 타입)
- Catalyst 최적화
- Python에서도 빠름
- SQL 지원

결론: 대부분 DataFrame 사용 권장
```

**Q5: "Spark에서 메모리 부족 시 대처법은?"**
```
1. collect() 대신 take(n) 사용
2. 파티션 수 조절 (repartition)
3. 캐시 전략 검토 (persist 레벨)
4. Broadcast Join 활용
5. Executor 메모리 증가 (spark.executor.memory)
6. 데이터 직렬화 최적화 (Kryo)
```

### 코딩 문제 유형

**유형 1: 데이터 변환**
```python
# 문제: 부서별 평균 급여가 50000 이상인 부서 찾기
df.groupBy("department") \
  .agg(avg("salary").alias("avg_salary")) \
  .filter(col("avg_salary") >= 50000)
```

**유형 2: 조인과 집계**
```python
# 문제: 주문이 없는 고객 찾기
customers.join(orders, "customer_id", "left_anti")
```

**유형 3: 윈도우 함수**
```python
# 문제: 부서별 급여 순위
from pyspark.sql.window import Window
from pyspark.sql.functions import rank

window = Window.partitionBy("department").orderBy(col("salary").desc())
df.withColumn("rank", rank().over(window))
```

### Palantir 특화 질문

**Q1: "Foundry에서 데이터 변환 경험이 있나요?"**
```
답변 포인트:
- @transform_df 데코레이터 사용 경험
- Input/Output 데이터셋 설정
- PySpark DataFrame 처리
- 데이터 품질 검증
```

**Q2: "증분 처리(Incremental)를 구현한 경험은?"**
```
답변 포인트:
- @incremental() 데코레이터
- 전체 재처리 vs 증분의 장단점
- 'added', 'modified', 'removed' 데이터 처리
- 성능 개선 수치 (가능하면)
```

**Q3: "대용량 데이터 조인 최적화 경험은?"**
```
답변 포인트:
- Broadcast Join 활용
- 조인 키 파티셔닝
- Shuffle 최소화 전략
- Skew 데이터 처리
```

### 화이트보드 연습 문제

```python
# 문제: 최근 30일간 일별 활성 사용자 수 계산
# Input: events (user_id, event_type, timestamp)

from pyspark.sql.functions import to_date, countDistinct, current_date, datediff

events \
  .filter(datediff(current_date(), to_date("timestamp")) <= 30) \
  .groupBy(to_date("timestamp").alias("date")) \
  .agg(countDistinct("user_id").alias("dau")) \
  .orderBy("date")
```

---

## 7. Cross-References

### Related KBs

| KB | 연관성 |
|----|--------|
| SQL fundamentals | SQL 문법 → Spark SQL에서 동일 |
| Python closures | Spark 직렬화 시 클로저 문제 |
| Iterables/Sequences | Lazy evaluation 개념 공유 |
| Arrays/Lists | 분산 컬렉션 vs 로컬 컬렉션 |

### Spark SQL vs 일반 SQL

```python
# 일반 SQL
SELECT department, AVG(salary)
FROM employees
WHERE age > 25
GROUP BY department

# Spark SQL (동일)
spark.sql("""
    SELECT department, AVG(salary)
    FROM employees
    WHERE age > 25
    GROUP BY department
""")

# DataFrame API (동일 결과)
employees \
  .filter(col("age") > 25) \
  .groupBy("department") \
  .agg(avg("salary"))
```

### 직렬화 주의사항 (Closure 관련)

```python
# WRONG: 클래스 메서드 참조 → 전체 객체 직렬화
class Processor:
    def __init__(self):
        self.large_data = [...]  # 큰 데이터

    def process(self, df):
        # self가 직렬화됨 → 모든 Worker에 large_data 전송
        return df.filter(lambda x: x in self.large_data)

# RIGHT: 필요한 데이터만 추출
class Processor:
    def __init__(self):
        self.large_data = [...]

    def process(self, df):
        filter_data = self.large_data  # 로컬 변수로 추출
        return df.filter(lambda x: x in filter_data)
```

### External Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Spark Official Docs | https://spark.apache.org/docs/latest/ | 공식 문서 |
| PySpark API | https://spark.apache.org/docs/latest/api/python/ | Python API |
| Databricks Guide | https://docs.databricks.com/spark/latest/spark-sql/ | 실용적 가이드 |
| Palantir Foundry | https://www.palantir.com/docs/foundry/ | Foundry 문서 |

---

## 8. Quick Cheat Sheet

### 자주 쓰는 Import

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when,
    count, sum, avg, min, max,
    collect_list, collect_set,
    row_number, rank, dense_rank,
    to_date, date_format, datediff,
    upper, lower, trim, split,
    explode, array, struct
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType,
    ArrayType, DateType, TimestampType
)
from pyspark.sql.window import Window
```

### 핵심 연산 한눈에

```python
# 읽기
df = spark.read.parquet("path")

# 변환
df.select("col1", "col2")
df.filter(col("age") > 25)
df.withColumn("new", col("old") * 2)
df.groupBy("key").agg(sum("value"))
df1.join(df2, "key")

# 쓰기
df.write.mode("overwrite").parquet("output")

# 확인
df.show()
df.printSchema()
df.count()
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation for Palantir interview prep |
