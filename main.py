# encoding: utf-8
"""
@author : shirukai
@date : 2021/7/22

"""
import os

from flask import Flask, jsonify, request

from models import db, User, auto_alter_tables

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
# 使用本地的sqlite数据库
app.config.from_mapping(**{
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///%s/application.db?check_same_thread=False' % BASE_DIR,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})
db.init_app(app)
with app.app_context():
    db.create_all()


@app.route('/users', methods=['POST'])
def add_users():
    """
    添加用户接口
    :return:
    """
    res = request.json
    user = User()
    for attr in User.__mapper__.attrs.keys():
        if attr in res:
            value = res[attr]
            setattr(user, attr, value)
    db.session.add(user)
    db.session.commit()
    return 'success'


@app.route('/users', methods=['GET'])
def get_users():
    """
    查询用户接口
    :return:
    """
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


# 更新表结构
auto_alter_tables(app)

app.run('localhost', 18111)
