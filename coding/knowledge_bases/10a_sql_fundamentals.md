# 10a: SQL Fundamentals (SQL 기초)

> **Concept ID**: `10a_sql_fundamentals`
> **Universal Principle**: 관계형 데이터베이스에서 데이터를 정의, 조작, 조회하기 위한 선언적 언어
> **Target**: Complete beginner to Palantir Dev/Delta interview level
> **Prerequisites**: None (entry point KB)

---

## 1. Universal Concept (SQL의 본질)

**SQL (Structured Query Language)**은 관계형 데이터베이스 관리 시스템(RDBMS)에서 데이터를 관리하고 조회하기 위한 표준 언어입니다. 1970년대 IBM에서 개발되었으며, 현재 모든 주요 데이터베이스 시스템에서 지원됩니다.

### 1.1 Mental Model: 질문을 던지면 답을 얻는다

```
┌─────────────────────────────────────────────────────────────────────┐
│                SQL = "데이터에게 질문하는 언어"                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  사용자:  "서울에 사는 30세 이상 고객을 알려줘"                      │
│     │                                                               │
│     ▼                                                               │
│  SQL:     SELECT * FROM customers                                   │
│           WHERE city = '서울' AND age >= 30;                        │
│     │                                                               │
│     ▼                                                               │
│  결과:    | name   | age | city |                                   │
│           |--------|-----|------|                                   │
│           | 김철수 | 35  | 서울 |                                   │
│           | 이영희 | 42  | 서울 |                                   │
│                                                                     │
│  핵심: "어떻게(How)"가 아니라 "무엇(What)"을 원하는지 말한다         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Declarative vs Imperative: 선언적 vs 명령적

```
┌─────────────────────────────────────────────────────────────────────┐
│          DECLARATIVE (SQL)           │      IMPERATIVE (Python)     │
├──────────────────────────────────────┼──────────────────────────────┤
│                                      │                              │
│  "30세 이상 고객을 찾아줘"           │  "데이터를 순회하면서        │
│                                      │   나이가 30 이상인지 확인해  │
│  SELECT * FROM customers             │   맞으면 결과에 추가해"      │
│  WHERE age >= 30;                    │                              │
│                                      │  results = []                │
│  데이터베이스가 최적화               │  for c in customers:         │
│  (인덱스 사용, 병렬 처리 등)         │      if c.age >= 30:         │
│                                      │          results.append(c)   │
│                                      │                              │
│  장점: 간결, 최적화 자동             │  장점: 세밀한 제어 가능      │
│  단점: 복잡한 로직 어려움            │  단점: 최적화 직접 구현      │
│                                      │                              │
└──────────────────────────────────────┴──────────────────────────────┘
```

### 1.3 데이터베이스 구조: 테이블, 행, 열

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATABASE STRUCTURE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DATABASE (데이터베이스)                                             │
│  └── SCHEMA (스키마)                                                 │
│      └── TABLE (테이블) = 엑셀 시트와 유사                          │
│          ├── COLUMN (열) = 속성/필드                                │
│          └── ROW (행) = 레코드/튜플                                 │
│                                                                     │
│  예시: employees 테이블                                              │
│  ┌──────┬──────────┬──────────┬────────┬─────────────┐              │
│  │ id   │ name     │ dept     │ salary │ hire_date   │ ← COLUMNS   │
│  ├──────┼──────────┼──────────┼────────┼─────────────┤              │
│  │ 1    │ Alice    │ Sales    │ 50000  │ 2020-01-15  │ ← ROW 1     │
│  │ 2    │ Bob      │ IT       │ 65000  │ 2019-03-22  │ ← ROW 2     │
│  │ 3    │ Charlie  │ Sales    │ 55000  │ 2021-07-10  │ ← ROW 3     │
│  └──────┴──────────┴──────────┴────────┴─────────────┘              │
│                                                                     │
│  - PRIMARY KEY (id): 각 행을 고유하게 식별하는 키                   │
│  - FOREIGN KEY: 다른 테이블을 참조하는 키                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 SQL의 4가지 카테고리

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SQL LANGUAGE CATEGORIES                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. DDL (Data Definition Language) - 구조 정의                      │
│     └── CREATE, ALTER, DROP, TRUNCATE                               │
│         "테이블을 만들고, 수정하고, 삭제한다"                       │
│                                                                     │
│  2. DML (Data Manipulation Language) - 데이터 조작                  │
│     └── SELECT, INSERT, UPDATE, DELETE                              │
│         "데이터를 조회하고, 추가하고, 수정하고, 삭제한다"           │
│                                                                     │
│  3. DCL (Data Control Language) - 권한 제어                         │
│     └── GRANT, REVOKE                                               │
│         "누가 무엇을 할 수 있는지 권한을 부여/회수한다"             │
│                                                                     │
│  4. TCL (Transaction Control Language) - 트랜잭션 제어              │
│     └── COMMIT, ROLLBACK, SAVEPOINT                                 │
│         "작업을 확정하거나 취소한다"                                │
│                                                                     │
│  면접 중점: DML (특히 SELECT)이 가장 많이 물어봄                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Topics (핵심 주제)

### 2.1 DDL (Data Definition Language) - 테이블 구조 정의

#### CREATE TABLE: 테이블 생성

```sql
-- 기본 테이블 생성
CREATE TABLE employees (
    id          INT PRIMARY KEY,           -- 기본 키 (고유 식별자)
    name        VARCHAR(100) NOT NULL,     -- 필수 문자열 (최대 100자)
    email       VARCHAR(255) UNIQUE,       -- 고유한 값만 허용
    dept_id     INT,                       -- 외래 키가 될 필드
    salary      DECIMAL(10, 2) DEFAULT 0,  -- 기본값 설정
    hire_date   DATE,                      -- 날짜 타입
    is_active   BOOLEAN DEFAULT TRUE,      -- 불리언 타입

    -- 외래 키 제약조건 (다른 테이블 참조)
    CONSTRAINT fk_dept
        FOREIGN KEY (dept_id)
        REFERENCES departments(id)
        ON DELETE SET NULL               -- 참조 대상 삭제 시 NULL로 설정
        ON UPDATE CASCADE                -- 참조 대상 수정 시 같이 수정
);

