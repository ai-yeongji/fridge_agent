"""
냉장고 음식 관리 데이터베이스 모델
"""
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class FoodItem(Base):
    """음식 아이템 모델"""
    __tablename__ = 'food_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # 채소, 육류, 유제품, 과일, 조미료, 기타
    purchase_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    location = Column(String(20), nullable=False, default='냉장')  # 냉장, 냉동, 실온
    quantity = Column(Float, default=1.0)
    unit = Column(String(20), default='개')
    memo = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def days_until_expiry(self):
        """소비기한까지 남은 일수"""
        return (self.expiry_date - date.today()).days

    def status(self):
        """음식 상태 (신선, 임박, 만료)"""
        days = self.days_until_expiry()
        if days < 0:
            return "만료"
        elif days <= 3:
            return "임박"
        else:
            return "신선"

    def __repr__(self):
        return f"<FoodItem(name='{self.name}', expiry='{self.expiry_date}', status='{self.status()}')>"


class Database:
    """데이터베이스 관리 클래스"""

    def __init__(self, db_url='sqlite:///fridge.db'):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """세션 생성"""
        return self.Session()

    def add_food(self, name, category, purchase_date, expiry_date, location='냉장',
                 quantity=1.0, unit='개', memo=None):
        """음식 추가"""
        session = self.get_session()
        try:
            food = FoodItem(
                name=name,
                category=category,
                purchase_date=purchase_date,
                expiry_date=expiry_date,
                location=location,
                quantity=quantity,
                unit=unit,
                memo=memo
            )
            session.add(food)
            session.commit()
            return food
        finally:
            session.close()

    def get_all_foods(self):
        """모든 음식 조회"""
        session = self.get_session()
        try:
            return session.query(FoodItem).order_by(FoodItem.expiry_date).all()
        finally:
            session.close()

    def get_expiring_soon(self, days=3):
        """곧 만료될 음식 조회"""
        session = self.get_session()
        try:
            today = date.today()
            target_date = today + __import__('datetime').timedelta(days=days)
            return session.query(FoodItem).filter(
                FoodItem.expiry_date >= today,
                FoodItem.expiry_date <= target_date
            ).order_by(FoodItem.expiry_date).all()
        finally:
            session.close()

    def get_expired_foods(self):
        """만료된 음식 조회"""
        session = self.get_session()
        try:
            today = date.today()
            return session.query(FoodItem).filter(
                FoodItem.expiry_date < today
            ).order_by(FoodItem.expiry_date.desc()).all()
        finally:
            session.close()

    def update_food(self, food_id, **kwargs):
        """음식 정보 수정"""
        session = self.get_session()
        try:
            food = session.query(FoodItem).filter(FoodItem.id == food_id).first()
            if food:
                for key, value in kwargs.items():
                    if hasattr(food, key):
                        setattr(food, key, value)
                session.commit()
                return food
            return None
        finally:
            session.close()

    def delete_food(self, food_id):
        """음식 삭제"""
        session = self.get_session()
        try:
            food = session.query(FoodItem).filter(FoodItem.id == food_id).first()
            if food:
                session.delete(food)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_food_by_id(self, food_id):
        """ID로 음식 조회"""
        session = self.get_session()
        try:
            return session.query(FoodItem).filter(FoodItem.id == food_id).first()
        finally:
            session.close()
