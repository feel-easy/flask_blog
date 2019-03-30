from flask import request, jsonify, current_app, make_response, session

from . import passport_blue
# 导入自定义的状态码
from blog.utils.response_code import RET
# 导入生成图片验证码的工具
from blog.utils.captcha.captcha import captcha
# 导入redis实例,常量文件
from blog import redis_store, constants, db
# 导入正则
import re, random

# 导入模型类User
from blog.models import User
# 导入日期模块
from datetime import datetime

"""
生成图片验证码
发送短信
注册
登录
退出

"""


@passport_blue.route("/image_code")
def generate_image_code():
    """
    生成图片验证码
    uuid：全局唯一的标识符，redis.setex('ImageCode_' + uuid )
    1、获取前端生成的uuid
    request.args.get("image_code_id")
    2、判断参数是否存在，如果不存在直接return
    3、使用工具captcha生成图片验证码,name,test,images
    4、保存图片验证码的text文本，redis数据库中
    5、返回图片

    :return:
    """
    # 获取前端传入的图片验证码的编号uuid
    image_code_id = request.args.get('image_code_id')
    # 判断参数是否存在
    if not image_code_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 调用captcha工具，生成图片验证码
    name, text, image = captcha.generate_captcha()
    # 保存图片验证码的文本到redis数据库中
    try:
        redis_store.setex('ImageCode_' + image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据异常')
    else:
        response = make_response(image)
        # 修改默认的响应类型，test/html,
        response.headers['Content-Type'] = 'images/jpg'
        return response


@passport_blue.route("/sms_code", methods=['POST'])
def send_sms_code():
    """
    发送短信：web开发：写接口、调接口
    获取参数----检查参数----业务处理----返回结果
    1、获取参数mobile，image_code,image_code_id
    2、检查参数的完整性
    3、检查手机号的格式，正则
    4、尝试从redis中获取真实的图片验证码
    image_code = redis_store.get(imagecode)
    5、判断获取结果，如果不存在，说明图片验证码已过期
    6、删除redis中存储的图片验证码，因为图片验证码无论正确与否，只能比较一次，
    7、比较图片验证码是否正确
    8、构造短信随机码，6位数
    9、使用云通讯发送短信，保存发送结果
    10、返回结果
    :return:
    """
    # 获取参数
    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')
    # 检查参数的完整性
    # if mobile and image_code and image_code_id:
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 使用正则校验手机号格式
    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    # 手机号是否注册可以

    # 获取redis中存储的真实图片验证码
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')
    # 判断获取结果
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已过期')
    # 删除redis中的图片验证码
    try:
        redis_store.delete('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
    # 比较图片验证码是否一致,忽略大小写
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码不一致')
    # 判断手机号是否已注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户数据失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')

    # 构造六位数的短信随机数
    sms_code = '%06d' % random.randint(0, 999999)
    print(sms_code)
    # 存入到redis数据库中
    try:
        redis_store.setex('SMSCode_' + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据异常')
    # 使用云通讯发送短信
    try:
        # ccp = sms.CCP()
        # TODO 发送验证码
        # results = ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
        results = 0
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='发送短信异常')
    # 判断发送结果
    if results == 0:
        return jsonify(errno=RET.OK, errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送失败')


@passport_blue.route('/register', methods=['POST'])
def register():
    """
    用户注册
    1、获取参数，mobile，sms_code,password
    2、检查参数完整性
    3、检查手机号的格式
    4、尝试从redis中获取真实的短信验证码
    5、判断获取结果是否存在
    6、先比较短信验证码是否正确
    7、删除redis中存储的短信验证码
    8、构造模型类对象，存储用户信息
    9、提交数据到数据库中
    10、缓存用户信息到redis数据库中
    11、返回结果
    :return:
    """
    # 获取参数
    mobile = request.json.get('mobile')
    sms_code = request.json.get('sms_code')
    password = request.json.get('password')
    # 检查参数的完整性
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 使用正则校验手机号格式
    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    # 从redis中获取真实的短信验证码
    try:
        real_sms_code = redis_store.get('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')
    # 判断获取结果是否存在
    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg='数据已过期')
    # 比较短信验证码是否一致
    # if real_sms_code != str(sms_code):
    #     return jsonify(errno=RET.DATAERR,errmsg='短信验证码不一致')
    # 删除短信验证码
    try:
        redis_store.delete('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
    # 判断手机号是否已注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户数据失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')
    # 保存用户信息
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    # 实际上调用了模型类中的password方法，实现了密码加密存储，generate_password_hash
    user.password = password
    # 提交数据到mysql
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 缓存用户信息
    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name'] = mobile
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')


@passport_blue.route('/login', methods=['POST'])
def login():
    """
    登录
    获取参数----检查参数----业务处理----返回结果
    1、获取参数，mobile，password
    2、检查参数的完整性
    3、检查手机号格式，可选
    4、根据手机号查询用户是否已注册
    user = User.query.filter_by(mobile=mobile).first()
    5、判断查询结果
    6、判断密码是否正确
    7、缓存用户信息
    注册时缓存：session['nick_name'] = mobile
    登录时缓存：session['nick_name'] = user.nick_name
    8、返回结果
    :return:
    """
    # 获取参数
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    # 检查参数的完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 检查手机号的格式
    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')
    # 根据手机号查询mysql，确认用户已注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户数据失败')

    # 建议使用这种判断
    if user is None or not user.check_password(password):
        return jsonify(errno=RET.DATAERR, errmsg='用户名或密码错误')
    # 记录用户的登录时间
    user.last_login = datetime.now()
    # 提交数据到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 缓存用户信息
    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name'] = user.nick_name
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')


@passport_blue.route('/logout')
def logout():
    """退出登录"""
    # 本质是清除用户在服务器缓存的用户信息
    session.pop('user_id', None)
    session.pop('mobile', None)
    session.pop('nick_name', None)
    # 添加管理员退出
    session.pop('is_admin', None)
    return jsonify(errno=RET.OK, errmsg='OK')

    pass
