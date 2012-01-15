FacebookStream = [];

function parseFacebookTime(str) {
    var parts = str.split('T'),
    dateParts = parts[0].split('-'),
    timeParts = parts[1].split('+')[0].split(':'),
    d = new Date();

    d.setUTCFullYear(Number(dateParts[0]));
    d.setUTCMonth(Number(dateParts[1])-1);
    d.setUTCDate(Number(dateParts[2]));
    d.setUTCHours(Number(timeParts[0]));
    d.setUTCMinutes(Number(timeParts[1]));
    d.setUTCSeconds(Number(timeParts[2]));
    return d;
}


function getCommentStr(postId, imgSrc, fromProfileUrl,fromName, message,time,userLikes,noOfUserLikes){
    var str = ""
    str += "<div class='FeedCommentEntry'>";
    str += "<div class='FeedCommentEntryImageLogo'>";
    str += "<img src='"+imgSrc+"' width='30px' height='30px'/>";
    str += "</div>";
    str += "<div class='FeedCommentEntryContentWrap'>";
    str += "<div class='FeedCommentEntryUser'>";
    str += "<a href='"+fromProfileUrl+"'>" + fromName + "</a>";
    str += "</div>";
    str += "<div class='FeedCommentEntryContent'>" + message + "</div>";
    str += "<div class='FeedCommentEntryActions'><span class='timeago' title='" + time +"'></span>&nbsp;&nbsp;&bull;&nbsp;&nbsp;";
    str += "<a href='#' id='like_"+postId+"' onclick='postFacebookLike(\""+postId+"\");return false;'>"+(userLikes?"Unlike":"Like")+"</a>";
    
    if (noOfUserLikes)
        str += "&nbsp;&nbsp;&bull;&nbsp;&nbsp;<a href='#' id='like_"+postId+"' onclick='return false;'>"+noOfUserLikes+" like(s)</a>";
    
    str += "</div>";
    str += "</div>";
    str += "<div style='height:1px;clear:both'>&nbsp;</div>";
    str += "</div>";
    return str;
}

