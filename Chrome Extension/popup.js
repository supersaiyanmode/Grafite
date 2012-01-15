backgroundPage = chrome.extension.getBackgroundPage();

function setStatus(str){
    $('#divErrorMessage').html(str);
}

function loadBirthdays(){
    var obj = backgroundPage.config.birthdays;
    if (!obj)   return;
    var str = "";
    for (var i=0; i<obj.birthdays.length; i++){
        str += '<div style="float:left">';
        str += '<img src="https://graph.facebook.com/' + obj.birthdays[i].uid + '/picture" width="30px" height="30px" style="margin-right:5px;float:left"/>';
        str += '</div><div><a href="#" onclick="openUrl(\'https://www.facebook.com/profile.php?id='+obj.birthdays[i].uid+'\');return false;"><strong>' + obj.birthdays[i].name + '</strong></a><br>';
        str += '<a href="#" onclick="$(this).slideUp();$(\'#divBirthdaysWish_' + obj.birthdays[i].uid + '\').slideDown();return false;">Wish!</a>';
        str += '<div id="divBirthdaysWish_' + obj.birthdays[i].uid + '" style="display:none">';
        str += '<input type="text" value="Happy Birthday! :-)" id="txtBirthdayWish_' + obj.birthdays[i].uid + '"> </input>';
        str += '<a href="#" onclick="wishHB(\'' + obj.birthdays[i].uid + '\');return false">Wish!</a>';
        str += '</div>';
        str += '</div>';
        str += "<div style='clear:both'/>";
    }
    $('#divBirthdaysList').html(str);
    $('#spanBirthdayCount').html(""+obj.birthdays.length);
}

$(function(){
    init();
    $('#lnkRIL').click(function(){$('#divRILReminder').toggle("fast");});
    $('#lnkPublishCurrentPage').click(function(){
        $('#divPublishCurrentPage').toggle("fast");
        chrome.tabs.getSelected(null,function(tab){
            $('#txtIFoundThisInteresting').val("I found this interesting: " + tab.url);
        });
      
    });
});
function init(){
    if (backgroundPage.config.accessToken){
        var at = backgroundPage.config.accessToken;
        $('#divUnauthorised').hide();
        $('#divAuthorised').show();
        var url="https://grafiteapp.appspot.com/users/?type=profileDetails&UserID=@me&access_token="+at;
        $.get(url, function(data) {
            var data = $.parseJSON(data);
            if (data.result.toLowerCase() == "success"){
                $('#imgUserDP').attr("src","https://grafiteapp.appspot.com" + data.data.dp);
                $('#imgUsername').html("<a href='https://grafiteapp.appspot.com" 
                                                + data.data.url + "'>" + data.data.nickname + "</a>");
                loadBirthdays();
                loadFBNotifications();
            }else{
                refreshAccessToken(init);
            }
        });
    }else{
        $('#divAuthorised').hide();
        $('#divUnAuthorised').show();
        
    }
    setStatus('');
}

function refreshAccessToken(){
    backgroundPage.refreshUserAccessToken({
        success:function(at){init();},
        error:function(){
            $('#divUnauthorised').show();
            $('#divAuthorised').hide();
        }
    });
}
function publishCurrentPage(){
    chrome.tabs.getSelected(null,function(tab){
        var services = [];
        var arr = ['Facebook','Buzz','Twitter'];
        for (var s in arr){
            if($('#chkUpdate'+arr[s] + "_IFTI").is(":checked")){
                services.push(arr[s]);
            }
        }
        services = services.join(",");
        postStatusUpdate("I found this interesting: " + tab.url,services);
    });
}

function updateStatus(){
    var text = $.trim($('#txtStatus').val());
    if (text == "")
        return;
    postStatusUpdate(text);
}
function postStatusUpdate(text,services){
    if (typeof services === 'undefined'){
        var services = [];
        var arr = ['Facebook','Buzz','Twitter'];
        for (var s in arr){
            if($('#chkUpdate'+arr[s]).is(":checked")){
                services.push(arr[s]);
            }
        }
        services = services.join(",");
    }
    backgroundPage.postStatusUpdate(text,services);
}


function loadFBNotifications(){
    var notifications = backgroundPage.config.FBNotifications;
    if (!notifications)
        return;
    var str = "";
    for (var i=0; i<notifications.data.length; i++){
        str += '<div style="float:left">';
        str += '<img src="https://graph.facebook.com/' + notifications.data[i].from.id + '/picture" width="30px" height="30px" style="margin-right:5px;float:left"/>';
        str += '</div><div><a href="#" onclick="openUrl(\''+notifications.data[i].link+'\');return false;"><strong>' + notifications.data[i].title+ '</strong></a><br>';
        str += '<timeago title="'+notifications.data[i].updated_time+'"></timeago>';
        str += '</div>';
        str += "<div style='clear:both; margin-top:3px;'/>";
    }
    $('#divNotificationsList').html(str);
    $('#spanNotificationsCount').html("" + notifications.data.length);
}

function addPageReminder(){
    var time = $.trim($('#txtRILReminderTime').val());
    chrome.tabs.getSelected(null,function(tab){
        postReminder("You marked the following page as Read-It-Later:\n\n"+tab.url, time);
    });
}

function wishHB(fbId){
    backgroundPage.wishHB(fbId,$.trim($("#txtBirthdayWish_" + fbId).val()));
}

function postReminder(reminderText,time){
    backgroundPage.addReminder(remindText,time);
    return false;
}
function register(){
    var code = $("#txtCode").val();
    if (code == "")
        return false;
    $('#divErrorMessage').html("Please wait ..");
    backgroundPage.register(code,{
        success:function(at){init();},
        error:function(at){
            $('#divErrorMessage').html("Grr..Invalid Code, retry! :-(");
        }
    });
}
function unregister(){
    backgroundPage.logout(init);
}
function openLoggedOnUrl(url){
    if (backgroundPage.config.accessToken)
    openUrl("https://grafiteapp.appspot.com/userHome?access_token="+backgroundPage.config.accessToken+"&redirect=" + url);
}
function openUrl(url){
    chrome.tabs.create({'url': url}, function(tab) {});
}