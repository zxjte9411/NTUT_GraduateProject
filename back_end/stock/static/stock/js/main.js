$(() => {
    function update_view() {
        $.ajaxSetup({
            url: "/withdraw",
            type: 'POST',
            global: false,
            dataType: 'json',
        })

        $.ajax({
            data: {
                csrfmiddlewaretoken: $("*[name='csrfmiddlewaretoken']").val(),
                money: $("#select_2").val(),
                stock_num: $("#select_1").val()
            },

            success: function (data) {
                if (data.status == 1) {
                    result_table = $("#dataTable")
                    result_table.html("")
                    let thead = "<thead><tr><th>指標</th><th>獲利率</th></tr></thead>"
                    let tbody = $("<tbody></tbody>")
                    $.each(data.pointers, function (_index, element) {
                        // console.log(element.pointer)
                        // console.log(element.value)
                        tbody.append("<tr><th>" + element.pointer + "</th><th>"+element.value+"</th></tr>")
                    })
                    result_table.append(thead)
                    result_table.append(tbody)
                    // 第一次發 POST 會改變 table 的顯示
                    $("#result").show()
                }
            },

            error: function (XMLHttpRequest, _ajaxOptions, _errorThrown) {
                console.log(XMLHttpRequest.status)
                // console.log(errorThrown)
            }
        })
    }

    $("#button_submit").click(function () {
        update_view()
    })
})