$(() => {
    function update_view_of_detail(action_url) {
        $.ajaxSetup({
            url: action_url,
            type: 'POST',
            global: false,
            dataType: 'json',
        })

        $.ajax({
            data: {
                csrfmiddlewaretoken: $("*[name='csrfmiddlewaretoken']").val(),
                money: $("#money").val(),
                stock_num: $("#stock_num").val()
            },
            success: function (data) {
                let tptype = $("#tptype").val()
                if (data.status == 1) {
                    result_table = $("#dataTable")
                    let tbody
                    if ($("#dataTable tbody").length === 0) {
                        tbody = $("<tbody></tbody>")
                    }
                    else {
                        tbody = $("#dataTable tbody")
                    }
                    tbody.html("")
                    data.details[tptype].forEach(element => {
                        tbody.append("<tr><th>" + element.date + "</th><th>" + element.close + "</th><th>" + element.type + "</tr>")
                    })
                    result_table.append(tbody)
                    // 第一次發 POST 會改變 table 的顯示
                    $("#result").show()
                }
            },
            error: function (XMLHttpRequest, _ajaxOptions, _errorThrown) {
                console.log(XMLHttpRequest.status)
            }

        })
    }
    function update_view_of_withdraw(action_url) {
        $.ajaxSetup({
            url: action_url,
            type: 'POST',
            global: false,
            dataType: 'json',
        })

        $.ajax({
            data: {
                csrfmiddlewaretoken: $("*[name='csrfmiddlewaretoken']").val(),
                money: $("#money").val(),
                stock_num: $("#stock_num").val()
            },
            success: function (data) {
                if (data.status == 1) {
                    result_table = $("#dataTable")
                    let tbody
                    if ($("#dataTable tbody").length === 0) {
                        tbody = $("<tbody></tbody>")
                    }
                    else {
                        tbody = $("#dataTable tbody")
                    }
                    tbody.html("")
                    $.each(data.pointers, function (_index, element) {
                        tbody.append("<tr><th>" + element.pointer + "</th><th>" + element.value + "</th></tr>")
                    })
                    result_table.append(tbody)
                    // 第一次發 POST 會改變 table 的顯示
                    $("#result").show()
                    $("#return_money").val($("#money").val())
                    $("#return_stock_num").val($("#stock_num").val())
                }
            },
            error: function (XMLHttpRequest, _ajaxOptions, _errorThrown) {
                console.log(XMLHttpRequest.status)
            }
        })
    }

    $("#button_submit_withdraw").click(function () {
        update_view_of_withdraw("/withdraw")
    })
    $("#button_submit_detail").click(function () {
        update_view_of_detail("/withdraw/detail")
    })
})