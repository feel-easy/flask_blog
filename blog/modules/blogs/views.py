# 使用蓝图对象
import datetime

from dateutil.relativedelta import relativedelta
from flask import session, render_template, current_app, jsonify, request, g

from blog import constants, db
from blog.models import User, Category, Blogs, CommentLike, Comment
from blog.utils.commons import login_required
from blog.utils.response_code import RET
from . import blog_blue

import hashlib
from werkzeug.security import generate_password_hash, check_password_hash


# 首页模板数据加载
@blog_blue.route('/')
@login_required
def index():
    """
    首页：
        右上角用户信息展示：检查用户登录状态
    :return:
    """
    user = g.user

    # 博客分类数据展示
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询博客分类数据失败')
    # 判断查询结果
    if not categories:
        return jsonify(errno=RET.NODATA, errmsg='无博客分类数据')
    category_list = []
    # 遍历查询博客分类结果,存入列表
    for category in categories:
        category_list.append(category.to_dict())

    # 博客点击排行
    try:
        blogs_list = Blogs.query.order_by(Blogs.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询博客排行数据失败')
    if not blogs_list:
        return jsonify(errno=RET.NODATA, errmsg='无博客排行数据')
    blogs_click_list = []
    for blog in blogs_list:
        blogs_click_list.append(blog.to_dict())

    data = {
        'user_info': user.to_dict() if user else None,
        'category_list': category_list,
        'blogs_click_list': blogs_click_list
    }

    # return render_template('news/index.html', data=data)
    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@blog_blue.route('/blogs_list')
def get_blogs_list():
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
    cid = request.args.get('cid', '1')
    page = request.args.get('page', '1')
    per_page = request.args.get('per_page', '10')
    # 转换参数的数据类型
    try:
        cid, page, per_page = int(cid), int(page), int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')
    # 定义容器，存储查询的过滤条件
    filters = []
    # 判断分类id如果不是最新
    if cid > 1:
        filters.append(Blogs.category_id == cid)
    # 使用过滤条件查询mysql，按照博客发布时间排序
    print(filters)
    try:
        # *filters表示python中拆包，News.category_id==cid，*filters里面存储的是sqlalchemy对象
        # 在python中测试添加的数据为True或False
        paginate = Blogs.query.filter(*filters).order_by(Blogs.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询博客数据失败')
    # 获取分页后的数据
    news_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page
    # 定义容器，存储查询到的博客数据
    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_dict())
    data = {
        'news_dict_list': news_dict_list,
        'total_page': total_page,
        'current_page': current_page
    }
    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@blog_blue.route('/list/', methods=['GET'])
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
    filters = []
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


@blog_blue.route('/list/archives/')
def getBlogsArchivesList():
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

    # 转换参数的数据类型

    # 定义容器，存储查询的过滤条件
    filters = []
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
    lasttime = firstblogtime.combine(lastblogtime.replace(day=1).replace(month=lastblogtime.month+1).date(),
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


@blog_blue.route('/<int:blogs_id>')
@login_required
def get_blogs_detail(blogs_id):
    """
    博客详情
        用户数据展示
        点击排行展示
        博客数据展示
    :param blogs_id:
    :return:
    """
    # 从登录验证装饰器中获取用户信息
    user = g.user
    # 博客点击排行
    try:
        news_list = Blogs.query.order_by(Blogs.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询博客排行数据失败')
    if not news_list:
        return jsonify(errno=RET.NODATA, errmsg='无博客排行数据')
    news_click_list = []
    for news in news_list:
        news_click_list.append(news.to_dict())

    # 博客详情数据
    try:
        news = Blogs.query.get(blogs_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询博客详情数据失败')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='无博客详情数据')
    # 收藏或取消收藏的标记
    is_collected = False
    # 判断用户是否收藏过,用户登录后才能显示该博客是否收藏
    if user and news in g.user.collection_news:
        is_collected = True

    # 博客评论信息展示
    try:
        comments = Comment.query.filter(Comment.blog_id == blogs_id).filter(Comment.parent_id != None).order_by(
            Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询评论信息失败')
    # 评论点赞id
    comment_like_ids = []
    # 获取当前登录用户的所有评论的id，
    if user:
        try:
            comment_ids = [comment.id for comment in comments]
            # 再查询点赞了哪些评论
            comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                     CommentLike.user_id == g.user.id).all()
            # 遍历点赞的评论数据
            comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
        except Exception as e:
            current_app.logger.error(e)
    comment_dict_list = []
    for comment in comments:
        comment_dict = comment.to_dict()
        # 如果未点赞
        comment_dict['is_like'] = False
        # 如果点赞
        if comment.id in comment_like_ids:
            comment_dict['is_like'] = True
        comment_dict_list.append(comment_dict)

    data = {
        'user_info': user.to_dict() if user else None,
        'news_click_list': news_click_list,
        'news_detail': news.to_dict(),
        'is_collected': is_collected,
        "comments": comment_dict_list
    }

    # return render_template('news/detail.html', data=data)
    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@blog_blue.route("/blogs_collect", methods=['POST'])
@login_required
def blogs_collect():
    """
    博客收藏和取消收藏
    1、获取参数，news_id,action[collect,cancel_collect]
    2、检查参数的完整性
    3、转换news_id参数的数据类型
    4、检查action参数的范围
    5、查询mysql确认博客的存在
    6、校验查询结果
    7、判断用户选择的是收藏，还要判断用户之前未收藏过
    user.collection_news.append(news)
    如果是取消收藏
    user.collection_news.remove(news)
    8、提交数据mysql
    9、返回结果


    :return:
    """
    # 从登录验证装饰器中获取用户信息
    user = g.user
    # 判断用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    blogs_id = request.json.get('blogs_id')
    action = request.json.get('action')
    # 检查参数的完整性
    if not all([blogs_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 转换newsid数据类型
    try:
        blogs_id = int(blogs_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数类型错误')
    # 检查action参数的范围
    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数范围错误')
    # 根据博客id查询数据
    try:
        news = Blogs.query.get(blogs_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')
    # 判断查询结果
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='无博客数据')
    # 如果用户选择的是收藏
    if action == 'collect':
        # 该博客用户之前未收藏
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    # 提交数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')


@blog_blue.route("/blogs_comment", methods=['POST'])
@login_required
def blogs_comment():
    """
    博客评论
    1、尝试获取用户信息，如果用户未登录，直接结束程序
    2、获取参数，news_id,comment,parent_id
    3、检查参数的完整性，news_id,comment
    4、把news_id转换数据类型，如果parent_id存在
    5、查询数据库，确认博客的存在
    6、保存评论信息
    coments = Comment()
    7、提交数据到数据库
    8、返回结果

    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    # 获取参数
    blogs_id = request.json.get('blogs_id')
    content = request.json.get('comment')
    parent_id = request.json.get('parent_id')
    # 检查参数的完整性
    if not all([blogs_id, content]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 转换参数的数据类型
    try:
        blogs_id = int(blogs_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数类型错误')
    # 查询数据库，确认博客的存在
    try:
        news = Blogs.query.get(blogs_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询博客数据失败')
    # 判断查询结果
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='博客不存在')
    # 构造模型类对象，存储评论信息
    comments = Comment()
    comments.user_id = user.id
    comments.news_id = blogs_id
    comments.content = content
    if parent_id:
        comments.parent_id = parent_id
    try:
        db.session.add(comments)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg="OK", data=comments.to_dict())


@blog_blue.route('/comment_like', methods=['POST'])
@login_required
def comment_like():
    """
    点赞或取消点赞
    1、获取用户登录信息
    2、获取参数，comment_id,action
    3、检查参数的完整性
    4、判断action是否为add，remove
    5、把comment_id转成整型
    6、根据comment_id查询数据库
    7、判断查询结果
    8、判断行为是点赞还是取消点赞
    9、如果为点赞，查询改评论，点赞次数加1，否则减1
    10、提交数据
    11、返回结果

    :return:
    """
    user = g.user
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    if action not in ['add', 'remove']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='参数错误')
    try:
        comments = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    if not comments:
        return jsonify(errno=RET.NODATA, errmsg='评论不存在')
    # 如果选择的是点赞
    if action == 'add':
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment_id).first()
        # 判断查询结果，如果没有点赞过
        if not comment_like_model:
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment_id
            # 把数据提交给数据库会话对象，点赞次数加1
            db.session.add(comment_like_model)
            comments.like_count += 1
    # 如果取消点赞
    else:
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment_id).first()
        if comment_like_model:
            db.session.delete(comment_like_model)
            comments.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    return jsonify(errno=RET.OK, errmsg='OK')


@blog_blue.route('/followed_user', methods=['POST'])
@login_required
def followed_user():
    """
    关注与取消关注
    1、获取用户信息,如果未登录直接返回
    2、获取参数，user_id和action
    3、检查参数的完整性
    4、校验参数，action是否为followed，unfollow
    5、根据用户id获取被关注的用户
    6、判断获取结果
    7、根据对应的action执行操作，关注或取消关注
    8、返回结果
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    user_id = request.json.get('user_id')
    action = request.json.get('action')
    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    if action not in ['follow', 'unfollow']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')
    if not other:
        return jsonify(errno=RET.NODATA, errmsg='无用户数据')
    # 如果选择关注
    if action == 'follow':
        if other not in user.followed:
            user.followed.append(other)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg='当前用户已被关注')
    # 取消关注
    else:
        if other in user.followed:
            user.followed.remove(other)

    return jsonify(errno=RET.OK, errmsg='OK')
