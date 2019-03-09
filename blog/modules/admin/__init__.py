from flask import Blueprint, session, request, url_for, redirect

admin_blue = Blueprint('admin', __name__, url_prefix='/admin')

from . import views


@admin_blue.before_request
def check_admin():
    # if 不是管理员，那么直接跳转到主页
    is_admin = session.get("is_admin", False)
    # if not is_admin and 当前访问的url不是管理登录页:要求用户必须先登录后台页面
    print(url_for('.login'))
    print(url_for('admin.login'))
    if not is_admin and not request.url.endswith(url_for('admin.login')):
        return redirect('/')
