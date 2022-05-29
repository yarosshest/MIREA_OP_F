import re

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


class Tables(Base):
    __tablename__ = 'Tables'
    id = Column(Integer, primary_key=True)
    group = Column(String)
    subject = Column(String)
    form = Column(String)
    teacher = Column(String)
    room = Column(String)
    row = Column(Integer)

    def __init__(self, group, subject, form, teacher, room, row):
        self.group = group
        self.subject = subject
        self.form = form
        self.teacher = teacher
        self.room = room
        self.row = row


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

    def add_table(self, group, subject, form, teacher, room, row):
        if teacher == "nan":
            teacher = ''
        if subject == "nan":
            subject = ''
        if room == "nan":
            room = ''
        if form == "nan":
            form = ''
        tab = Tables(group, subject, form, teacher, room, row)
        session = sessionmaker(bind=self.engine)()
        session.add(tab)
        session.commit()
        session.close()

    def get_table_group(self, name):
        session = sessionmaker(bind=self.engine)()
        query = session.query(Tables).filter(Tables.group == name)
        res = ["-" for i in range(0, 72)]
        for i in query:
            res[i.row] = i.subject + ' ' + i.form + ' ' + i.teacher + ' ' + i.room
        session.close()
        return res

    def get_table_teacher(self, name):
        session = sessionmaker(bind=self.engine)()
        query = session.query(Tables).filter(Tables.teacher == name)
        if query is None:
            return None
        else:
            res = ["-" for i in range(0, 72)]
            for i in query:
                res[i.row] = i.subject + ' ' + i.form + ' ' + i.room
            session.close()
            return res

    def get_teachers(self, name):
        session = sessionmaker(bind=self.engine)()
        name = name[0].upper() + name[1:]
        pattern = re.compile(fr"^{name} \w.\w.$")
        query = session.query(Tables.teacher).distinct()
        res = []
        for i in query:
            teacher = pattern.findall(i.teacher)
            for j in teacher:
                res.append(j)
        session.close()
        return res


if __name__ == '__main__':
    # pass
    db = DatabaseFunction()
    print(db.get_teachers("Иванов"))