-- 인덱스 생성 (검색 성능 향상)
CREATE INDEX idx_emp_dept ON employees(dept_id);
CREATE UNIQUE INDEX idx_emp_email ON employees(email);
```

#### 데이터 타입 (Common Data Types)

```sql
-- 숫자 타입
INT, INTEGER           -- 정수 (-2^31 ~ 2^31-1)
BIGINT                 -- 큰 정수 (-2^63 ~ 2^63-1)
DECIMAL(p, s)          -- 정밀 소수점 (p: 전체 자릿수, s: 소수점 이하)
FLOAT, DOUBLE          -- 부동 소수점 (근사값, 금융 계산에 부적합)

-- 문자열 타입
CHAR(n)                -- 고정 길이 문자열 (항상 n자 저장)
VARCHAR(n)             -- 가변 길이 문자열 (최대 n자)
TEXT                   -- 긴 텍스트 (크기 제한 없음)

-- 날짜/시간 타입
DATE                   -- 날짜만 (YYYY-MM-DD)
TIME                   -- 시간만 (HH:MM:SS)
TIMESTAMP              -- 날짜 + 시간 (YYYY-MM-DD HH:MM:SS)
INTERVAL               -- 시간 간격

-- 불리언
BOOLEAN                -- TRUE / FALSE / NULL

-- 특수 타입
JSON, JSONB            -- JSON 데이터 (PostgreSQL)
ARRAY                  -- 배열 (PostgreSQL)
UUID                   -- 고유 식별자
```

#### ALTER TABLE: 테이블 수정

```sql
-- 열 추가
ALTER TABLE employees ADD COLUMN phone VARCHAR(20);

-- 열 수정
ALTER TABLE employees ALTER COLUMN salary TYPE DECIMAL(12, 2);

-- 열 삭제
ALTER TABLE employees DROP COLUMN phone;

-- 제약조건 추가
ALTER TABLE employees ADD CONSTRAINT chk_salary CHECK (salary >= 0);

-- 제약조건 삭제
ALTER TABLE employees DROP CONSTRAINT chk_salary;

-- 테이블 이름 변경
ALTER TABLE employees RENAME TO staff;
```

#### DROP & TRUNCATE

```sql
-- 테이블 완전 삭제 (구조 + 데이터)
DROP TABLE employees;

-- 존재하는 경우에만 삭제 (에러 방지)
DROP TABLE IF EXISTS employees;

-- 참조하는 객체까지 같이 삭제
DROP TABLE employees CASCADE;

-- 데이터만 삭제, 구조는 유지 (ROLLBACK 불가, 매우 빠름)
TRUNCATE TABLE employees;
-- vs DELETE FROM employees; (ROLLBACK 가능, 느림)
```

---

### 2.2 DML (Data Manipulation Language) - 데이터 조작

#### SELECT: 데이터 조회 (가장 중요!)

```sql
-- 기본 SELECT 문법
SELECT column1, column2    -- 조회할 열
FROM table_name            -- 대상 테이블
WHERE condition            -- 조건 필터
GROUP BY column            -- 그룹화
HAVING group_condition     -- 그룹 조건
ORDER BY column [ASC|DESC] -- 정렬
LIMIT n OFFSET m;          -- 결과 제한

-- 실행 순서 (VERY IMPORTANT!)
-- FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

#### SELECT 예제들

```sql
-- 1. 기본 조회
SELECT * FROM employees;                    -- 모든 열
SELECT name, salary FROM employees;         -- 특정 열만
SELECT DISTINCT dept FROM employees;        -- 중복 제거

-- 2. 별칭 (Alias)
SELECT
    name AS employee_name,                  -- 열 별칭
    salary * 12 AS annual_salary            -- 계산식 별칭
FROM employees AS e;                        -- 테이블 별칭

-- 3. 조건 필터 (WHERE)
SELECT * FROM employees
WHERE salary > 50000
  AND dept = 'IT'
  AND hire_date >= '2020-01-01';

-- 4. 패턴 매칭 (LIKE)
SELECT * FROM employees
WHERE name LIKE 'A%';       -- A로 시작
WHERE name LIKE '%son';     -- son으로 끝남
WHERE name LIKE '%ar%';     -- ar 포함
WHERE name LIKE '_ob';      -- 3글자, 마지막 두 글자가 ob

-- 5. 범위 조건
SELECT * FROM employees
WHERE salary BETWEEN 50000 AND 80000;  -- 50000 ≤ salary ≤ 80000
WHERE dept IN ('IT', 'Sales', 'HR');   -- 목록 중 하나
WHERE salary IS NULL;                   -- NULL 체크 (= NULL 안됨!)
WHERE salary IS NOT NULL;

-- 6. 정렬 (ORDER BY)
SELECT * FROM employees
ORDER BY salary DESC;                   -- 내림차순
ORDER BY dept ASC, salary DESC;         -- 다중 정렬
ORDER BY 2;                             -- 두 번째 열로 정렬 (비권장)

-- 7. 결과 제한
SELECT * FROM employees
ORDER BY salary DESC
LIMIT 10;                               -- 상위 10개
LIMIT 10 OFFSET 20;                     -- 21~30번째
```

#### 집계 함수 (Aggregate Functions)

```sql
-- 기본 집계 함수
SELECT
    COUNT(*) AS total_count,            -- 전체 행 수
    COUNT(salary) AS salary_count,      -- NULL 제외 개수
    COUNT(DISTINCT dept) AS dept_count, -- 고유값 개수
    SUM(salary) AS total_salary,        -- 합계
    AVG(salary) AS avg_salary,          -- 평균
    MIN(salary) AS min_salary,          -- 최소값
    MAX(salary) AS max_salary           -- 최대값
FROM employees;

-- GROUP BY: 그룹별 집계
SELECT
    dept,
    COUNT(*) AS emp_count,
    AVG(salary) AS avg_salary,
    MAX(salary) AS max_salary
FROM employees
GROUP BY dept;

-- 결과:
-- | dept  | emp_count | avg_salary | max_salary |
-- |-------|-----------|------------|------------|
-- | IT    | 15        | 75000      | 120000     |
-- | Sales | 20        | 55000      | 85000      |
-- | HR    | 8         | 50000      | 70000      |

-- HAVING: 그룹 조건 (WHERE는 그룹화 전, HAVING은 그룹화 후)
SELECT dept, AVG(salary) AS avg_sal
FROM employees
WHERE hire_date >= '2020-01-01'    -- 개별 행 필터
GROUP BY dept
HAVING AVG(salary) > 60000         -- 그룹 필터
ORDER BY avg_sal DESC;
```

#### INSERT: 데이터 삽입

