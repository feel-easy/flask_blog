import time
from datetime import datetime, timedelta

from flask import g, render_template, request, session, redirect, url_for, jsonify, current_app, abort

from blog import constants, db
from blog.models import User, Category, Blogs
from blog.utils.commons import login_required
# from blog.utils.image_storage import storage
from blog.utils.response_code import RET
from . import admin_blue


@admin_blue.route('/index')
@login_required
def index():
    """后台管理首页"""
    user = g.user
    return render_template('admin/index.html', user=user.to_dict())


@admin_blue.route('/login', methods=['GET', 'POST'])
def login():
    """
    后台管理员登录
    1、如果为get请求，使用session获取登录信息，user_id,is_admin,
    2、判断用户如果用户id存在并是管理员，重定向到后台管理页面
    3、获取参数，user_name,password
    4、校验参数完整性
    5、查询数据库，确认用户存在，is_admin为true，校验密码
    6、缓存用户信息，user_id,mobile,nick_name,is_admin
    7、跳转到后台管理页面

    :return:
    """
    if request.method == 'GET':
        user_id = session.get('user_id', None)
        is_admin = session.get('is_admin', False)
        if user_id and is_admin:
            return redirect(url_for('admin.index'))
        return render_template('admin/login.html')

    user_name = request.form.get('username')
    password = request.form.get('password')
    if not all([user_name, password]):
        return render_template('admin/login.html', errmsg='参数不完整')
    try:
        user = User.query.filter(User.mobile == user_name, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg='数据库查询错误')
    if user is None or not user.check_password(password):
        return render_template('admin/login.html', errmsg='用户名或密码错误')
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    # 必须要缓存is_admin字段，用来确认用户是管理员还是普通用户
    session['is_admin'] = user.is_admin
    return redirect(url_for('admin.index'))


@admin_blue.route('/user_count')
def user_count():
    """
    用户统计：非管理员的人数
    1、总人数
    2、月新增人数(新注册)
    3、日新增人数(新注册)
    :return:
    """
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询总人数失败')

    # 月人数:当月1号到当前日期的注册人数
    t = time.localtime()
    # tm_year=2018, tm_mon=10, tm_mday=12
    # 定义每月的开始日期的字符串:2018-01-01;2018-10-01
    mon_begin_date_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    # 把日期字符串转成日期对象
    mon_begin_date = datetime.strptime(mon_begin_date_str, '%Y-%m-%d')
    # 比较日期
    mon_count = 0
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time > mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询月人数失败')

    # 日新增人数
    day_count = 0
    # 每天的开始日期字符串
    day_begin_date_str = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    # 把日期字符串转成日期对象
    day_begin_date = datetime.strptime(day_begin_date_str, '%Y-%m-%d')
    # 比较日期
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询日人数失败')
    # 统计用户活跃度、活跃时间
    active_count = []
    active_time = []
    # datetime.now() - timedelta(days=)
    # 获取当前日期
    now_date_str = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    # 格式化日期对象
    now_date = datetime.strptime(now_date_str, '%Y-%m-%d')
    # 循环往前推31天,获取每天的开始时间和结束时间
    for d in range(0, 31):
        begin_date = now_date - timedelta(days=d)
        end_date = now_date - timedelta(days=(d - 1))
        # 比较日期
        try:
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询活跃人数失败')
        # 把查询结果存入列表
        active_count.append(count)
        # 把日期对象转成日期字符串
        begin_date_str = datetime.strftime(begin_date, '%Y-%m-%d')
        # 把日期存入列表
        active_time.append(begin_date_str)

    # 列表反转
    active_time.reverse()
    active_count.reverse()

    data = {
        'total_count': total_count,
        'mon_count': mon_count,
        'day_count': day_count,
        'active_count': active_count,
        'active_time': active_time
    }

    return render_template('admin/user_count.html', data=data)


@admin_blue.route('/user_list')
def user_list():
    """
    用户列表
    1、获取参数，页数page，默认1
    2、校验参数，int(page)
    3、查询数据库，为管理员，分页
    4、遍历查询结果，转成字典数据
    5、返回模板admin/user_list.html，users,total_page,current_page
    :return:
    """
    page = request.args.get('p', '1')
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    users = []
    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = User.query.filter(User.is_admin == False).paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
        current_page = paginate.page
        total_page = paginate.pages
        users = paginate.items
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')
    # 定义容器遍历查询结果
    user_dict_list = []
    for user in users:
        user_dict_list.append(user.to_admin_dict())
    data = {
        'users': user_dict_list,
        'current_page': current_page,
        'total_page': total_page
    }
    return render_template('admin/user_list.html', data=data)


