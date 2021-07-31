# encoding: utf-8
"""
@author : shirukai
@date : 2021/7/22

"""
import uuid

import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import InstrumentedAttribute

db = SQLAlchemy()


def auto_alter_tables(flask_app):
    """
    自动修改表结构
    :param flask_app:
    :return:
    """
    with flask_app.app_context():
        metadata = sqlalchemy.MetaData()
        tables = {table_name: {column.name: column for column in
                               sqlalchemy.Table(table_name, metadata, autoload=True, autoload_with=db.engine).c}
                  for table_name in db.engine.table_names()}
        models = db.Model.__subclasses__()
        for model_class in models:
            table_name = model_class.__table__.name
            if table_name in tables:
                table = tables[table_name]
                for attr_name in dir(model_class):
                    attr = getattr(model_class, attr_name)
                    if isinstance(attr, InstrumentedAttribute) \
                            and hasattr(attr, 'type') \
                            and hasattr(attr, 'compile'):
                        attr_name = attr.name
                        # 添加新字段
                        if attr_name not in table:
                            column_type = attr.type.compile(dialect=db.engine.dialect)
                            db.engine.execute(
                                'ALTER TABLE %s ADD COLUMN %s %s' % (table_name, attr_name, column_type))


class User(db.Model):
    """
    用户表
    """
    __tablename__ = 'user'
    id = db.Column(db.String(32), primary_key=True, default=uuid.uuid1().hex, comment='用户ID')
    name = db.Column(db.String(32), nullable=False, comment='用户名称')
    age = db.Column(db.Integer, nullable=True, comment='年龄')

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in self.__mapper__.attrs.keys()}