```sql
-- 단일 행 삽입
INSERT INTO employees (name, email, dept_id, salary)
VALUES ('Alice', 'alice@example.com', 1, 55000);

-- 다중 행 삽입
INSERT INTO employees (name, email, dept_id, salary)
VALUES
    ('Bob', 'bob@example.com', 2, 65000),
    ('Charlie', 'charlie@example.com', 1, 60000),
    ('Diana', 'diana@example.com', 3, 70000);

-- SELECT 결과 삽입
INSERT INTO employee_archive (name, salary, archived_date)
SELECT name, salary, CURRENT_DATE
FROM employees
WHERE is_active = FALSE;

-- 충돌 처리 (PostgreSQL: ON CONFLICT)
INSERT INTO employees (id, name, salary)
VALUES (1, 'Alice', 60000)
ON CONFLICT (id) DO UPDATE
SET salary = EXCLUDED.salary;  -- 이미 존재하면 업데이트
```

#### UPDATE: 데이터 수정

```sql
-- 조건부 업데이트
UPDATE employees
SET salary = 60000
WHERE id = 1;

-- 다중 열 업데이트
UPDATE employees
SET
    salary = salary * 1.1,      -- 10% 인상
    is_active = TRUE
WHERE dept = 'IT';

-- 다른 테이블 참조 업데이트 (PostgreSQL)
UPDATE employees e
SET salary = e.salary + d.bonus
FROM departments d
WHERE e.dept_id = d.id;

-- 주의: WHERE 없으면 전체 업데이트!
-- UPDATE employees SET salary = 0;  -- 모든 직원 급여가 0이 됨!
```

#### DELETE: 데이터 삭제

```sql
-- 조건부 삭제
DELETE FROM employees
WHERE id = 1;

-- 다중 조건 삭제
DELETE FROM employees
WHERE is_active = FALSE
  AND hire_date < '2015-01-01';

-- 전체 삭제 (주의!)
DELETE FROM employees;  -- 모든 데이터 삭제, 복구 가능
TRUNCATE TABLE employees;  -- 더 빠르지만 복구 불가

-- 서브쿼리를 사용한 삭제
DELETE FROM employees
WHERE dept_id IN (
    SELECT id FROM departments WHERE name = 'Closed'
);
```

---

### 2.3 Joins (테이블 결합)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JOIN TYPES VISUAL                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  employees (A)        departments (B)                               │
│  ┌────┬────────┐     ┌────┬──────────┐                             │
│  │ id │ dept_id│     │ id │ name     │                             │
│  ├────┼────────┤     ├────┼──────────┤                             │
│  │ 1  │ 10     │     │ 10 │ Sales    │                             │
│  │ 2  │ 20     │     │ 20 │ IT       │                             │
│  │ 3  │ 30     │     │ 40 │ HR       │                             │
│  │ 4  │ NULL   │     └────┴──────────┘                             │
│  └────┴────────┘                                                   │
│                                                                     │
│  INNER JOIN:      A ∩ B (양쪽 다 있는 것만)                        │
│  ┌─────────┐                                                       │
│  │  (A∩B)  │  → id 1 (dept 10), id 2 (dept 20)                    │
│  └─────────┘     id 3 제외 (dept 30 없음), id 4 제외 (NULL)        │
│                                                                     │
│  LEFT JOIN:       A + (A ∩ B) (왼쪽 전부 + 매칭)                   │
│  ┌────┬─────┐                                                      │
│  │ A  │(A∩B)│  → id 1, 2 (매칭), id 3, 4 (NULL로 채움)            │
│  └────┴─────┘                                                      │
│                                                                     │
│  RIGHT JOIN:      (A ∩ B) + B (매칭 + 오른쪽 전부)                 │
│  ┌─────┬────┐                                                      │
│  │(A∩B)│ B  │  → id 1, 2 (매칭), dept 40/HR (NULL로 채움)         │
│  └─────┴────┘                                                      │
│                                                                     │
│  FULL OUTER:      A ∪ B (모든 것)                                  │
│  ┌────┬─────┬────┐                                                 │
│  │ A  │(A∩B)│ B  │  → 모든 행, 매칭 안 되면 NULL                  │
│  └────┴─────┴────┘                                                 │
│                                                                     │
│  CROSS JOIN:      A × B (카테시안 곱, 모든 조합)                   │
│                   4 × 3 = 12 rows                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### JOIN 예제 코드

```sql
-- 샘플 테이블
-- employees: id, name, dept_id
-- departments: id, name, location

-- INNER JOIN: 양쪽 테이블에 매칭되는 행만
SELECT
    e.name AS employee,
    d.name AS department
FROM employees e
INNER JOIN departments d ON e.dept_id = d.id;
-- dept_id가 NULL이거나, departments에 없는 dept_id는 제외됨

-- LEFT (OUTER) JOIN: 왼쪽 테이블 전부 + 매칭
SELECT
    e.name AS employee,
    COALESCE(d.name, 'No Department') AS department
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id;
-- 모든 직원이 나옴, department 없으면 NULL

-- RIGHT (OUTER) JOIN: 오른쪽 테이블 전부 + 매칭
SELECT
    COALESCE(e.name, 'Vacant') AS employee,
    d.name AS department
FROM employees e
RIGHT JOIN departments d ON e.dept_id = d.id;
-- 모든 부서가 나옴, 직원 없는 부서도 포함

-- FULL OUTER JOIN: 양쪽 전부
SELECT
    e.name AS employee,
    d.name AS department
FROM employees e
FULL OUTER JOIN departments d ON e.dept_id = d.id;
-- 모든 직원과 모든 부서가 나옴

-- CROSS JOIN: 모든 조합 (카테시안 곱)
SELECT e.name, d.name
FROM employees e
CROSS JOIN departments d;
-- employees가 4행, departments가 3행이면 12행 결과

-- Self JOIN: 같은 테이블을 자기 자신과 조인
-- 예: 직원과 그 매니저 찾기
SELECT
    e.name AS employee,
    m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;

-- 다중 JOIN
SELECT
    e.name AS employee,
    d.name AS department,
    l.city AS location
FROM employees e
JOIN departments d ON e.dept_id = d.id
JOIN locations l ON d.location_id = l.id;
```

---

### 2.4 Subqueries (서브쿼리)

