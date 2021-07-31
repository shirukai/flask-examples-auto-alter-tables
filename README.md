# Flask中SQLAlchemy自动更新表结构

> Python: 2.7
>
> Flask: 1.0.3
> Flask-SQLAlchemy: 2.3.2
>
> SQLAlchemy: 1.3.12 
>
> Flask-SQLAlchemy是Flask中比较好用的ORM框架，说起ORM框架，熟悉SpringBoot开发的同学肯定对JPA比较了解，它们都是通过实体对象映射关系库中的表，操作实体对象，进行增删改查，减少了SQL的编写，非常方便。在JPA中，当我们修改了一个实体类之后（添加字段），对应的表结构可以自动发生更新，通常不需要人为干预。在Flask-SQLAlchemy中，并没有提供自动更新表结构的功能，网上也有不少方式去增强实现这个功能，比如表迁移新建、执行SQL等等。笔者经过一系列的搜索之后，没有找到一个自己比较满意的解决方案，所以总结了一个相对比较方便的方法，能够自动根据实体对象，自动更新表结构。
>
> 项目Github地址：https://github.com/shirukai/flask-examples-auto-alter-tables.git

# 1 思路

思路非常的简单：

 	1. 拿到数据库所有表及字段信息
 	2. 拿到继承db.Model的所有子类
 	3. 分析实体类字段与表字段是否一致
 	4. 不一致，将进行更新操，目前只进行字段新增的判断

# 2 实现

## 2.1 技术点讲解

结合上面的实现思路，在进行实现之前，先简单列一下几个技术点：

1. **如何拿到数据库所有表及字段信息？**

   通过`db.engin.table_names()`可以拿到所有的表名

   通过`sqlalchemy.Table()`可以拿到具体的表元数据

2. **如何拿到db.Model所有子类**

   直接通过`db.Model.__subclasses__()`

3. **如何修改表**

   `db.engine.execute()`可以执行对应的修改表结构的语句

## 2.2 代码实现

### 2.2.1 创建项目

PyCharm创建一个名为flask-examples-auto-alter-tables的项目，Python选2.7，其它版本也可以。

![image-20210731112327625](https://cdn.jsdelivr.net/gh/shirukai/images/20210731112332.png)

### 2.2.2 安装依赖

在项目下创建名为requirements.txt的文件，添加如下内容：

```
SQLAlchemy==1.3.12
Flask==1.0.3
Flask_SQLAlchemy==2.3.2

```

pip安装依赖

```
pip install -r requirements.txt
```

### 2.2.3 编写实体类以及自动更新表的方法

在项目下创建一个models.py的文件，内容如下:

```python
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

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in self.__mapper__.attrs.keys()}

```

### 2.2.4 编写Flask应用

在项目下创建一个名为main.py的文件，内容如下：

```python
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
```

## 2.3 效果演示

1. 执行main.py启动Flask应用，右击直接运行即可：

   ![image-20210731113508582](https://cdn.jsdelivr.net/gh/shirukai/images/20210731113508.png)

2. 调用创建用户的接口：

   POST请求，请求参数为

   ```json
   {
       "name":"小明"
   }
   ```

   ![image-20210731113644399](https://cdn.jsdelivr.net/gh/shirukai/images/20210731113644.png)

3. 调用查询用户的接口：

   GET请求，请求结果为

   ```json
   [
       {
           "id": "3af2b9b5f1b011eb8315acde48001122",
           "name": "小明"
       }
   ]
   ```

   ![image-20210731113814319](https://cdn.jsdelivr.net/gh/shirukai/images/20210731113814.png)

4. 修改models.py里的User实体类，添加一个age字段

   ```python
   class User(db.Model):
       """
       用户表
       """
       __tablename__ = 'user'
       id = db.Column(db.String(32), primary_key=True, default=uuid.uuid1().hex, comment='用户ID')
       name = db.Column(db.String(32), nullable=False, comment='用户名称')
       # 新增字段
       age = db.Column(db.Integer, nullable=True, comment='年龄')
   
       def to_dict(self):
           return {attr: getattr(self, attr) for attr in self.__mapper__.attrs.keys()}
   ```

5. 完成上述修改之后重新启动应用

6. 调用创建用户的接口

   POST请求，请求参数为

   ```json
   {
       "name":"小明",
       "age":19
   }
   ```

   ![image-20210731114304998](https://cdn.jsdelivr.net/gh/shirukai/images/20210731114305.png)

7. 调用查询用户的接口

   ![image-20210731114334431](https://cdn.jsdelivr.net/gh/shirukai/images/20210731114334.png)

# 3 总结

目前当前项目只实现了表的新增字段，对于其它需求，如字段类型变更、字段删除等操作，可以参考这个思路实现，但是要注意对表中原有数据产生的影响。目前代码已经上传至Github，地址：https://github.com/shirukai/flask-examples-auto-alter-tables.git。
