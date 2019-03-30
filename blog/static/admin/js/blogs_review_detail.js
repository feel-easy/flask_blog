new Vue({
    el: '#blogs_review',
    data: {
        input: '# hello'
    },
    computed: {
        compiledMarkdown: function () {
            return marked(this.input, { sanitize: true })
        }

    },
    mounted: function () {
        var $radio = $('input[name="action"]');
        $radio.click(function () {
            if ($(this).index() == 1) {
                $('.group_hide').show();
            }
            else {
                $('.group_hide').hide();
            }
        });
        this.input = $('#data').text()
        $('#data').text('')

    },
    methods: {
        update: _.debounce(function (e) {
            this.input = e.target.value
        }, 300),
        submittable: function () {
            $(".blogs_review").submit(function (e) {
                e.preventDefault()

                // 博客审核提交
                var params = {}
                $(this).serializeArray().map(function (x) {
                    params[x.name] = x.value
                })
                function getCookie(name) {
                    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
                    return r ? r[1] : undefined;
                }

                $.ajax({
                    url: "/admin/blogs_review_action",
                    type: "post",
                    contentType: "application/json",
                    data: JSON.stringify(params),
                    headers: {
                        'X-CSRFToken': getCookie('csrf_token')
                    },
                    success: function (resp) {
                        if (resp.errno == "0") {
                            alert('审核提交成功')
                            //                    window.location.reload()
                            window.location.href = "/admin/blogs_review"
                        } else {
                            alert(resp.errmsg)
                        }
                    }
                })


            })
        },
        cancel: function () {
            history.go(-1)
        },
        
    }
})
