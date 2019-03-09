from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from blog import constants
from . import db


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""
    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录的创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录的更新时间


# 用户收藏表，建立用户与其收藏博客多对多的关系
tb_user_collection = db.Table(
    "blog_user_collection",
    db.Column("user_id", db.Integer, db.ForeignKey("blog_user.id"), primary_key=True),  # 新闻编号
    db.Column("blogs_id", db.Integer, db.ForeignKey("blog_blogs.id"), primary_key=True),  # 分类编号
    db.Column("create_time", db.DateTime, default=datetime.now)  # 收藏创建时间
)

tb_user_follows = db.Table(
    "blog_user_fans",
    db.Column('follower_id', db.Integer, db.ForeignKey('blog_user.id'), primary_key=True),  # 粉丝id
    db.Column('followed_id', db.Integer, db.ForeignKey('blog_user.id'), primary_key=True)  # 被关注人的id
)

class User(BaseModel, db.Model):
    """用户"""
    __tablename__ = "blog_user"
    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    nick_name = db.Column(db.String(32), unique=True, nullable=False)  # 用户昵称
    password_hash = db.Column(db.String(128), nullable=False)  # 加密的密码
    mobile = db.Column(db.String(11), unique=True, nullable=False)  # 手机号
    avatar_url = db.Column(db.String(256))  # 用户头像路径
    last_login = db.Column(db.DateTime, default=datetime.now)  # 最后一次登录时间
    is_admin = db.Column(db.Boolean, default=False)
    signature = db.Column(db.String(512))  # 用户签名
    gender = db.Column(  # 订单的状态
        db.Enum(
            "MAN",  # 男
            "WOMAN"  # 女
        ),
        default="MAN")
    # 当前用户收藏的所有博客
    collection_news = db.relationship("Blogs", secondary=tb_user_collection, lazy="dynamic")  # 用户收藏的博客
    # 用户所有的粉丝，添加了反向引用followed，代表用户都关注了哪些人
    followers = db.relationship('User',
                                secondary=tb_user_follows,
                                primaryjoin=id == tb_user_follows.c.followed_id,
                                secondaryjoin=id == tb_user_follows.c.follower_id,
                                backref=db.backref('followed', lazy='dynamic'),
                                lazy='dynamic')

    blog_list = db.relationship('Blogs', backref='user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError("当前属性不可读")

    @password.setter
    def password(self, value):
        self.password_hash = generate_password_hash(value)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "avatar_url": self.avatar_url if self.avatar_url else "",
            "mobile": self.mobile,
            "gender": self.gender if self.gender else "MAN",
            "signature": self.signature if self.signature else "",
            "followers_count": self.followers.count(),
            "blogs_count": self.blog_list.count()
        }
        return resp_dict

    def to_admin_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "mobile": self.mobile,
            "register": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return resp_dict


class Blogs(BaseModel, db.Model):
    """博客"""
    __tablename__ = "blog_blogs"
    id = db.Column(db.Integer, primary_key=True)  # 博客编号
    title = db.Column(db.String(256), nullable=False)  # 博客标题
    source = db.Column(db.String(64), nullable=False)  # 博客来源
    digest = db.Column(db.String(512), nullable=False)  # 博客摘要
    content = db.Column(db.Text, nullable=False)  # 博客内容
    content_url = db.Column(db.String(64), nullable=False)  # 博客详情页url
    clicks = db.Column(db.Integer, default=0)  # 浏览量
    index_image_url = db.Column(db.String(256))  # 博客列表图片路径
    category_id = db.Column(db.Integer, db.ForeignKey("blog_category.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("blog_user.id"))  # 当前博客的作者id
    status = db.Column(db.Integer, default=0)  # 当前博客状态 如果为0代表审核通过，1代表审核中，-1代表审核不通过
    reason = db.Column(db.String(256))  # 未通过原因，status = -1 的时候使用
    # 当前博客的所有评论
    comments = db.relationship("Comment", lazy="dynamic")

    def to_review_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "reason": self.reason if self.reason else ""
        }
        return resp_dict

    def to_basic_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "digest": self.digest,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "index_image_url": self.index_image_url,
            "clicks": self.clicks,
        }
        return resp_dict

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "digest": self.digest,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": self.content,
            "comments_count": self.comments.count(),
            "clicks": self.clicks,
            "category": self.category.to_dict(),
            "index_image_url": self.index_image_url,
            'content_url':self.content_url,
            "author": self.user.to_dict() if self.user else None
        }
        return resp_dict


class Comment(BaseModel, db.Model):
    """评论"""
    __tablename__ = "blog_comment"
    id = db.Column(db.Integer, primary_key=True)  # 评论编号
    user_id = db.Column(db.Integer, db.ForeignKey("blog_user.id"), nullable=False)  # 用户id
    blog_id = db.Column(db.Integer, db.ForeignKey("blog_blogs.id"), nullable=False)  # 博客id
    content = db.Column(db.Text, nullable=False)  # 评论内容
    parent_id = db.Column(db.Integer, db.ForeignKey("blog_comment.id"))  # 父评论id
    parent = db.relationship("Comment", remote_side=[id])  # 自关联
    like_count = db.Column(db.Integer, default=0)  # 点赞条数

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": self.content,
            "parent": self.parent.to_dict() if self.parent else None,
            "user": User.query.get(self.user_id).to_dict(),
            "blogs_id": self.blogs_id,
            "like_count": self.like_count
        }
        return resp_dict


class CommentLike(BaseModel, db.Model):
    """评论点赞"""
    __tablename__ = "blog_comment_like"
    comment_id = db.Column("comment_id", db.Integer, db.ForeignKey("blog_comment.id"), primary_key=True)  # 评论编号
    user_id = db.Column("user_id", db.Integer, db.ForeignKey("blog_blogs.id"), primary_key=True)  # 用户编号


class Category(BaseModel, db.Model):
    """博客分类"""
    __tablename__ = "blog_category"
    id = db.Column(db.Integer, primary_key=True)  # 分类编号
    name = db.Column(db.String(64), nullable=False)  # 分类名
    blog_list = db.relationship('Blogs', backref='category', lazy='dynamic')

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "name": self.name
        }
        return resp_dict


class Image(BaseModel, db.Model):
    __tablename__ = "blog_image"
    id = db.Column(db.Integer, primary_key=True)  # 图片编号
    img_url = db.Column(db.String(256), nullable=True)  # 图片的url
