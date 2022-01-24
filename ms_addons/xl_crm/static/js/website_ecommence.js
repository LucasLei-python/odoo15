odoo.define('sdosoft_ecommerce.website_ecommence', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    //自动计算产品类型高度
    if ($('.product-category').length == 1) {
        $('.product-category').css('height', $(window).height() - 100);
    }

    function get_sku_product_and_price() {
        var $modal = $("#product_details_sku");
        var variant_ids = $modal.find(".modal-body").data("attribute_value_ids");
        var values = [];
        var return_obj = {'product_id': '', 'product_price': 0}
        $modal.find('.sku-list li.sku-tag.active').each(function () {
            values.push(+$(this).data("value-id"));
        });
        for (var k in variant_ids) {
            if (_.isEmpty(_.difference(variant_ids[k][1], values))) {
                return_obj['product_id'] = variant_ids[k][0]
                return_obj['product_price'] = variant_ids[k][2].toFixed(2)
                break;
            }
        }
        return return_obj;
    }

    $(".self_show_sku, .self_show_sku_cart, .self_show_sku_buy").on('click', function () {
        var product_id = $(this).data("product-id");
        ajax.jsonRpc("/micro/shop/product/show_sku/async", 'call', {'product_id': product_id})
            .then(function (html) {
                var $modal = $("#product_details_sku");
                $modal.find(".modal-content").empty().html(html);
                //$modal.modal({backdrop: "static"});
                $modal.modal('show');
                $modal.find("#buy_quantity").TouchSpin({
                    initval: 1
                });
                $modal.find(".sku-list .type .sku-tag").click(function () {
                    $(this).siblings().removeClass("active");//首先移除全部的active
                    $(this).toggleClass("active");//选中的添加acrive
                    var product = get_sku_product_and_price()
                    $modal.find(".modal-header .price .oe_currency_value").text(product.product_price);
                    $modal.find(".modal-header .thumb img").attr("src", "/web/image/product.product/" + product.product_id + "/image/90x90");
                });
                $(".self_add_to_cart, .self_add_to_order").click(function () {
                    var click_target = $(this);
                    var add_qty = $("#buy_quantity").val();
                    var postData = {'add_qty': add_qty};
                    var product = get_sku_product_and_price()
                    if (!product.product_id) {
                        $.toast("商品不存在");
                        return;
                    }
                    postData['product_id'] = product.product_id
                    ajax.jsonRpc("/micro/shop/update_cart/async", 'call', postData)
                        .then(function (quantity) {
                            $modal.modal("hide");
                            $.toast("已加入购物车");
                            if (click_target.hasClass("self_add_to_order")) {
                                location.href = "/micro/shop/cart";
                            }
                        });
                });
            });
    });

    $(".self_cart_list_edit").click(function () {
        var edit_text = $(this).text();
        $(".edit").text(edit_text == "编辑" ? "完成" : "编辑");
        $(".goods-list .goods").toggleClass("is-editing");
    });

    $(".container-shopping-cart input[name='quantity']").TouchSpin();
    $(".container-shopping-cart input[name='quantity']").on("change", function () {
        var $this = $(this);
        var product_id = $this.data("product-id");
        var line_id = $this.data("line-id");
        var set_qty = $this.val();
        shop_cart_update_json(line_id, product_id, set_qty);
    });
    $(".container-shopping-cart .delete-btn").on("click", function () {
        var $this = $(this);
        var product_id = $this.data("product-id");
        var line_id = $this.data("line-id");
        shop_cart_update_json(line_id, product_id, 0);
    });
    $(".selft_confirm_order").click(function () {
        location.href = "/micro/shop/order";
    });

    function shop_cart_update_json(line_id, product_id, set_qty) {
        ajax.jsonRpc("/micro/shop/update_cart_json", 'call', {
            'line_id': line_id,
            'product_id': product_id,
            'set_qty': set_qty
        }).then(function (data) {
            if (data.cart_quantity == 0) {
                $.alert("购物车已被清空，请重新加入", function () {
                    location.href = "/micro/shop";
                });
            } else {
                $(".self_amount_total .oe_currency_value").text(currency(data.amount_total));
                $(".self_cart_quantity").text("(" + data.cart_quantity + ")");
                if (set_qty == 0) {
                    $("div[data-line-id='" + line_id + "'][data-product-id='" + product_id + "']").remove();
                }
            }
        });
    }

    //计算合计
    function amount_total() {
        var total = parseFloat($(".self_shopping_total span.oe_currency_value").text());
        var point = parseFloat($("span.self_point_money").text());
        var coupon = parseFloat($("span.self_coupon_money").text());
        var cash = total - point - coupon;
        $(".order-total-price .oe_currency_value").text(cash.toFixed(2));
    }

    //积分兑换
    $("input.self_shopping_point").blur(function () {
        var $this = $(this);
        var point = $.trim($this.val());
        var reg = /^[0-9]+$/;
        if (point == "" || !reg.test(point)) {
            return false;
        }
        ajax.jsonRpc("/micro/shop/point_exchange", 'call', {'point': point})
            .then(function (data) {
                if (reg.test(data)) {
                    $(".self_point_money").text(parseFloat(data).toFixed(2));
                    $("#hid_point").val(point);
                    amount_total();
                }
                else {
                    $.toast(data);
                }
            });
    });

    //优惠券兑换
    $("a.self_my_coupon").click(function () {
        ajax.jsonRpc("/micro/shop/coupon_list", 'call', {})
            .then(function (html) {
                var $modal = $("#shopping_address_modal");
                $modal.find(".modal-content").empty().html(html);
                $modal.removeClass("modal-add-address").removeClass("modal-address").removeClass("modal-select-coupons").addClass("modal-select-coupons");
                $modal.modal('show');
                $modal.find("div.coupons-orange").click(function () {
                    var coupon_id = $(this).data("id");
                    ajax.jsonRpc("/micro/shop/coupon_exchange", 'call', {'coupon_id': coupon_id})
                        .then(function (data) {
                            $modal.modal('hide');
                            var reg = /^[0-9]+$/;
                            if (reg.test(data)) {
                                $(".self_coupon_money").text(parseFloat(data).toFixed(2));
                                $("#hid_coupon").val(coupon_id);
                                amount_total();
                            }
                            else {
                                $.toast(data);
                            }
                        });
                });
            });
    });

    //开始-----------订单地址--------------------

    $("a.self_shopping_address").click(function () {
        show_address_edit_modal("list", "0");
    });

    function show_address_edit_modal(call_type, shipping_id) {
        ajax.jsonRpc("/micro/shop/update_shop_address", 'call', {'call_type': call_type, 'shipping_id': shipping_id})
            .then(function (html) {
                    var $modal = $("#shopping_address_modal");
                    $modal.find(".modal-content").empty().html(html);
                    if ($modal.find("button.self_shopping_address_save").length == 1) {
                        $modal.removeClass("modal-add-address").removeClass("modal-address").removeClass("modal-select-coupons").addClass("modal-add-address");
                    } else {
                        $modal.removeClass("modal-add-address").removeClass("modal-address").removeClass("modal-select-coupons").addClass("modal-address");
                    }
                    //$modal.modal({backdrop: "static"});
                    $modal.modal('show');

                    if ($modal.find("input[name='location']").length == 1) {
                        var $target = $modal.find("input[name='location']");
                        var provance = $modal.find("input[name='state']").val();
                        var city = $modal.find("input[name='city']").val();
                        var area = $modal.find("input[name='district']").val();
                        $target.val(provance + ' ' + city + ' ' + area);


                        $target.citySelect({
                            provance: provance,
                            city: city,
                            area: area
                        });
                        $target.on('click', function (event) {
                            console.log("click..");
                            $target.citySelect('open');
                        });
                        $target.on('done.ydui.cityselect', function (ret) {
                            $modal.find("input[name='state']").val(ret.provance);
                            $modal.find("input[name='city']").val(ret.city);
                            $modal.find("input[name='district']").val(ret.area);
                            $target.val(ret.provance + ' ' + ret.city + ' ' + ret.area);
                            console.log(ret.provance + ' ' + ret.city + ' ' + ret.area);
                        });
                    }

                    $modal.find("a.self_shopping_address_add").click(function () {
                        show_address_edit_modal("edit", "0");
                    });

                    $modal.find("a.self_shopping_address_edit").click(function (event) {
                        var shipping_id = $(this).data("shipping-id");
                        show_address_edit_modal("edit", shipping_id);
                        event.stopPropagation();
                    });

                    $modal.find("div.self_shopping_address_item").click(function (event) {
                        var shipping_id = $(this).data("shipping-id");
                        ajax.jsonRpc("/micro/shop/single_address", 'call', {
                            'shipping_id': shipping_id
                        }).then(function (html) {
                            $("a.self_shopping_address").html(html);
                            $modal.modal("hide");
                        });
                    });

                    $modal.find("button.self_shopping_address_save").click(function () {
                        var postData = {'call_type': 'edit'}
                        postData['shipping_id'] = $(this).data("shipping-id");
                        postData['name'] = $modal.find("input[name='name']").val();
                        postData['phone'] = $modal.find("input[name='phone']").val();
                        postData['provance'] = $modal.find("input[name='state']").val();
                        postData['city'] = $modal.find("input[name='city']").val();
                        postData['district'] = $modal.find("input[name='district']").val();
                        postData['address'] = $modal.find("input[name='address']").val();
                        postData['postcode'] = $modal.find("input[name='postcode']").val();

                        ajax.jsonRpc("/micro/shop/member/address/edit", 'call', postData).then(function (data) {
                            if (data == 'ok') {
                                show_address_edit_modal("list", "0");
                            } else {
                                $.toast(data, "cancel");
                            }
                        });
                    });
                }
            );
    }

    $("button.self_shopping_submit").click(function () {
        var shipping_id = $.trim($("a.self_shopping_address div.selected").data("id"));
        var buyer_remark = $(".self_shopping_remark").val();
        var point = $("#hid_point").val();
        var coupon_id = $("#hid_coupon").val();
        if (shipping_id == "") {
            $.toast("收件入信息不能为空", "cancel");
            return;
        }
        ajax.jsonRpc("/micro/shop/update_shop_order", 'call', {
            'shipping_id': shipping_id,
            'buyer_remark': buyer_remark,
            'point': point,
            'coupon_id': coupon_id,
        }).then(function (data) {
            if (data.key == 'exception') {
                $.alert(data.message);
            }
            else if (data.key == 'error') {
                $.alert("购物车已被清空，请重新加入", function () {
                    location.href = "/micro/shop";
                });
            } else {
                location.href = "/micro/shop/pay/" + data.message;
            }
        });
    });

    //结束-----------订单地址--------------------

    //开始-----------会员中心--地址管理--------------------
    function show_member_address_list() {
        ajax.jsonRpc("/micro/shop/member/address/shipping", 'call', {})
            .then(function (html) {
                $(".self_member_address_list").html(html);

                $(".self_member_address_list i.icon-check").click(function () {
                    if ($(this).hasClass("icon-check-active")) {
                        return;
                    }
                    var postData = {'call_type': 'default'}
                    postData['shipping_id'] = $(this).data("shipping-id");

                    ajax.jsonRpc("/micro/shop/member/address/edit", 'call', postData).then(function (data) {
                        if (data == 'ok') {
                            show_member_address_list();
                        } else {
                            $.toast(data, "cancel");
                        }
                    });
                });

                $(".self_member_address_list a.self_member_address_edit").click(function () {
                    var shipping_id = $(this).data("shipping-id");
                    show_member_address_edit(shipping_id);
                    event.stopPropagation();
                });
                $(".self_member_address_list a.self_member_address_add").click(function () {
                    show_member_address_edit("0");
                });
            });
    }

    function show_member_address_edit(shipping_id) {
        ajax.jsonRpc("/micro/shop/member/address/shipping/edit", 'call', {'shipping_id': shipping_id})
            .then(function (html) {
                    var $modal = $("#member_address_modal");
                    $modal.find(".modal-content").empty().html(html);
                    $modal.modal('show');

                    var $target = $modal.find("input[name='location']");
                    var provance = $modal.find("input[name='state']").val();
                    var city = $modal.find("input[name='city']").val();
                    var area = $modal.find("input[name='district']").val();

                    $target.val(provance + ' ' + city + ' ' + area);
                    $target.citySelect({
                        provance: provance,
                        city: city,
                        area: area
                    });
                    $target.on('click', function (event) {
                        console.log("click..");
                        $target.citySelect('open');
                    });
                    $target.on('done.ydui.cityselect', function (ret) {
                        $modal.find("input[name='state']").val(ret.provance);
                        $modal.find("input[name='city']").val(ret.city);
                        $modal.find("input[name='district']").val(ret.area);
                        $target.val(ret.provance + ' ' + ret.city + ' ' + ret.area);
                        console.log(ret.provance + ' ' + ret.city + ' ' + ret.area);
                    });

                    $modal.find("button.self_shopping_address_save").click(function () {
                        var postData = {'call_type': 'edit'}
                        postData['shipping_id'] = $(this).data("shipping-id");
                        postData['name'] = $modal.find("input[name='name']").val();
                        postData['phone'] = $modal.find("input[name='phone']").val();
                        postData['provance'] = $modal.find("input[name='state']").val();
                        postData['city'] = $modal.find("input[name='city']").val();
                        postData['district'] = $modal.find("input[name='district']").val();
                        postData['address'] = $modal.find("input[name='address']").val();
                        postData['postcode'] = $modal.find("input[name='postcode']").val();

                        ajax.jsonRpc("/micro/shop/member/address/edit", 'call', postData).then(function (data) {
                            if (data == 'ok') {
                                show_member_address_list();
                                $modal.modal('hide');
                            } else {
                                $.toast(data, "cancel");
                            }
                        });
                    });

                    $modal.find("button.self_shopping_address_remove").click(function () {
                        var postData = {'call_type': 'remove'}
                        postData['shipping_id'] = $(this).data("shipping-id");

                        ajax.jsonRpc("/micro/shop/member/address/edit", 'call', postData).then(function (data) {
                            if (data == 'ok') {
                                show_member_address_list();
                                $modal.modal('hide');
                            } else {
                                $.toast(data, "cancel");
                            }
                        });
                    });
                }
            );
    }

    if ($(".self_member_address_list").length == 1) {
        show_member_address_list();
    }

    //结束-----------会员中心--地址管理--------------------

    //开始-----------会员中心--绑定手机--------------------

    function disableSend($button) {
        var num = 89;
        var msg = "重新获取";
        $button.prop("disabled", true).text(msg + "(" + num + ")");
        var h = window.setInterval(function () {
            if (num != 0) {
                $button.prop("disabled", true).text(msg + "(" + num + ")");
            } else {
                $button.prop("disabled", false).text("获取验证码");
                window.clearInterval(h);
            }
            num--;
        }, 1000);
    }

    $("button.self_button_code").click(function () {
        var $button = $(this);
        var mobile = $(".self_mobile").val();
        if (!(/^1[34578]\d{9}$/.test(mobile))) {
            $.toast("手机号码格式不正确", "text");
            return;
        }
        ajax.jsonRpc("/alisms/send", 'call', {'mobile': mobile}).then(function (data) {
            $.toast(data.message, "text");
            if (data.success) {
                disableSend($button);
            }
        });
    });
    $("button.self_confirm_code").click(function () {
        var mobile = $.trim($(".self_mobile").val());
        var code = $.trim($(".self_code").val());
        if (mobile == "" || code == "") {
            $.toast("请输入手机号码和验证码", "text");
            return;
        }
        ajax.jsonRpc("/micro/shop/member/mobile/async", 'call', {'mobile': mobile, 'code': code}).then(function (data) {
            if (data == 'ok') {
                $.toast("手机号码绑定成功");
                window.setTimeout(function () {
                    location.href = "/micro/shop/member";
                }, 800);
            } else {
                $.toast(data, "text");
            }
        });
    });


    //结束-----------会员中心--绑定手机--------------------

    //微信支付 开始
    $("button.self_wxpay_now").click(function () {
        var acquirer_id = $.trim($("#acquirer_id").val());
        var order_id = $.trim($("#order_id").val());
        if (acquirer_id == "") {
            $.toast("请选择支付方式");
            return false;
        }
        if (order_id == "") {
            $.toast("订单不存在");
            return false;
        }
        ajax.jsonRpc('/micro/shop/payment/transaction/' + acquirer_id + '/' + order_id, 'call', {}).then(function (data) {
            $(data).appendTo('body').submit();
        });
    });
    $("button.self_otherpay_now").click(function () {
        $.toast("不支持该支付方式");
        return false;
    });

    //微信支付 结束

    //订单评价
    $("button.self_order_review").click(function () {
        var review = new Array();
        var order_id = $("#hid_order_id").val();
        $("textarea").each(function () {
            var content = $.trim($(this).val());
            var product_id = $(this).data("product_id");
            if (content == "") {
                review = new Array();
                return;
            } else {
                review.push({'content': content, 'product_id': product_id})
            }
        });
        if (review.length == 0) {
            $.toast("请评价所有的商品");
            return false;
        }
        ajax.jsonRpc("/micro/shop/member/order/review/async", 'call', {
            'reviews': review,
            'order_id': order_id
        }).then(function (data) {
            if (data == 'ok') {
                $.toast("评价成功，谢谢您的评价！");
                window.setTimeout(function () {
                    location.href = "/micro/shop/member/order/completed";
                }, 800);
            } else {
                $.toast(data, "text");
            }
        });
    });

    //提现
    $("button.self_cash").click(function () {
        ajax.jsonRpc("/micro/shop/member/distribution/cash/async", 'call', {}).then(function (data) {
            if (data == 'ok') {
                $.toast("提现申请提交成功");
                window.setTimeout(function () {
                    location.href = "/micro/shop/member/distribution/account?tab=cash";
                }, 800);
            } else {
                $.toast(data, "text");
            }
        });
    });

    //生成推广二维码
    var qrcode_url = $.trim($("#qr_market_code").data("qrcode_url"));
    if (qrcode_url) {
        var qrcode = new QRCode(document.getElementById("qr_market_code"), {
            width: 200,
            height: 200
        });
        qrcode.makeCode(qrcode_url);
    }
});