```sql
-- ==================================================
-- Scalar Subquery: 단일 값 반환
-- ==================================================

-- 평균 급여보다 높은 직원
SELECT name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- SELECT 절에서 스칼라 서브쿼리
SELECT
    name,
    salary,
    (SELECT AVG(salary) FROM employees) AS avg_salary,
    salary - (SELECT AVG(salary) FROM employees) AS diff_from_avg
FROM employees;

-- ==================================================
-- Inline View (Derived Table): FROM 절의 서브쿼리
-- ==================================================

-- 부서별 평균 급여 → 다시 필터링
SELECT dept, avg_salary
FROM (
    SELECT dept, AVG(salary) AS avg_salary
    FROM employees
    GROUP BY dept
) AS dept_averages
WHERE avg_salary > 60000;

-- ==================================================
-- EXISTS vs IN
-- ==================================================

-- IN: 값이 목록에 있는지 확인
SELECT * FROM employees
WHERE dept_id IN (SELECT id FROM departments WHERE location = 'Seoul');

-- EXISTS: 서브쿼리 결과가 존재하는지 확인 (더 효율적인 경우 많음)
SELECT * FROM employees e
WHERE EXISTS (
    SELECT 1 FROM departments d
    WHERE d.id = e.dept_id AND d.location = 'Seoul'
);

-- NOT IN 주의사항: NULL이 있으면 결과가 비어버림!
SELECT * FROM employees
WHERE dept_id NOT IN (SELECT id FROM departments);
-- departments에 NULL이 있으면 아무 결과도 안 나옴!

-- 해결: NOT EXISTS 사용
SELECT * FROM employees e
WHERE NOT EXISTS (
    SELECT 1 FROM departments d WHERE d.id = e.dept_id
);

-- ==================================================
-- Correlated Subquery: 외부 쿼리 참조
-- ==================================================

-- 각 부서에서 가장 높은 급여를 받는 직원
SELECT * FROM employees e1
WHERE salary = (
    SELECT MAX(salary)
    FROM employees e2
    WHERE e2.dept_id = e1.dept_id  -- 외부 쿼리 참조
);

-- 평균보다 급여가 높은 직원 (부서별 평균 기준)
SELECT * FROM employees e1
WHERE salary > (
    SELECT AVG(salary)
    FROM employees e2
    WHERE e2.dept_id = e1.dept_id
);

-- ==================================================
-- ANY / ALL
-- ==================================================

-- ANY: 하나라도 만족하면 TRUE
SELECT * FROM employees
WHERE salary > ANY (SELECT salary FROM employees WHERE dept = 'IT');
-- IT 부서 중 최소 급여보다 높으면 됨

-- ALL: 모두 만족해야 TRUE
SELECT * FROM employees
WHERE salary > ALL (SELECT salary FROM employees WHERE dept = 'IT');
-- IT 부서 중 최고 급여보다 높아야 함
```

---

### 2.5 Advanced Topics (고급 주제)

#### Window Functions (윈도우 함수)

```sql
-- ==================================================
-- Window Function 기본 문법
-- function() OVER (PARTITION BY ... ORDER BY ... FRAME)
-- ==================================================

-- ROW_NUMBER: 순번 부여
SELECT
    name, dept, salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) AS salary_rank
FROM employees;

-- 결과:
-- | name    | dept  | salary | salary_rank |
-- |---------|-------|--------|-------------|
-- | Alice   | IT    | 120000 | 1           |
-- | Bob     | Sales | 85000  | 2           |
-- | Charlie | IT    | 75000  | 3           |

-- PARTITION BY: 그룹별로 순번
SELECT
    name, dept, salary,
    ROW_NUMBER() OVER (
        PARTITION BY dept
        ORDER BY salary DESC
    ) AS rank_in_dept
FROM employees;

-- 결과:
-- | name    | dept  | salary | rank_in_dept |
-- |---------|-------|--------|--------------|
-- | Alice   | IT    | 120000 | 1            |
-- | Charlie | IT    | 75000  | 2            |
-- | Bob     | Sales | 85000  | 1            |
-- | Diana   | Sales | 55000  | 2            |

-- ==================================================
-- RANK vs DENSE_RANK vs ROW_NUMBER
-- ==================================================

-- 급여: 100, 100, 90, 80
-- ROW_NUMBER: 1, 2, 3, 4 (항상 연속)
-- RANK:       1, 1, 3, 4 (같은 값 동순위, 다음 순위 건너뜀)
-- DENSE_RANK: 1, 1, 2, 3 (같은 값 동순위, 다음 순위 연속)

SELECT
    name, salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num,
    RANK() OVER (ORDER BY salary DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank
FROM employees;

-- ==================================================
-- LAG / LEAD: 이전/다음 행 참조
-- ==================================================

-- LAG: 이전 행의 값
-- LEAD: 다음 행의 값

SELECT
    order_date,
    amount,
    LAG(amount, 1, 0) OVER (ORDER BY order_date) AS prev_amount,
    LEAD(amount, 1, 0) OVER (ORDER BY order_date) AS next_amount,
    amount - LAG(amount, 1, 0) OVER (ORDER BY order_date) AS diff_from_prev
FROM orders;

-- 결과:
-- | order_date | amount | prev_amount | next_amount | diff_from_prev |
-- |------------|--------|-------------|-------------|----------------|
-- | 2024-01-01 | 100    | 0           | 150         | 100            |
-- | 2024-01-02 | 150    | 100         | 200         | 50             |
-- | 2024-01-03 | 200    | 150         | 0           | 50             |

-- ==================================================
-- 누적 합계, 이동 평균
-- ==================================================

SELECT
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total,
    AVG(amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3days
FROM orders;

-- ==================================================
-- FIRST_VALUE / LAST_VALUE / NTH_VALUE
-- ==================================================

SELECT
    name, dept, salary,
    FIRST_VALUE(name) OVER (
        PARTITION BY dept
        ORDER BY salary DESC
    ) AS highest_paid_in_dept,
    LAST_VALUE(name) OVER (
        PARTITION BY dept
        ORDER BY salary DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS lowest_paid_in_dept
FROM employees;
```

#### CTE (Common Table Expressions)

