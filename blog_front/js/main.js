var vm = new Vue({
    el: '#article',
    data: {
        host: 'http://127.0.0.1:5000',
        message: '',
        datalist: [],
        page: 1,
        per_page: 5,
        pagecount: 0,
        cid: 1,
        ordertype: 1

    },
    mounted: function () {
        this.topage()
    },
    methods: {
        zuixin: function () {
            console.log('最新')
            this.page = 1
            this.ordertype = 1;
            this.topage()
        },
        zuire: function () {
            console.log('最热')
            this.page = 1
            this.ordertype = 2;
            this.topage()
        },
        topage: function () {
            // var params= {
            //     cid: this.cid,
            //     ordertype: this.ordertype,
            //     page: this.page,
            //     per_page: this.per_page,
            //     csrf_token: this.getCookie('csrf_token')
            // }
            // axios({
            //     method: 'post',
            //     url: this.host + '/api/list/',
            //     // data: JSON.stringify(params),
            //     data:params,
            //     // contentType: 'application/json',
            //     headers: {
            //         'X-CSRFToken': this.getCookie('csrf_token')
            //     }
            // })
            axios({
                method: 'get',
                url: this.host + '/api/list/',
                params: {
                    cid: this.cid,
                    ordertype: this.ordertype,
                    page: this.page,
                    per_page: this.per_page,
                }

            })
                .then(response => {
                    this.datalist = response.data.data.blogs_dict_list;
                    this.pagecount = response.data.data.total_page;
                    // this.page = response.data.data.current_page;

                })
                .catch(error => {
                    console.log(error.response.data)
                });
        },

        nextpage: function () {
            this.page += 1;
            this.topage()
        },
        lastpage: function () {
            this.page -= 1;
            this.topage()
        },
        tothepage: function (pageid) {
            this.page = pageid;
            this.topage()

        },
        getCookie: function (name) {
            var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
            return r ? r[1] : undefined;
        }


    }
});

var div1 = new Vue({
    el: '#div1',
    data: {
        host: 'http://127.0.0.1:5000',
        datalist: []

    },
    mounted: function () {
        axios({
            method: 'get',
            url: this.host + '/api/study_list/',
            params: {

            }

        }).then(response => {
            this.datalist = response.data.data;

        })
            .catch(error => {
                console.log(error.response.data)
            });
    },
    methods: {

    }

});

var div2 = new Vue({
    el: '#div2',
    data: {
        host: 'http://127.0.0.1:5000',
        datalist: []

    },
    mounted: function () {
        axios({
            method: 'get',
            url: this.host + '/api/friendlylink_list/',
            params: {

            }

        }).then(response => {
            this.datalist = response.data.data;

        })
            .catch(error => {
                console.log(error.response.data)
            });
    },
    methods: {

    }

});