function getFacebookFeedEntry(data){
    var str = "";
    var canComment = false;
    if (["status","link"].indexOf(data.type)<0)
        return {};
    str += "<div class='FeedEntry FacebookFeedEntry' id='Facebook_post_"+data.id+"'><span class='FeedUserLogo'><img src='https://graph.facebook.com/" + data.from.id + "/picture' width='30px' height='30px'></img></span>";
    str += "<div class='FeedContentWrap'>";
    str += "<div class='FeedTitle'>";
    str += "<a  target='_blank' href='http://www.facebook.com/profile.php?id="+data.from.id+"'>";
    str += data.from.name+ "</a>";
    if (data.to){
        str += " > ";
        var arr = [];
        for (var j=0; j<data.to.data.length; j++){
            arr.push("<strong><a  target='_blank'  href='http://www.facebook.com/profile.php?id="+data.to.data[j].id+"'>" + data.to.data[j].name+ "</a></strong>");
        }
        str += arr.join(", ");
    }
    if (data.message){
        var msg = $.trim(data.message).replace("<","&lt;").replace(">","&gt;").replace(/\n/mg,"<br>\n");
        var tempMsg = msg.split(/\s/);
        if (tempMsg.length > 30){
            tempMsg = tempMsg.slice(0,30).join(' ');
            tempMsg += "<script type='text/javascript'>function expandPost_" + data.id + "(){";
            tempMsg += "$('#Post_" + data.id + "_expand').html('" + msg.replace(/\n/mg, "\n\\") + "'); }";
            tempMsg += "</script><span id='#Post_" + data.id + "_expand'><a href='#'>expand</a></span>";
            msg = tempMsg;
        }
        str += "<div class='FeedTopMessage'>" + msg;
        if (data.with_tags){
            str += "<span class='withText'> — with </span>";
            var withArr = [];
            for (var j=0; j<data.with_tags.data.length; j++){
                withArr.push("<a  target='_blank'  href='http://www.facebook.com/profile.php?id="+data.with_tags.data[j].id+"'>" +  data.to.data[j].name+ "</a>");
            }
            str += withArr.join(", ");
        }
        str +=  "</div>\n"; //FeedTopMessage
    }
    str += "</div>";
    str += "<div class='FeedMainContentWrap'>";
    if(data.type.toLowerCase() == "link"){
        str += "<div class='FeedExtraLinkArea'>";
        if (data.picture){
            str += "<div class='FeedExtraLinkImagePreview'>";
            str += "<img src='" + data.picture + "'/>";
            str += "</div>";
        }
        str += "<div class='FeedExtraLinkContent'>";
        if (data.link && data.name)
            str += "<a target='_blank' href='" + data.link + "'>" + data.name + "</a><br>";
        if (data.caption)
            str += "<div class='FeedExtraLinkContentCaption'>" + (data.caption||"") + "</div>";
        if (data.description)
            str += "<div class='FeedExtraLinkContentDescription'>" + (data.description||"") + "</div>";
        else if (data.properties)
            str += "<a target='_blank' href='" + data.properties[0].href + "'>" + data.properties[0].name+ "</a>&nbsp;"+ data.properties[0].text;
        str += "</div>";
        str += "<div style='clear:both'></div>";
        str += "</div>";
    }
    str += "<div class='FeedMainContentActions'>";
    var actions = ["<a href='#' ><span class='timeago' title='"+data.updated_time+"'/></a>"
        + (data.application? " via <a href='https://www.facebook.com/apps/application.php?id=" + data.application.id + "'>" + data.application.name + "</a>" : "")
    ];
    for (j=0; j<data.actions.length; j++){
        var curAction = data.actions[j].name;
        if (curAction.toLowerCase() == 'comment'){
            canComment = true;
            actions.push("<a  href='#' id='"+data.id+"' onclick='return false;'>"+ curAction + "</a>");
        }
        else if(curAction.toLowerCase() =='like'){
            var userLikes = false;
            try{
                if (data.likes.data[0].id == FacebookUserId)
                    userLikes = true;
            }catch (e){}
            actions.push("<a  href='#' id='like_"+data.id+"' onclick='return postFacebookLike(\""+data.id+"\")'>"+(userLikes?"Unlike":"Like")+"</a>");
        }
        else
            actions.push("<a  href='" + data.actions[j].link+"' target='_blank'>"+data.actions[j].name+"</a>");
    }
    str += actions.join("&nbsp;&bull;&nbsp");
    str += "</div>"; //FeedMainContentActions

    if (data.likes && data.likes.count > 0){
        str += "<div class='FeedMainContentLikes'>";
        var likes = []
        for (j=0; data.likes.data && j<data.likes.data.length; j++){
            likes.push("<a href='https://www.facebook.com/profile.php?id="+data.likes.data[j].id+"'>" + data.likes.data[j].name+"</a>"); 
        }
        str += "<img src='/images/like.gif' width='15px' height='15px' style='margin-right:10px'></img>" + likes.join(", ");
        if (data.likes.count != j){
            str += " and " + (data.likes.count-(data.likes.data?data.likes.data.length:0)) + " others like(s) this";
        }
        str += "</div>";
    }
    if (data.comments.count > 0){
        str += "<div class='FeedMainContentComments' id='Facebook_post_"+data.id+"_comments'>";
        if (!data.comments.data || (data.comments.data.length != data.comments.count)){
            str += "<div class='FeedCommentEntry'><a href='#' onclick='getAllFBComments(\"" + data.id +"\");return false'>View all " + data.comments.count + " comments</a></div>";
        }
        for (j=0; data.comments.data && j<data.comments.data.length; j++){
            var userLikes = false;
            str += getCommentStr(data.comments.data[j].id,
                                    'https://graph.facebook.com/' + data.comments.data[j].from.id + '/picture',
                                    'https://www.facebook.com/profile.php?id=' + data.comments.data[j].from.id,
                                    data.comments.data[j].from.name,
                                    data.comments.data[j].message,
                                    data.comments.data[j].created_time,
                                    userLikes,
                                    data.comments.data[j].likes
                                );
        }
        str += "</div>"; //FeedComments
    }
    if (canComment){
        str += "<div class='FeedMainContentUserComment' style='display:none' id='divFacebook_post_"+data.id+"_UserComment'>";
        str += "<input type='text' id='Facebook_post_"+data.id+"_UserComment'/>";
        str += "<button onclick='postFacebookComment(\"" + data.id + "\");return false;'>Comment</button>";
        str += "</div>";
        str += "<a href='#' id='linkFacebook_post_"+data.id+"_PromptComment' onclick=\"$('#divFacebook_post_"+data.id+"_UserComment').slideDown();$('#linkFacebook_post_"+data.id+"_PromptComment').hide();return false;\" style='margin-top:5px;text-align:center'>Comment</a>";
    }
    str += "</div><div style='clear:both'/>";
    str += "</div>";
    str += "</div>"; //FeedMainContentWrap
    return {"html":str,"time":parseFacebookTime(data.updated_time),"stream":"Facebook"};
}

function loadFacebookFeed(url){
    var xhr;
    var respFn = function(x){
        var data = JSON.parse(xhr.responseText);
        FacebookStream = [];
        for (var i=0; i<data.data.length; i++){
            var temp = getFacebookFeedEntry(data.data[i]);
            if (!temp.html)
                continue;
            FacebookStream.push(temp);
        }
        var temp = getFacebookFeedEntry(data.data[0]);
        temp.html = "<div class='FeedEntry'><a href='#' onclick='loadFacebookFeed(\""+data.paging.next+"\");return false;'>Load More</a></div>";
        //FacebookStream.push(temp);
        console.log(FacebookStream);
    };
    var respFn1 = function(x){
        console.log("ERRRRO!!!!!");
        respFn(x);
    };
    xhr = $.ajax({
        method:'GET',
        url:'https://graph.facebook.com/me/home?access_token=' + config.facebookAccessToken,
        success:respFn,
        error:respFn1
    }).done(respFn);
    return false;
}