```sql
-- ==================================================
-- 기본 CTE (WITH 절)
-- ==================================================

-- 복잡한 쿼리를 단계별로 나누어 가독성 향상
WITH high_earners AS (
    SELECT * FROM employees WHERE salary > 80000
),
dept_counts AS (
    SELECT dept_id, COUNT(*) AS count
    FROM high_earners
    GROUP BY dept_id
)
SELECT d.name, dc.count
FROM departments d
JOIN dept_counts dc ON d.id = dc.dept_id;

-- ==================================================
-- 다중 CTE
-- ==================================================

WITH
    sales_2024 AS (
        SELECT * FROM orders WHERE order_date >= '2024-01-01'
    ),
    monthly_totals AS (
        SELECT
            DATE_TRUNC('month', order_date) AS month,
            SUM(amount) AS total
        FROM sales_2024
        GROUP BY DATE_TRUNC('month', order_date)
    ),
    avg_monthly AS (
        SELECT AVG(total) AS avg_total FROM monthly_totals
    )
SELECT
    mt.month,
    mt.total,
    am.avg_total,
    mt.total - am.avg_total AS diff_from_avg
FROM monthly_totals mt
CROSS JOIN avg_monthly am
ORDER BY mt.month;

-- ==================================================
-- Recursive CTE (재귀 CTE)
-- ==================================================

-- 조직도 계층 구조 탐색
WITH RECURSIVE org_tree AS (
    -- Base case: 최상위 관리자 (manager_id가 NULL)
    SELECT id, name, manager_id, 1 AS level
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- Recursive case: 부하 직원 찾기
    SELECT e.id, e.name, e.manager_id, ot.level + 1
    FROM employees e
    JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT * FROM org_tree ORDER BY level, name;

-- 결과:
-- | id | name    | manager_id | level |
-- |----|---------|------------|-------|
-- | 1  | CEO     | NULL       | 1     |
-- | 2  | VP_1    | 1          | 2     |
-- | 3  | VP_2    | 1          | 2     |
-- | 4  | Manager | 2          | 3     |
-- | 5  | Staff   | 4          | 4     |
```

#### 집합 연산 (Set Operations)

```sql
-- UNION: 합집합 (중복 제거)
SELECT name FROM employees
UNION
SELECT name FROM contractors;

-- UNION ALL: 합집합 (중복 유지, 더 빠름)
SELECT name FROM employees
UNION ALL
SELECT name FROM contractors;

-- INTERSECT: 교집합
SELECT product_id FROM orders_2023
INTERSECT
SELECT product_id FROM orders_2024;
-- 2023년과 2024년 모두 주문된 상품

-- EXCEPT (MINUS): 차집합
SELECT product_id FROM orders_2023
EXCEPT
SELECT product_id FROM orders_2024;
-- 2023년에는 있지만 2024년에는 없는 상품
```

#### NULL 처리

```sql
-- NULL 체크
SELECT * FROM employees WHERE manager_id IS NULL;
SELECT * FROM employees WHERE manager_id IS NOT NULL;

-- COALESCE: 첫 번째 NULL이 아닌 값 반환
SELECT
    name,
    COALESCE(phone, mobile, 'No Phone') AS contact
FROM employees;

-- NULLIF: 두 값이 같으면 NULL 반환 (0으로 나누기 방지 등)
SELECT total / NULLIF(count, 0) AS average
FROM stats;

-- CASE WHEN: NULL 포함 조건 처리
SELECT
    name,
    CASE
        WHEN salary IS NULL THEN 'Not Set'
        WHEN salary < 50000 THEN 'Low'
        WHEN salary < 80000 THEN 'Medium'
        ELSE 'High'
    END AS salary_level
FROM employees;

-- NULL 정렬 순서 제어
SELECT * FROM employees
ORDER BY salary NULLS FIRST;  -- NULL이 맨 앞에
ORDER BY salary NULLS LAST;   -- NULL이 맨 뒤에
```

---

## 3. Semantic Comparison (데이터베이스별 차이)

### 3.1 Quick Reference Table

| Topic | PostgreSQL | MySQL | Oracle | SQL Server | SQLite |
|-------|------------|-------|--------|------------|--------|
| **String concat** | `||` | `CONCAT()` | `||` | `+` | `||` |
| **Auto increment** | `SERIAL` | `AUTO_INCREMENT` | `SEQUENCE` | `IDENTITY` | `AUTOINCREMENT` |
| **String quotes** | `'single'` | `'single'` or `"double"` | `'single'` | `'single'` | `'single'` |
| **Identifier quotes** | `"double"` | `` `backtick` `` | `"double"` | `[brackets]` | `"double"` or `` ` `` |
| **LIMIT/OFFSET** | `LIMIT n OFFSET m` | `LIMIT m, n` or `LIMIT n OFFSET m` | `FETCH FIRST n` | `TOP n` or `OFFSET FETCH` | `LIMIT n OFFSET m` |
| **Boolean type** | `BOOLEAN` | `TINYINT(1)` | `NUMBER(1)` | `BIT` | `INTEGER` |
| **Window functions** | Full support | 8.0+ | Full support | Full support | 3.25+ |
| **CTE** | `WITH` | `WITH` (8.0+) | `WITH` | `WITH` | `WITH` |
| **Upsert** | `ON CONFLICT` | `ON DUPLICATE KEY` | `MERGE` | `MERGE` | `ON CONFLICT` |
| **Array type** | `ARRAY[]` | Not native | `VARRAY` | Not native | Not native |
| **JSON type** | `JSON`/`JSONB` | `JSON` | `JSON` | `JSON` (2016+) | `JSON` (3.38+) |
| **Date functions** | `DATE_TRUNC()` | `DATE_FORMAT()` | `TRUNC()` | `DATEPART()` | `strftime()` |
| **Current date** | `CURRENT_DATE` | `CURDATE()` | `SYSDATE` | `GETDATE()` | `DATE('now')` |

### 3.2 Auto Increment (자동 증가)

```sql
-- PostgreSQL
CREATE TABLE users (
    id SERIAL PRIMARY KEY,           -- 또는 GENERATED ALWAYS AS IDENTITY
    name VARCHAR(100)
);

-- MySQL
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100)
);

-- Oracle
CREATE SEQUENCE user_seq START WITH 1;
CREATE TABLE users (
    id NUMBER DEFAULT user_seq.NEXTVAL PRIMARY KEY,
    name VARCHAR2(100)
);

-- SQL Server
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100)
);

-- SQLite
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);
```

### 3.3 LIMIT/Pagination (페이지네이션)

```sql
-- PostgreSQL, MySQL 8.0+, SQLite
SELECT * FROM employees
ORDER BY salary DESC
LIMIT 10 OFFSET 20;  -- 21~30번째 행

-- MySQL (alternative)
SELECT * FROM employees
ORDER BY salary DESC
LIMIT 20, 10;  -- LIMIT offset, count

-- Oracle 12c+
SELECT * FROM employees
ORDER BY salary DESC
OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY;

