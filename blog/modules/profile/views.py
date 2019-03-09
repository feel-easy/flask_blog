from flask import g, redirect, render_template, request, jsonify, current_app, session

from . import profile_blue
from blog.utils.commons import login_required
from blog.utils.response_code import RET
from blog import db, constants

# 导入模型类
from blog.models import Category, Blogs, User


@profile_blue.route("/info")
@login_required
def user_info():
    """
    个人中心基本资料展示
    1、尝试获取用户信息
    user = g.user
    2、如果用户未登录，重定向到项目首页
    3、如果用户登录，获取用户信息
    4、把用户信息传给模板
    :return:
    """
    user = g.user
    if not user:
        return redirect('/')
    data = {
        'user': user.to_dict()
    }
    return render_template('blogs/user.html', data=data)


@profile_blue.route("/base_info", methods=['GET', 'POST'])
@login_required
def base_info():
    """
    基本资料的展示和修改
    1、尝试获取用户信息
    2、如果是get请求，返回用户信息给模板
    如果是post请求：
    1、获取参数，nick_name,signature,gender[MAN,WOMAN]
    2、检查参数的完整性
    3、检查gender性别必须在范围内
    4、保存用户信息
    5、提交数据
    6、修改redis缓存中的nick_name
    注册：session['nick_name'] = mobile
    登录：session['nick_name'] = user.nick_name
    修改：session['nick_name'] = nick_name

    7、返回结果


    :return:
    """
    user = g.user
    if request.method == 'GET':
        data = {
            'user': user.to_dict()
        }
        return render_template('blogs/user_base_info.html', data=data)
    # 获取参数
    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')
    # 检查参数
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 校验性别参数范围
    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数范围错误')
    # 保存用户信息
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    # 提交数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 修改redis缓存中的用户信息
    session['nick_name'] = nick_name
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')


@profile_blue.route("/pic_info", methods=['GET', 'POST'])
@login_required
def save_avatar():
    """
    保存用户头像
    获取用户信息，如果是get请求，user.to_dict()加载模板
    1、获取参数，
    avatar = request.files.get('avatar')
    文件对象：具有读写方法的对象
    2、检查参数
    3、读取文件对象
    4、调用七牛云，上传头像，保存七牛云返回的图片名称
    name = storage(images)
    5、保存用户头像数据，提交到mysql中是图片名称
    6、拼接图片的完整的绝对路径
    外链域名+图片名称：http://p8m0n4bb5.bkt.clouddn.com/图片名称
    7、返回结果

    :return:
    """
    user = g.user
    if request.method == 'GET':
        data = {
            'user': user.to_dict()
        }
        return render_template('blogs/user_pic_info.html', data=data)
    # 获取文件参数
    avatar = request.files.get('avatar')
    # 检查参数
    if not avatar:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 读取图片数据，转换成bytes类型
    try:
        image_data = avatar.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')
    try:
        image_name = ''
        # TODO  上传图片
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')
    # 保存图片文件的名称到mysql数据库中
    user.avatar_url = image_name
    # 提交数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 拼接图片的绝对路径，返回前端
    avatar_url = constants.QINIU_DOMIN_PREFIX + image_name
    data = {
        'avatar_url': avatar_url
    }
    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@profile_blue.route('/blogs_release', methods=['GET', 'POST'])