@admin_blue.route('/blogs_review')
def blogs_review():
    """
    博客审核列表
    1、获取参数，页数p，默认1，关键字参数keywords，默认None
    2、校验参数，int(page)
    3、定义过滤条件，filter[blogs.status!=0]，如果keywords存在，添加到过滤条件中
    4、查询博客数据库,默认按照博客的发布时间，分页
    5、遍历查询结果
    6、返回模板admin/blogs_review.html,total_page,current_page,blogs_list

    :return:
    """
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    blogs_list = []
    current_page = 1
    total_page = 1

    filters = [Blogs.status != 0]
    # 如果关键字存在，那么就添加关键字搜索
    if keywords:
        filters.append(Blogs.title.contains(keywords))
    try:
        paginate = Blogs.query.filter(*filters) \
            .order_by(Blogs.create_time.desc()) \
            .paginate(page, constants.ADMIN_BLOGS_PAGE_MAX_COUNT, False)

        blogs_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    blogs_dict_list = []
    for blogs in blogs_list:
        blogs_dict_list.append(blogs.to_review_dict())

    data = {"total_page": total_page, "current_page": current_page, "blogs_list": blogs_dict_list}

    return render_template('admin/blogs_review.html', data=data)


@admin_blue.route('/blogs_review_detail/<int:blogs_id>')
def blogs_review_detail(blogs_id):
    """
    博客详情
    1、根据blogs_id查询数据库
    2、判断查询结果
    3、返回模板，blogs:blogs.to_dict()

    :param blogs_id:
    :return:
    """
    blogs = None
    try:
        blogs = Blogs.query.get(blogs_id)
    except Exception as e:
        current_app.logger.error(e)
    if not blogs:
        return render_template('admin/blogs_review_detail.html', data={'errmsg': '未查到数据'})
    data = {"blogs": blogs.to_dict()}
    return render_template('admin/blogs_review_detail.html', data=data)