-- Oracle (older versions)
SELECT * FROM (
    SELECT e.*, ROWNUM rn FROM (
        SELECT * FROM employees ORDER BY salary DESC
    ) e WHERE ROWNUM <= 30
) WHERE rn > 20;

-- SQL Server 2012+
SELECT * FROM employees
ORDER BY salary DESC
OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY;

-- SQL Server (older versions)
SELECT TOP 10 * FROM (
    SELECT TOP 30 * FROM employees ORDER BY salary DESC
) AS t ORDER BY salary ASC;
```

### 3.4 String Concatenation (문자열 연결)

```sql
-- PostgreSQL, Oracle, SQLite
SELECT first_name || ' ' || last_name AS full_name FROM users;

-- MySQL
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;
SELECT CONCAT_WS(' ', first_name, middle_name, last_name) AS full_name FROM users;

-- SQL Server
SELECT first_name + ' ' + last_name AS full_name FROM users;
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;  -- 2012+
```

### 3.5 Date/Time Functions (날짜 함수)

```sql
-- 현재 날짜/시간
-- PostgreSQL:  CURRENT_DATE, CURRENT_TIMESTAMP, NOW()
-- MySQL:       CURDATE(), NOW(), CURRENT_TIMESTAMP
-- Oracle:      SYSDATE, SYSTIMESTAMP
-- SQL Server:  GETDATE(), CURRENT_TIMESTAMP
-- SQLite:      DATE('now'), DATETIME('now')

-- 날짜 추출
-- PostgreSQL
EXTRACT(YEAR FROM hire_date)
DATE_TRUNC('month', hire_date)

-- MySQL
YEAR(hire_date)
DATE_FORMAT(hire_date, '%Y-%m')

-- Oracle
EXTRACT(YEAR FROM hire_date)
TRUNC(hire_date, 'MM')

-- SQL Server
YEAR(hire_date)
DATEPART(year, hire_date)

-- SQLite
strftime('%Y', hire_date)

-- 날짜 연산
-- PostgreSQL
hire_date + INTERVAL '1 month'
hire_date - INTERVAL '7 days'

-- MySQL
DATE_ADD(hire_date, INTERVAL 1 MONTH)
DATE_SUB(hire_date, INTERVAL 7 DAY)

-- Oracle
hire_date + INTERVAL '1' MONTH
hire_date - 7

-- SQL Server
DATEADD(month, 1, hire_date)
DATEADD(day, -7, hire_date)
```

### 3.6 Upsert (Insert or Update)

```sql
-- PostgreSQL
INSERT INTO users (id, name, email)
VALUES (1, 'Alice', 'alice@email.com')
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name, email = EXCLUDED.email;

-- MySQL
INSERT INTO users (id, name, email)
VALUES (1, 'Alice', 'alice@email.com')
ON DUPLICATE KEY UPDATE
name = VALUES(name), email = VALUES(email);

-- Oracle / SQL Server (MERGE)
MERGE INTO users target
USING (SELECT 1 AS id, 'Alice' AS name, 'alice@email.com' AS email FROM dual) source
ON (target.id = source.id)
WHEN MATCHED THEN
    UPDATE SET name = source.name, email = source.email
WHEN NOT MATCHED THEN
    INSERT (id, name, email) VALUES (source.id, source.name, source.email);

-- SQLite
INSERT INTO users (id, name, email)
VALUES (1, 'Alice', 'alice@email.com')
ON CONFLICT (id) DO UPDATE
SET name = excluded.name, email = excluded.email;
```

---

## 4. Common Pitfalls (흔한 실수)

### 4.1 NULL 관련 실수

```sql
-- 실수 1: NULL과 = 비교
SELECT * FROM employees WHERE manager_id = NULL;  -- 결과 없음!

-- 해결: IS NULL 사용
SELECT * FROM employees WHERE manager_id IS NULL;

-- 실수 2: NOT IN에 NULL이 포함되면 결과가 비어버림
SELECT * FROM employees
WHERE dept_id NOT IN (SELECT id FROM departments);
-- departments에 NULL이 있으면 아무것도 안 나옴!

-- 해결: NOT EXISTS 또는 NULL 제외
SELECT * FROM employees
WHERE NOT EXISTS (SELECT 1 FROM departments WHERE id = employees.dept_id);
-- 또는
WHERE dept_id NOT IN (SELECT id FROM departments WHERE id IS NOT NULL);

-- 실수 3: NULL과의 연산은 NULL
SELECT 100 + NULL;           -- NULL
SELECT 'Hello' || NULL;      -- NULL (PostgreSQL)
SELECT NULL = NULL;          -- NULL (TRUE 아님!)
```

### 4.2 GROUP BY 관련 실수

```sql
-- 실수: SELECT에 있는 열이 GROUP BY에 없음
SELECT name, dept, SUM(salary)  -- name은 집계 안 됨!
FROM employees
GROUP BY dept;

-- 해결 1: GROUP BY에 추가
SELECT name, dept, SUM(salary)
FROM employees
GROUP BY name, dept;

-- 해결 2: 집계 함수 사용
SELECT MAX(name), dept, SUM(salary)
FROM employees
GROUP BY dept;

-- 해결 3: Window Function 사용
SELECT name, dept, SUM(salary) OVER (PARTITION BY dept) AS dept_total
FROM employees;
```

### 4.3 JOIN 관련 실수

```sql
-- 실수 1: 카테시안 곱 (의도치 않은 CROSS JOIN)
SELECT * FROM employees, departments;  -- 모든 조합이 나옴!

-- 해결: 명시적 JOIN 조건
SELECT * FROM employees e
JOIN departments d ON e.dept_id = d.id;

-- 실수 2: LEFT JOIN 후 WHERE로 NULL 필터링 (INNER JOIN 효과)
SELECT * FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id
WHERE d.name = 'IT';  -- LEFT JOIN 의미 없어짐!

-- 해결: JOIN 조건에 포함하거나 OR IS NULL 추가
SELECT * FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id AND d.name = 'IT';
-- 또는
WHERE d.name = 'IT' OR d.name IS NULL;

-- 실수 3: 다대다 관계에서 중복
-- 만약 employee-project가 다대다면 JOIN 시 행 수 폭발!
-- 해결: DISTINCT 또는 집계 함수 사용
SELECT DISTINCT e.name FROM employees e
JOIN projects p ON ...;
```

### 4.4 성능 관련 실수

```sql
-- 실수 1: SELECT * 남용
SELECT * FROM large_table;  -- 불필요한 열까지 모두 조회

-- 해결: 필요한 열만 명시
SELECT id, name FROM large_table;

