from sqlalchemy import create_engine, DateTime, func, Boolean, Float, PickleType
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref, Query

Base = declarative_base()


class Users(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer)
    group = Column(String)

    def __init__(self, vk_id, group):
        self.vk_id = vk_id
        self.group = group


class DatabaseFunction(object):
    def __init__(self):
        self.meta = MetaData()
        self.engine = create_engine('sqlite:///db.db')
        Base.metadata.create_all(self.engine)

    def save_user(self, vk_id, group):
        session = sessionmaker(bind=self.engine)()
        query = session.query(Users).filter(Users.vk_id == vk_id).first()
        if query is None:
            user = Users(vk_id, group)
            session.add(user)
        else:
            query.group = group

        session.commit()
        session.close()

    def get_group(self, vk_id):
        session = sessionmaker(bind=self.engine)()
        query = session.query(Users).filter(Users.vk_id == vk_id).first()
        res = ''
        if query is None:
            res = "Нет группы"
        else:
            res = query.group
        session.close()
        return res


if __name__ == '__main__':
    pass