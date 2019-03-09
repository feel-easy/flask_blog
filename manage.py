from flask_migrate import MigrateCommand, Migrate

# 使用管理器
from flask_script import Manager
# 导入工厂函数
from blog import create_app, db, models

# 调用__init__文件中的工厂函数，获取app
from blog.models import User

app = create_app('development')

manage = Manager(app)
Migrate(app, db)
manage.add_command('db', MigrateCommand)


# 创建管理员账户
# 在script扩展，自定义脚本命令，以自定义函数的形式实现创建管理员用户
# 以终端启动命令的形式实现；
# 在终端使用命令：python manage.py create_supper_user -n admin -p 123456
@manage.option('-n', '-name', dest='name')
@manage.option('-p', '-password', dest='password')
def create_supper_user(name, password):
    if not all([name, password]):
        print('参数缺失')
    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
    print('管理员创建成功')


if __name__ == '__main__':
    print(app.url_map)
    manage.run()