-- 실수 2: 함수로 인덱스 무효화
SELECT * FROM employees WHERE YEAR(hire_date) = 2024;
-- hire_date 인덱스 사용 못함!

-- 해결: 범위 조건으로 변경
SELECT * FROM employees
WHERE hire_date >= '2024-01-01' AND hire_date < '2025-01-01';

-- 실수 3: N+1 쿼리 (애플리케이션 레벨)
-- 루프에서 각 행마다 추가 쿼리 실행

-- 해결: JOIN으로 한 번에 조회
SELECT e.*, d.name AS dept_name
FROM employees e
JOIN departments d ON e.dept_id = d.id;

-- 실수 4: LIKE '%keyword%' (앞에 % 있으면 인덱스 못 씀)
SELECT * FROM products WHERE name LIKE '%phone%';

-- 해결: Full-text search 사용 또는 앞부분 매칭
SELECT * FROM products WHERE name LIKE 'phone%';  -- 인덱스 사용 가능
```

### 4.5 기타 실수

```sql
-- 실수: ORDER BY 없이 LIMIT (결과 비결정적)
SELECT * FROM employees LIMIT 10;  -- 순서 보장 없음!

-- 해결: 항상 ORDER BY와 함께
SELECT * FROM employees ORDER BY id LIMIT 10;

-- 실수: DISTINCT와 ORDER BY 충돌
SELECT DISTINCT dept FROM employees ORDER BY name;  -- 에러!

-- 해결: ORDER BY에 사용할 열도 SELECT에 포함
SELECT DISTINCT dept, MIN(name) FROM employees
GROUP BY dept ORDER BY MIN(name);

-- 실수: 시간대 미고려
SELECT * FROM events WHERE event_time = '2024-01-01 00:00:00';
-- 시간대에 따라 다른 결과!

-- 해결: UTC 사용 또는 AT TIME ZONE 명시
SELECT * FROM events
WHERE event_time AT TIME ZONE 'UTC' = '2024-01-01 00:00:00+00';
```

---

## 5. Interview Focus (면접 포인트)

### 5.1 면접 빈출 주제

#### Q1: "INNER JOIN과 LEFT JOIN의 차이는?"

```
INNER JOIN:
- 양쪽 테이블에 모두 매칭되는 행만 반환
- 매칭 안 되면 결과에서 제외
- A ∩ B (교집합)

LEFT JOIN (LEFT OUTER JOIN):
- 왼쪽 테이블의 모든 행 반환
- 오른쪽에 매칭되는 행이 없으면 NULL로 채움
- A + (A ∩ B)

예시:
employees: {1, 2, 3} (dept_id: 10, 20, NULL)
departments: {10, 20, 30}

