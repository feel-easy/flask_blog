# flask_blog
This is a flask blog project to learn flask

```
一、项目基本流程：
搭建项目目录；在单文件中实现基本业务逻辑，拆分配置文件、拆分程序实例、拆分视图函数。
数据库迁移创建表：
python manage.py db init
python manage.py db migrate
python manage.py db upgrade

二、项目目录文档说明：
1、项目根目录                说明
   /blog              项目应用核心目录
   /logs              项目日志目录
   config.py           项目配置文件--保存session信息、调试模式、密钥等
   manage.py            项目启动文件
   requirements.txt      项目依赖文件

2、项目/blog目录                说明
   /libs              项目用到的资源库--第三方扩展(云通信)
   /modules            项目模块--所有的蓝图对象和视图函数
   /static                 项目静态文件夹
   /templates          项目模板文件夹
   /utils             项目通用设施--自定义状态码、七牛云上传图片等
   __init__.py              项目应用初始化文件--应用程序实例、数据库实例、注册蓝图、日志、CSRF等
   constants.py         项目常量信息--数据库缓存信息、验证码、新闻信息等
   models.py           项目模型类

3、项目/blog/libs目录         说明


4、项目/blog/static目录       说明
   favicon.ico             项目logo

5、项目/blog/utils目录        说明
    captcha/              生成图片验证码工具
    response_code.py      自定义状态码
    commons.py            项目封装的辅助设施--登录验证装饰器login_required、自定义过滤器index_filter
```