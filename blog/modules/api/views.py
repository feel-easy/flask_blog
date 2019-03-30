# 使用蓝图对象
import datetime

from dateutil.relativedelta import relativedelta
from flask import session, render_template, current_app, jsonify, request, g

from blog import constants, db
from blog.models import User, Category, Blogs, CommentLike, Comment
from blog.utils.commons import login_required
from blog.utils.response_code import RET
from . import api_blue

import hashlib
from werkzeug.security import generate_password_hash, check_password_hash


@api_blue.route('/list/', methods=['GET'])
def getBlogsList():
    """
    博客列表
    1、获取参数，cid，page，per_page
    2、检查参数的类型
    3、根据cid来查询mysql数据库,最新
    如果用户选择的是最新，默认查询所有博客数据
    News.query.filter().order_by(News.create_time.desc()).paginate(page,per_page,False)
    News.query.filter(News.category_id==cid).order_by(News.create_time.desc()).paginate(page,per_page,False)
    4、获取分页后的数据
    总页数、当前页数、博客列表
    5、返回结果
    :return:
    """
    # 获取参数
    ordertype = request.args.get('ordertype', '1')
    cid = request.args.get('cid', '1')
    page = request.args.get('page', '1')
    per_page = request.args.get('per_page', '10')
    # print(cid, page, per_page)
    # 转换参数的数据类型
    try:
        cid, page, per_page, ordertype = int(cid), int(page), int(per_page), int(ordertype)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')
    # 定义容器，存储查询的过滤条件
    filters = [Blogs.status == 0]
    # 判断分类id如果不是最新
    if cid > 1:
        filters.append(Blogs.category_id == cid)
    # 使用过滤条件查询mysql，按照博客发布时间排序
    # print(filters)
    try:
        # *filters表示python中拆包，News.category_id==cid，*filters里面存储的是sqlalchemy对象
        # 在python中测试添加的数据为True或False
        if ordertype == 1:
            paginate = Blogs.query.filter(*filters).order_by(Blogs.create_time.desc()).paginate(page, per_page, False)
        else:
            paginate = Blogs.query.filter(*filters).order_by(Blogs.clicks.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询博客数据失败')
    # 获取分页后的数据
    blogs_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page
    # 定义容器，存储查询到的博客数据
    blogs_dict_list = []
    for blog in blogs_list:
        blogs_dict_list.append(blog.to_dict())
    data = {
        'blogs_dict_list': blogs_dict_list,
        'total_page': total_page,
        'current_page': current_page
    }
    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@api_blue.route('/list/archives/')
def getBlogsArchivesList():
    """
    博客归档列表
    :return:
    """
    # 获取参数

    # 转换参数的数据类型

    # 定义容器，存储查询的过滤条件
    filters = [Blogs.status == 0]
    try:
        # *filters表示python中拆包，News.category_id==cid，*filters里面存储的是sqlalchemy对象
        blogs_list = Blogs.query.filter(*filters).order_by(Blogs.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询博客数据失败')

    firstblogtime = blogs_list[-1].create_time
    lastblogtime = blogs_list[0].create_time
    # firstblogtime = firstblogtime.replace(day=1)
    firsttime = firstblogtime.combine(firstblogtime.replace(day=1).date(), datetime.time(0, 0, 0, 0))
    lasttime = firstblogtime.combine(lastblogtime.replace(day=1).replace(month=lastblogtime.month + 1).date(),
                                     datetime.time(0, 0, 0, 0))

    # print(firsttime, lasttime)
    datalist = []
    begin_date = firsttime
    while begin_date < lasttime:
        end_date = begin_date + relativedelta(months=+1)

        mouth_data = [i.to_dict() for i in blogs_list if begin_date <= i.create_time < end_date]
        # mouth_data.reverse()
        if mouth_data:
            datalist.append({'mouth': begin_date.date().strftime('%Y/%m'), 'mouth_data': mouth_data})
        begin_date += relativedelta(months=+1)
    # print(datalist)
    # # 定义容器，存储查询到的博客数据
    # blogs_dict_list = []
    # for blog in blogs_list:
    #     blogs_dict_list.append(blog.to_dict())
    datalist.reverse()
    data = {
        'blogs_dict_list': datalist,
    }
    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@api_blue.route('/study_list/', methods=['GET'])
def getStudyList():
    data = [
        {'name': 'Python学习交流群', 'content': [{'name': '310828874', 'url': ''}]},
        {'name': '知乎专栏', 'content': [{'name': 'Django 学习小组', 'url': ''}]}
    ]
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@api_blue.route('/friendlylink_list/',methods=['GET'])
def friendlylink_list():
    data = [
        {'name': '互联网运营', 'url':'https://www.paurl.com/'},
        {'name': 'Django中文社区', 'url': 'http://www.dj-china.org/'},
        {'name': 'Vim教程网', 'url': 'https://vim.ink/'},
        {'name': '追梦人的博客', 'url': 'https://www.zmrenwu.com/'},

    ]
    return jsonify(errno=RET.OK, errmsg='OK', data=data)