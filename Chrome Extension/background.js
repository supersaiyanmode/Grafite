config = {
    get PAC(){
        if (typeof(localStorage['PAC']) == 'undefined' || localStorage['PAC'] == '')
            return null;
        return localStorage['PAC'];
    },
    set PAC(val){
        localStorage['PAC'] = val;
    },
    
    get accessToken(){
        if (!config.PAC)
            return null;
        if (localStorage['GrafiteAccessToken'] && localStorage['GrafiteAccessToken']!= '')
             return localStorage['GrafiteAccessToken'];
        return null;
    },
    set accessToken(val){
        localStorage['GrafiteAccessToken'] = val;
    },
    
    get facebookAccessToken(){
        if (!config.PAC)
            return null;
        if (localStorage['FacebookAccessToken'] && localStorage['FacebookAccessToken']!= '')
             return localStorage['FacebookAccessToken'];
        return null;
    },
    set facebookAccessToken(val){
        localStorage['FacebookAccessToken'] = val;
    },
    
    get birthdays(){
        if (!config.accessToken)
            return null;
        if (!localStorage['birthdays'])
            return null;
        return JSON.parse(localStorage['birthdays']);
    },
    set birthdays(val){
        localStorage['birthdays'] = JSON.stringify(val);
    },
    
    get FBNotifications(){
        if (!config.accessToken)
            return null;
        if (!localStorage['FBNotifications'])
            return null;
        return JSON.parse(localStorage['FBNotifications']);
    },
    set FBNotifications(val){
        localStorage['FBNotifications'] = JSON.stringify(val);
        //update the badge!
        var len = val.data.length;
        if (len)
            chrome.browserAction.setBadgeText({text:""+len});
        else
            chrome.browserAction.setBadgeText({text:""});
        chrome.browserAction.setBadgeBackgroundColor({color:[0,0,200,120]});
        
    }
}

function getPopupWindow(){
    var views = chrome.extension.getViews({type:"popup"});
    if (views.length){
        return views[0];
    }
    return null;
}
function setPopupMessageStatus(str){
    var obj = getPopupWindow();
    obj && obj.setStatus(str);
}

function logout(callback){
    setPopupMessageStatus("Please wait ..");
    var req = {"t":"unregister","pac":config.PAC};
    $.post("https://grafiteapp.appspot.com/api/unregister",req,function(data,text,jqXHR){
        var res = data;//$.parseJSON(data);
        if (res.result == "success"){
            config.PAC = '';
            config.accessToken = '';
            callback();
        }else{
            setPopupMessageStatus("Couldn't log out! :-(");
            callback();
        }
    });
    init();
}

function register(code,callback){
    if (code == "")
        return false;
    setPopupMessageStatus("Please wait ..");
    var req = {"t":"register","code":code};
    $.post("https://grafiteapp.appspot.com/api/register",req,function(data,text,jqXHR){
        var res = data;
        if (res.result == "success"){
            config.PAC = res.pac;
            refreshUserAccessToken({
                success:callback.success,
                error:callback.error
            });
        }else{
            setPopupMessageStatus("Invalid Code, retry!");
        }
    });
}

function refreshUserAccessToken(obj){
    if (!config.PAC){
        obj.error("Not Logged in!");
        return;
    }
    var req = {"t":"getUserAccessToken","pac":config.PAC};
    $.post("https://grafiteapp.appspot.com/api/status",req,function(data,text,jqXHR){
        var response = data;//$.parseJSON(data);
        if (response.result=="success"){
            config.accessToken = response.AccessToken;
            initServices();
            if (obj.success)
                obj.success(response.AccessToken);
        }else{
            config.PAC = null;
            config.accessToken = null;
            init();
            if (obj.error)
                obj.error("Not Logged in!");
            
        }
    });
}

function getBirthdays(){
    $.get("https://grafiteapp.appspot.com/facebook/birthdays/?access_token="+config.accessToken,function(data){
        if (data.result.toLowerCase() == 'success')
            config.birthdays = {"birthdays":data.content,"updated":new Date()};
    });
}
function wishHB(fbId,text){
    setPopupMessageStatus("Posting...");
    req = {"status":text,"alt":"json","access_token":config.accessToken, "to":fbId};
    $.post("https://grafiteapp.appspot.com/facebook/update/",req,function(data,text,jqXHR){
        setPopupMessageStatus(data.result=='success'?"Posted!":"Unable to post!");
    });
}

function postStatusUpdate(text,services){
    if (services == "")
        return;
    setPopupMessageStatus("Posting...");
    var req = {"status":text,"services":services,"alt":"json","access_token":config.accessToken};
    $.post("https://grafiteapp.appspot.com/status",req,function(data,text,jqXHR){
        var response = $.parseJSON(data);
        console.log(response);
        if (response.result.toLowerCase() != "success"){
            refreshUserAccessToken(function(x){postStatusUpdate(text,services);});
        }
        response = response.data;
        var postedTo = [];
        var notPosted = [];
        for (x in response){
            if (response[x].result.toLowerCase() == "success")
                postedTo.push(x);
            else
                notPosted.push(x);
        }
        var innerHTML = "";
        if (postedTo.length>0)
            innerHTML += "Posted to " + postedTo.join(",") + "<br>";
        if (notPosted.length>0)
            innerHTML += "Unable to post to " + NotPosted.join(",");
        
        setPopupMessageStatus(innerHTML);
    });
}

function getFBNotifications(){
    var req = "?access_token="+config.accessToken;
    $.get("https://grafiteapp.appspot.com/facebook/notifications/"+req,function(data){
        if (data.result.toLowerCase() == "success"){
            config.FacebookAccessToken = data.data;
            console.log("Got FB AccessToken");
        }else{
            refreshUserAccessToken(function(x){getFBNotifications();});
        }
    });
}

function getFBAccessToken(){
    var req = "?access_token="+config.accessToken;
    $.get("https://grafiteapp.appspot.com/facebook/accessToken/"+req,function(data){
        if (data.result.toLowerCase() == "success"){
            config.facebookAccessToken = data.data;
        }else{
            refreshUserAccessToken(function(x){getFBNotifications();});
        }
    });
}

function getFacebookTickerData(){
    var str = "";
    for (x in FacebookStream){
        str += FacebookStream[x].html;
    }
    return str;
}

function addReminder(text, remindAt){
    setPopupMessageStatus("Adding reminder...");
    var req={"type":"add", "time":remindAt, "text":text,"access_token":config.AccessToken}
    $.post("https://grafiteapp.appspot.com/reminder",req,function(data,text,jqXHR){
        if (data.result == "success")
            setPopupMessageStatus("Reminder added!");
        else
            setPopupMessageStatus("Error trying to add reminder..");
    });
}
function initServices(){
    getBirthdays();
    getFBAccessToken();
    getFBNotifications();
    birthdayIntervalTimer = setInterval(getBirthdays, 1*60*60*1000);
    //FBNotificationsTimer = setInterval(getFBNotifications, 20000);
    FBTickerTimer = setInterval(loadFacebookFeed, 20000);
}

function init(){
    localStorage['PAC'] = "dbecab24-9cba-4533-9aad-bd2920a717b5"; //REMOVE THIS LINE WHEN PUBLISHING!
    refreshUserAccessToken({
        success:function(x){}, //initServices will be called by refreshUserAccessToken()
        error:function(x){}
    });    
}
$(function(){ init(); });
