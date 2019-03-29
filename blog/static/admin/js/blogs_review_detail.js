function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function(){
    $(".blogs_review").submit(function (e) {
        e.preventDefault()

        // 博客审核提交
        var params = {}
        $(this).serializeArray().map(function(x){
            params[x.name] = x.value
        })

        $.ajax({
            url:"/admin/blogs_review_action",
            type:"post",
            contentType:"application/json",
            data:JSON.stringify(params),
            headers:{
                'X-CSRFToken':getCookie('csrf_token')
            },
            success:function(resp){
                if (resp.errno == "0"){
                    alert('审核提交成功')
                    window.location.reload()
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