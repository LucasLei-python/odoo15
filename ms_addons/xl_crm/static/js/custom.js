//initiating jQuery
jQuery(function ($) {



    $(document).ready(function () {

        //datetimepicker jQuery
        $("#DeliveryDate").datetimepicker({
            language: "zh-CN",
            format: "yyyy-mm-dd",
            pickerPosition: "bottom-left",
            weekStart: 1,
            todayBtn: 1,
            autoclose: 1,
            todayHighlight: 1,
            startView: 2,
            minView: 2,
            forceParse: 0
        });

    });




});


