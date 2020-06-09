crossOrigin: 'anonymous',
function add_search() {
    var val = $(".searchInput").val();
    if (val.length >= 2) {
        //点击搜索按钮时，去重
        KillRepeat(val);
        //去重后把数组存储到浏览器localStorage
        localStorage.search = searchArr;
        //然后再把搜索内容显示出来
        MapSearchArr();
    }

    window.location.href = search_url + '?q=' + val + "&s_type=" + $(".searchItem.current").attr('data-type')

}

function MapSearchArr() {
    var tmpHtml = "";
    var arrLen = 0
    if (searchArr.length >= 5) {
        arrLen = 5
    } else {
        arrLen = searchArr.length
    }
    for (var i = 0; i < arrLen; i++) {
        tmpHtml += '<a href="' + search_url + '?q=' + searchArr[i] + '">' + searchArr[i] + '</a>'
    }
    $(".mysearch .all-search").html(tmpHtml);
}

//去重
function KillRepeat(val) {
    var kill = 0;
    for (var i = 0; i < searchArr.length; i++) {
        if (val === searchArr[i]) {
            kill++;
        }
    }
    if (kill < 1) {
        searchArr.unshift(val);
    } else {
        removeByValue(searchArr, val)
        searchArr.unshift(val)
    }
}

function openBrowse() {
    var ie = navigator.appName == "Microsoft Internet Explorer" ? true : false;
    if (ie) {
        document.getElementById("soutu").click();
    } else {
        var a = document.createEvent("MouseEvents");
        a.initEvent("click", true, true);
        document.getElementById("soutu").dispatchEvent(a);
    }
}

function uploadImg(files) {
    var formData = new FormData();
    formData.append('file', files[0])
    $.ajax({
        url: '/soutu',
        type: 'POST',
        data: formData,
        dataType: 'json',
        cache: false,
        processData: false,
        contentType: false,
        success: function (data) {
            var val = data["key_words"]
            if (val.length >= 2) {
                //点击搜索按钮时，去重
                KillRepeat(val);
                //去重后把数组存储到浏览器localStorage
                localStorage.search = searchArr;
                //然后再把搜索内容显示出来
                MapSearchArr();
            }
            console.log('dddd')
            window.location.href = search_url + '?q=' + val + "&s_type=" + $(".searchItem.current").attr('data-type')
        },
        error: function (data) {
            alert("网络错误");
        }
    });
    return false;
}
