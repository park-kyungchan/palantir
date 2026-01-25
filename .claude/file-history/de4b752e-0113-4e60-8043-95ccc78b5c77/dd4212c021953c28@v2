# Test models for /ontology-objecttype demonstration
# Simulating a simple HR system

from sqlalchemy import Column, String, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Employee(Base):
    """직원 정보를 관리하는 모델"""
    __tablename__ = 'employees'

    employee_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    department_id = Column(String(50), ForeignKey('departments.department_id'))
    hire_date = Column(Date)
    is_active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="employees")


class Department(Base):
    """부서 정보를 관리하는 모델"""
    __tablename__ = 'departments'

    department_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    budget = Column(Integer)

    employees = relationship("Employee", back_populates="department")


class AuditLog(Base):
    """감사 로그 - Helper 클래스 (ObjectType 아님)"""
    __tablename__ = 'audit_logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(50))
    timestamp = Column(Date)
    user_id = Column(String(50))


class EmployeeDTO:
    """직원 데이터 전송 객체 - DTO (ObjectType 아님)"""
    def __init__(self, employee_id: str, name: str):
        self.employee_id = employee_id
        self.name = name
