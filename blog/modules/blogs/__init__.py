from flask import Blueprint

# 创建新闻模块的蓝图对象

blog_blue = Blueprint('blog_blue', __name__, url_prefix='/api')

# 把使用蓝图对象的文件，导入到创建蓝图对象的下面
from . import views