@login_required
def blogs_release():
    """
    博客发布：
    如果是get请求，加载博客分类，需要移除'最新'分类，传给模板
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if request.method == 'GET':
        try:
            category_list = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询博客分类数据失败')
        # 判断查询结果
        if not category_list:
            return jsonify(errno=RET.NODATA, errmsg='无博客分类数据')
        categories = []
        for category in category_list:
            categories.append(category.to_dict())
        # 移除最新
        categories.pop(0)
        data = {
            'categories': categories
        }
        return render_template('blogs/user_blogs_release.html', data=data)

    # 如果不是get请求，获取参数,title,category_id,digest,index_image,content
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    digest = request.form.get('digest')
    index_image = request.files.get('index_image')
    content = request.form.get('content')
    # 检查参数的完整性
    if not all([title, category_id, digest, index_image, content]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 转换博客分类数据类型
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数类型错误')
    # 读取图片数据
    try:
        image_data = index_image.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')

    try:
        # TODO 上传图片 image_name 返回的文件名
        image_name = ""
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')
    # 保存博客数据
    blogs = Blogs()
    blogs.category_id = category_id
    blogs.user_id = user.id
    blogs.source = '个人发布'
    blogs.title = title
    blogs.digest = digest

    # blogs.index_image_url = index_image
    # 博客图片应该存储的是图片的绝对路径,让博客图片和博客内容是一个整体。
    blogs.index_image_url = image_name
    blogs.content = content
    blogs.status = 1
    # 提交数据
    try:
        db.session.add(blogs)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')


@profile_blue.route('/blog_release', methods=['GET', 'POST'])
def blog_release():
    """
    博客发布：
    如果是get请求，加载博客分类，需要移除'最新'分类，传给模板
    :return:
    """
    if request.method == 'GET':
        try:
            category_list = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询博客分类数据失败')
        # 判断查询结果
        if not category_list:
            return jsonify(errno=RET.NODATA, errmsg='无博客分类数据')
        categories = []
        for category in category_list:
            categories.append(category.to_dict())
        # 移除最新
        categories.pop(0)
        data = {
            'categories': categories
        }
        # return render_template('blogs/user_blogs_release.html', data=data)
        return jsonify(data)

    # 如果不是get请求，获取参数,title,category_id,digest,index_image,content
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    digest = request.form.get('digest')
    # index_image = request.files.get('index_image')
    content = request.form.get('content')
    # 检查参数的完整性
    if not all([title, category_id, digest, content]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 转换博客分类数据类型
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数类型错误')
    # 读取图片数据
    try:
        # image_data = index_image.read()
        pass
        # TODO 图片
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')

    try:
        # TODO 上传图片 image_name 返回的文件名
        image_name = ""
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')
    # 保存博客数据
    blogs = Blogs()
    blogs.category_id = category_id
    blogs.user_id = 1
    blogs.source = '个人发布'
    blogs.title = title
    blogs.digest = digest

    # blogs.index_image_url = index_image
    # 博客图片应该存储的是图片的绝对路径,让博客图片和博客内容是一个整体。
    blogs.index_image_url = image_name
    blogs.content = content
    blogs.status = 1
    # 提交数据
    try:
        db.session.add(blogs)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')


@profile_blue.route("/pass_info", methods=['GET', 'POST'])
@login_required
def pass_info():
    """
    个人中心：修改密码
    1、判断请求方法，如果get请求，默认渲染模板页面
    2、获取参数，old_password,new_password
    3、检查参数的完整性
    4、获取用户信息，用来对旧密码进行校验是否正确
    5、更新用户新密码
    6、返回结果
    :return:
    """
    # 如果是get请求,默认渲染模板页面
    if request.method == 'GET':
        return render_template('blogs/user_pass_info.html')
    # 获取参数
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    # 检查参数的完整性
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 获取用户的登录信息
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    # 校验密码是否正确
    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg='旧密码错误')
    # 如果旧密码正确，更新新密码到数据库
    user.password = new_password
    # 提交数据到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')


@profile_blue.route('/collection')
@login_required
def user_collection():
    """
    用户收藏
    1、获取参数，页数p，默认1
    2、判断参数，整型
    3、获取用户信息，定义容器存储查询结果，总页数默认1，当前页默认1
    4、查询数据库，从用户收藏的的博客中进行分页，user.collection_blogs
    5、获取总页数、当前页、博客数据
    6、定义字典列表，遍历查询结果，添加到列表中
    7、返回模板blogs/user_collection.html,'total_page',current_page,'collections'

    :return:
    """
    page = request.args.get('p', '1')
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    user = g.user
    blogs_list = []
    total_page = 1
    current_page = 1
    try:
        paginate = user.collection_blogs.paginate(page, constants.USER_COLLECTION_MAX_BLOGS, False)
        current_page = paginate.page
        total_page = paginate.pages
        blogs_list = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    blogs_dict_list = []
    for blogs in blogs_list:
        blogs_dict_list.append(blogs.to_basic_dict())
    data = {
        'collections': blogs_dict_list,
        'total_page': total_page,
        'current_page': current_page
    }

    return render_template('blogs/user_collection.html', data=data)


@profile_blue.route('/blogs_list')
@login_required
def user_blogs_list():
    """
    用户博客列表
    1、获取参数，页数p，默认1
    2、判断参数，整型
    3、获取用户信息，定义容器存储查询结果，总页数默认1，当前页默认1
    4、查询数据库，查询博客数据并进行分页，
    5、获取总页数、当前页、博客数据
    6、定义字典列表，遍历查询结果，添加到列表中
    7、返回模板blogs/user_blogs_list.html 'total_page',current_page,'blogs_dict_list'

    :return:
    """
    page = request.args.get('p', '1')
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    user = g.user
    blogs_list = []
    total_page = 1
    current_page = 1
    try:
        paginate = Blogs.query.filter(Blogs.user_id == user.id).paginate(page, constants.USER_COLLECTION_MAX_BLOGS,
                                                                         False)
        blogs_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')
    blogs_dict_list = []
    for blogs in blogs_list:
        blogs_dict_list.append(blogs.to_review_dict())
    data = {
        'blogs_list': blogs_dict_list,
        'total_page': total_page,
        'current_page': current_page
    }
    return render_template('blogs/user_blogs_list.html', data=data)


@profile_blue.route('/user_follow')
@login_required
def user_follow():
    """
    用户关注
    1、获取参数，页数p，默认1
    2、判断参数，整型
    3、获取用户信息，定义容器存储查询结果，总页数默认1，当前页默认1
    4、查询数据库，查询博客数据并进行分页，user.followed.paginate
    5、获取总页数、当前页、博客数据
    6、定义字典列表，遍历查询结果，添加到列表中
    7、返回模板blogs/user_follow.html, 'total_page',current_page,'users'

    :return:
    """
    page = request.args.get('p', '1')
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    user = g.user
    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
        current_page = paginate.page
        total_page = paginate.pages
        follows = paginate.items
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')
    user_follow_list = []
    for follow in follows:
        user_follow_list.append(follow.to_dict())
    data = {
        'users': user_follow_list,
        'current_page': current_page,
        'total_page': total_page
    }
    return render_template('blogs/user_follow.html', data=data)


@profile_blue.route('/other_info')
@login_required
def other_info():
    """
    查询用户关注的其他用户信息
    1、获取用户登录信息
    2、获取参数，user_id
    3、校验参数，如果不存在404
    4、如果博客有作者,并且登录用户关注过作者，is_followed = False
    5、返回模板blogs/other.html，is_followed,user,other_info
    :return:
    """
    user = g.user
    other_id = request.args.get('id')
    if not other_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')
    if not other:
        return jsonify(errno=RET.NODATA, errmsg='无数据')
    is_follwed = False
    if other and user:
        if other in user.followed:
            is_follwed = True
    data = {
        'is_followed': is_follwed,
        'user': user.to_dict() if user else None,
        'other_info': other.to_dict()
    }
    return render_template('blogs/other.html', data=data)


@profile_blue.route('/other_blogs_list')
@login_required
def other_blogs_list():
    """
    返回指定用户发布的博客
    1、获取参数，user_id，p默认1
    2、页数转成整型
    3、根据user_id查询用户表，判断查询结果
    4、如果用户存在，分页用户发布的博客数据，other.blogs_list.paginate()
    5、获取分页数据，总页数、当前页
    6、遍历数据，转成字典
    7、返回结果，blogs_list,total_page,current_page
    :return:
    """
    user_id = request.args.get('user_id')
    page = request.args.get('p', '1')
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库错误')
    if not other:
        return jsonify(errno=RET.NODATA, errmsg='用户不存在')
    try:
        paginate = other.blogs_list.paginate(page, constants.USER_COLLECTION_MAX_BLOGS, False)
        blogs_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')
    blogs_dict_list = []
    for blogs in blogs_list:
        blogs_dict_list.append(blogs.to_basic_dict())
    data = {
        'blogs_list': blogs_dict_list,
        'total_page': total_page,
        'current_page': current_page
    }
    return jsonify(errno=RET.OK, errmsg='OK', data=data)