@admin_blue.route('/blogs_review_action', methods=['POST'])
def blogs_review_action():
    """
    博客审核
    1、获取参数，blogs_id,action
    2、校验参数完整
    3、校验参数action是否为accept,reject
    4、查询博客数据，校验查询结果
    5、判断action，如果接受，blogs_status = 0
    6、否则获取拒绝原因，reason,
        blogs_status = -1
        blogs_reason = reason
    7、返回结果

    :return:
    """
    blogs_id = request.json.get('blogs_id')
    action = request.json.get('action')
    if not all([blogs_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数类型错误")

    # 查询到指定的博客数据
    try:
        blogs = Blogs.query.get(blogs_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not blogs:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    if action == "accept":
        # 代表接受
        blogs.status = 0
    else:
        # 代表拒绝
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请输入拒绝原因")
        blogs.status = -1
        blogs.reason = reason
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    return jsonify(errno=RET.OK, errmsg="OK")


@admin_blue.route('/blogs_edit')
def blogs_edit():
    """
    博客板式编辑
    1、获取参数，页数p，默认1，关键字参数keywords，默认None
    2、校验参数，int(page)
    3、初始化变量,blogs_list[],current_page = 1,total_page = 1
    4、定义过滤条件，filter[blogs.status==0]，如果keywords存在，添加到过滤条件中
    5、查询博客数据库,默认按照博客的发布时间，分页
    6、遍历查询结果
    7、返回模板admin/blogs_review.html,total_page,current_page,blogs_list

    :return:
    """
    page = request.args.get('p', '1')
    keywords = request.args.get('keywords', None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    blogs_list = []
    current_page = 1
    total_page = 1
    filters = [Blogs.status != 0]
    if keywords:
        filters.append(Blogs.title.contains(keywords))
    try:
        paginate = Blogs.query.filter(*filters).paginate(page, constants.ADMIN_BLOGS_PAGE_MAX_COUNT, False)
        blogs_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    blogs_dict_list = []
    for blogs in blogs_list:
        blogs_dict_list.append(blogs.to_basic_dict())
    data = {
        'total_page': total_page,
        'current_page': current_page,
        'blogs_list': blogs_dict_list
    }
    return render_template('admin/blogs_edit.html', data=data)


@admin_blue.route('/blogs_edit_detail', methods=['GET', 'POST'])
def blogs_edit_detail():
    """
    博客编辑详情
    1、如果get请求，获取blogs_id，校验参数存在，转成int，默认渲染模板
    2、查询数据库，校验查询结果
    3、查询分类数据，Category
    4、遍历查询结果，确认博客分类属于当前分类，如果是cate_dict['is_selected'] = True
    5、移除'最新'的分类，category_dict_li.pop(0)
    6、返回模板admin/blogs_edit_detail.html，blogs，categories
    7、如果post请求，获取表单参数，blogs_id,title,digest,content,index_image,category_id
    8、判断参数完整性
    9、查询数据库，校验结果，确认博客的存在
    10、读取图片数据，调用七牛云接口上传图片，获取图片名称，拼接图片绝对路径
    11、保存数据到数据库，title、digest、content、category_id
    12、返回结果

    :return:
    """
    if request.method == 'GET':
        blogs_id = request.args.get('blogs_id')
        if not blogs_id:
            abort(404)
        try:
            blogs_id = int(blogs_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/blogs_edit_detail.html', errmsg='参数类型错误')
        try:
            blogs = Blogs.query.get(blogs_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/blogs_edit_detail.html', errmsg='查询数据错误')
        if not blogs:
            return render_template('admin/blogs_edit_detail.html', errmsg='未查询到数据')
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/blogs_edit_detail.html', errmsg='查询分类数据错误')
        category_dict_list = []
        # 遍历分类数据，需要判断当前遍历到的分类和博客所属分类一致
        for category in categories:
            cate_dict = category.to_dict()
            if category.id == blogs.category_id:
                cate_dict['is_selected'] = True
            category_dict_list.append(cate_dict)
        category_dict_list.pop(0)
        data = {
            'blogs': blogs.to_dict(),
            'categories': category_dict_list
        }
        return render_template('admin/blogs_edit_detail.html', data=data)
    blogs_id = request.form.get('blogs_id')
    title = request.form.get('title')
    digest = request.form.get('digest')
    content = request.form.get('content')
    index_image = request.files.get('index_image')
    category_id = request.form.get('category_id')

    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    try:
        blogs = Blogs.query.get(blogs_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')
    if not blogs:
        return jsonify(errno=RET.NODATA, errmsg='无博客数据')
    if index_image:
        image = index_image.read()
        try:
            image_name = ""
            # TODO img name
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')
        blogs.image_url = image_name
    blogs.title = title
    blogs.digest = digest
    blogs.content = content
    blogs.category_id = category_id

    try:
        db.session.add(blogs)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    return jsonify(errno=RET.OK, errmsg='OK')


@admin_blue.route('/blogs_type', methods=['GET', 'POST'])
def blogs_type():
    """
    博客分类
    1、如果get请求，查询分类数据，遍历查询结果，移除'最新'的分类
    2、返回模板admin/blogs_type.html,categories
    3、如果post请求，获取参数，name,id(表示编辑已存在的分类)
    4、校验name参数存在
    5、如果id存在(即修改已有的分类)，转成int，根据分类id查询数据库，校验查询结果，category.name = name
    6、实例化分类对象，保存分类名称，提交数据到数据库
    7、返回结果

    :return:
    """
    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/blogs_type.html', errmsg='查询数据错误')
        categories_dict_list = []
        for category in categories:
            categories_dict_list.append(category.to_dict())
        categories_dict_list.pop(0)
        data = {
            'categories': categories_dict_list
        }
        return render_template('admin/blogs_type.html', data=data)
    cname = request.json.get('name')
    cid = request.json.get('id')
    if not cname:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if cid:
        try:
            cid = int(cid)
            category = Category.query.get(cid)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询数据错误')
        if not category:
            return jsonify(errno=RET.NODATA, errmsg='未查询到分类数据')
        category.name = cname
    else:
        category = Category()
        category.name = cname
        db.session.add(category)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    return jsonify(errno=RET.OK, errmsg='OK')
