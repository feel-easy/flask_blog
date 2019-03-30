function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function(){
    $(".blogs_add").submit(function (e) {
        e.preventDefault()
        // 博客添加提交
        var params = {}
        $(this).serializeArray().map(function(x){
            params[x.name] = x.value
        })
//        alert(JSON.stringify(params))
        $.ajax({
            url:"/admin/blogs_add_action",
            type:"post",
            contentType:"application/json",
            data:JSON.stringify(params),
            headers:{
                'X-CSRFToken':getCookie('csrf_token')
            },
            success:function(resp){
                if (resp.errno == "0"){
                    alert('添加成功')
//                    window.location.reload()
                       window.location.href="/admin/blogs_review"
                }else{
                    alert(resp.errmsg)
                }
            }
        })
    })
})

// 点击取消，返回上一页
function cancel() {
    history.go(-1)
}