INNER JOIN 결과: 1(10), 2(20) - 2행
LEFT JOIN 결과:  1(10), 2(20), 3(NULL) - 3행
```

#### Q2: "Window Function으로 순위를 매기는 법은?"

```sql
-- 세 가지 순위 함수 비교
SELECT
    name, salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num,
    RANK() OVER (ORDER BY salary DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank
FROM employees;

-- 예: 급여 100, 100, 90, 80
-- ROW_NUMBER: 1, 2, 3, 4 (항상 연속, 동점 구분)
-- RANK:       1, 1, 3, 4 (동점 같은 순위, 다음 건너뜀)
-- DENSE_RANK: 1, 1, 2, 3 (동점 같은 순위, 다음 연속)

-- 부서별 급여 순위
SELECT
    name, dept, salary,
    ROW_NUMBER() OVER (
        PARTITION BY dept
        ORDER BY salary DESC
    ) AS rank_in_dept
FROM employees;
```

#### Q3: "CTE를 사용하는 이유는?"

```
CTE (Common Table Expression) 장점:

1. 가독성 향상
   - 복잡한 쿼리를 단계별로 나눠서 이해하기 쉬움
   - 서브쿼리 중첩 대신 명명된 블록으로 구조화

2. 재사용성
   - 같은 서브쿼리를 여러 번 사용할 때 한 번만 정의

3. 재귀 쿼리 가능
   - 조직도, 카테고리 계층 등 트리 구조 탐색

4. 유지보수 용이
   - 각 단계를 독립적으로 테스트/수정 가능

예시:
WITH high_earners AS (
    SELECT * FROM employees WHERE salary > 80000
)
SELECT * FROM high_earners WHERE dept = 'IT';
```

#### Q4: "서브쿼리 최적화 방법은?"

```sql
-- 비효율적: Correlated Subquery (매 행마다 서브쿼리 실행)
SELECT * FROM employees e1
WHERE salary > (
    SELECT AVG(salary) FROM employees e2
    WHERE e2.dept_id = e1.dept_id
);

-- 최적화 1: JOIN으로 변환
SELECT e.*
FROM employees e
JOIN (
    SELECT dept_id, AVG(salary) AS avg_sal
    FROM employees
    GROUP BY dept_id
) d ON e.dept_id = d.dept_id AND e.salary > d.avg_sal;

-- 최적화 2: Window Function 사용
SELECT * FROM (
    SELECT
        *,
        AVG(salary) OVER (PARTITION BY dept_id) AS dept_avg
    FROM employees
) t
WHERE salary > dept_avg;

-- 최적화 3: EXISTS vs IN
-- 서브쿼리 결과가 많으면 EXISTS가 더 효율적
SELECT * FROM employees e
WHERE EXISTS (
    SELECT 1 FROM departments d
    WHERE d.id = e.dept_id AND d.location = 'Seoul'
);
```

#### Q5: "GROUP BY와 HAVING의 차이는?"

```sql
-- WHERE: 그룹화 전 개별 행 필터링
-- HAVING: 그룹화 후 그룹 필터링

SELECT dept, COUNT(*) AS emp_count, AVG(salary) AS avg_sal
FROM employees
WHERE hire_date >= '2020-01-01'    -- 개별 행 필터 (먼저 실행)
GROUP BY dept
HAVING COUNT(*) >= 5;               -- 그룹 필터 (나중 실행)

-- 실행 순서:
-- 1. FROM employees
-- 2. WHERE hire_date >= '2020-01-01' (개별 행 필터)
-- 3. GROUP BY dept
-- 4. HAVING COUNT(*) >= 5 (그룹 필터)
-- 5. SELECT

-- HAVING에서 집계 함수만 사용 가능 (GROUP BY 열 제외)
-- WHERE에서는 집계 함수 사용 불가
```

### 5.2 Palantir Context (팔란티어 맥락)

#### Foundry에서의 SQL 활용

```sql
-- Foundry Object Type은 SQL 테이블과 유사한 구조
-- Pipeline Builder에서 SQL Transform 지원

-- 예: 항공편 지연 분석
SELECT
    origin_airport,
    AVG(delay_minutes) AS avg_delay,
    COUNT(*) AS flight_count
FROM flights
WHERE flight_date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
GROUP BY origin_airport
HAVING COUNT(*) >= 100
ORDER BY avg_delay DESC;

-- Spark SQL과 호환 (대용량 데이터 처리)
-- Window Function으로 시계열 분석
SELECT
    flight_date,
    airline,
    delay_minutes,
    AVG(delay_minutes) OVER (
        PARTITION BY airline
        ORDER BY flight_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7day_avg
FROM flights;
```

#### AIP (Artificial Intelligence Platform)에서의 SQL

```
AIP에서 SQL 스킬이 중요한 이유:
1. 데이터 소스에서 직접 쿼리하여 context 제공
2. Function에서 SQL 기반 데이터 추출
3. 분석 결과를 Object로 저장

면접 시 자주 묻는 질문:
- "대용량 테이블에서 효율적으로 데이터 추출하는 방법?"
- "실시간 분석을 위한 쿼리 최적화 전략?"
- "Spark와 일반 SQL의 차이점?"
```

### 5.3 실전 면접 문제

```sql
-- 문제 1: 부서별 급여 상위 3명 조회
WITH ranked AS (
    SELECT
        name, dept, salary,
        DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rn
    FROM employees
)
SELECT name, dept, salary
FROM ranked
WHERE rn <= 3;

-- 문제 2: 연속 로그인 일수 계산 (streak)
WITH daily_logins AS (
    SELECT DISTINCT user_id, DATE(login_time) AS login_date
    FROM logins
),
numbered AS (
    SELECT
        user_id,
        login_date,
        login_date - INTERVAL '1 day' *
            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS grp
    FROM daily_logins
)
SELECT
    user_id,
    MIN(login_date) AS streak_start,
    MAX(login_date) AS streak_end,
    COUNT(*) AS streak_days
FROM numbered
GROUP BY user_id, grp
HAVING COUNT(*) >= 3;

-- 문제 3: 두 번째로 높은 급여 조회
SELECT MAX(salary) AS second_highest
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);

-- 또는 OFFSET 사용
SELECT DISTINCT salary
FROM employees
ORDER BY salary DESC
LIMIT 1 OFFSET 1;

-- 문제 4: 중복 데이터 삭제 (id가 가장 작은 것만 유지)
DELETE FROM employees
WHERE id NOT IN (
    SELECT MIN(id)
    FROM employees
    GROUP BY name, email
);

-- 문제 5: 누적 합계 (Running Total)
SELECT
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total
FROM orders;
```

---

## 6. Cross-References (관련 개념)

### Related KBs

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F50** | arrays_lists | 배열 타입 (PostgreSQL ARRAY) |
| **F51** | maps_dictionaries | JSON/JSONB 데이터 |
| **11a** | spark_basics | 분산 SQL 처리 (Spark SQL) |
| **13** | pipeline_builder | Foundry SQL Transform |
| **04** | data_layer | 데이터 모델링 |

### Design Philosophy Links

| Resource | URL | Description |
|----------|-----|-------------|
| PostgreSQL Docs | https://www.postgresql.org/docs/current/ | 가장 표준에 가까운 SQL |
| MySQL Docs | https://dev.mysql.com/doc/ | 웹 개발에서 많이 사용 |
| SQL Standard | https://www.iso.org/standard/63555.html | ISO SQL 표준 |
| W3Schools SQL | https://www.w3schools.com/sql/ | 초보자 튜토리얼 |
| SQLZoo | https://sqlzoo.net/ | 대화형 SQL 연습 |
| LeetCode SQL | https://leetcode.com/problemset/database/ | SQL 면접 문제 |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SQL FUNDAMENTALS CHEAT SHEET                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  기본 SELECT:                                                        │
│  SELECT column FROM table                                           │
│  WHERE condition                                                    │
│  GROUP BY column HAVING condition                                   │
│  ORDER BY column [ASC|DESC]                                         │
│  LIMIT n OFFSET m;                                                  │
│                                                                     │
│  실행 순서:                                                          │
│  FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  JOIN Types:                                                        │
│  INNER JOIN    양쪽 매칭만                                          │
│  LEFT JOIN     왼쪽 전부 + 매칭                                     │
│  RIGHT JOIN    매칭 + 오른쪽 전부                                   │
│  FULL OUTER    양쪽 전부                                            │
│  CROSS JOIN    카테시안 곱 (모든 조합)                              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  집계 함수:                                                          │
│  COUNT(*), COUNT(col), COUNT(DISTINCT col)                          │
│  SUM(col), AVG(col), MIN(col), MAX(col)                            │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Window Functions:                                                  │
│  ROW_NUMBER()  - 항상 연속 번호                                     │
│  RANK()        - 동점 같은 순위, 다음 건너뜀                        │
│  DENSE_RANK()  - 동점 같은 순위, 다음 연속                          │
│  LAG(col, n)   - n행 이전 값                                        │
│  LEAD(col, n)  - n행 이후 값                                        │
│  SUM() OVER()  - 누적 합계                                          │
│                                                                     │
│  Syntax: func() OVER (PARTITION BY x ORDER BY y)                    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  NULL 처리:                                                          │
│  IS NULL / IS NOT NULL (= NULL 안됨!)                               │
│  COALESCE(a, b, c)  - 첫 번째 NULL 아닌 값                          │
│  NULLIF(a, b)       - a=b면 NULL 반환                               │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  흔한 실수:                                                          │
│  1. col = NULL (X) → col IS NULL (O)                                │
│  2. NOT IN + NULL = 빈 결과 → NOT EXISTS 사용                       │
│  3. GROUP BY 없이 집계 + 일반 컬럼 혼용                             │
│  4. LEFT JOIN + WHERE 우측 조건 = INNER JOIN 효과                   │
│  5. WHERE 함수(col) → 인덱스 못 씀                                  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  면접 핵심:                                                          │
│  - INNER vs LEFT JOIN 차이 설명                                     │
│  - ROW_NUMBER vs RANK vs DENSE_RANK 차이                            │
│  - Correlated Subquery 최적화 방법                                  │
│  - GROUP BY vs HAVING vs WHERE 실행 순서                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
