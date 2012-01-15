var FacebookStream=[],BuzzStream=[],TwitterStream=[];

function parseISO8601(str) {
    var parts = str.split('T'),
    dateParts = parts[0].split('-'),
    timeParts = parts[1].split('Z'),
    timeSubParts = timeParts[0].split(':'),
    timeSecParts = timeSubParts[2].split('.'),
    timeHours = Number(timeSubParts[0]),
    _date = new Date;

    _date.setUTCFullYear(Number(dateParts[0]));
    _date.setUTCMonth(Number(dateParts[1])-1);
    _date.setUTCDate(Number(dateParts[2]));
    _date.setUTCHours(Number(timeHours));
    _date.setUTCMinutes(Number(timeSubParts[1]));
    _date.setUTCSeconds(Number(timeSecParts[0]));
    if (timeSecParts[1]) _date.setUTCMilliseconds(Number(timeSecParts[1]));
    return _date;
}

function parseFacebookTime(str) {
    var parts = str.split('T'),
    dateParts = parts[0].split('-'),
    timeParts = parts[1].split('+')[0].split(':'),
    d = new Date;

    d.setUTCFullYear(Number(dateParts[0]));
    d.setUTCMonth(Number(dateParts[1])-1);
    d.setUTCDate(Number(dateParts[2]));
    d.setUTCHours(Number(timeParts[0]));
    d.setUTCMinutes(Number(timeParts[1]));
    d.setUTCSeconds(Number(timeParts[2]));
    return d;
}

function parseTwitterTime(str){
    var months = "jan feb mar apr may jun jul aug sep oct nov dec".split(" ");
    var parts = str.split(' ');
    var time = parts[3].split(":");
    var d = new Date;

    d.setUTCDate(Number(parts[2]));
    d.setUTCMonth(months.indexOf(parts[1].toLowerCase()));
    d.setUTCFullYear(Number(parts[5]));
    
    d.setUTCHours(Number(time[0]));
    d.setUTCMinutes(Number(time[1]));
    d.setUTCSeconds(Number(time[2]));
    
    return d;
}

$(function(){
    var str = "<table><tr>";
    for (var i = 0; i<services.length; i++){
	str += "<td>" + services[i] + "<input type='checkbox' id='chk"+services[i]+"' name='" + services[i] +"Service' checked='checked'/></td>\n"
    }
    $('#divServicesCheckBoxes').html(str + "</tr></table>");
    $(':checkbox').iphoneStyle();

    //getFacebookDetails();
    //getBuzzDetails();
    //getTwitterDetails();
    
    loadBuzzFeed();
    loadFacebookFeed();
    loadTwitterFeed();
    
    $('.timeago').timeago();
});

function toggleStream(s){
    $("." + s + "FeedEntry").slideToggle();
}
function getFacebookDetails(){
    $.ajax({
	type: 'POST',
	url: '/facebook/status/',
	success: function(data){
	    if (data.result == 'success'){
		$('#spanFacebookLastStatus').html(data.status);
		$('#spanFacebookComments').html(data.comments);
		$('#spanFacebookLikes').html(data.likes);
		$('#lnkFacebook').attr('href',data.link);
		$('#imgFacebookDP').attr('src',data.DPSrc);
		$('#imgFacebookDP').attr('width',"100");
	    }
	}
    });
}

function getBuzzDetails(){
    $.ajax({
	type: 'POST',
	url: '/buzz/status/',
	success: function(data){
	    if (data.result == 'success'){
		$('#spanBuzzLastStatus').html(data.status);
		$('#spanBuzzComments').html(data.comments);
		$('#spanBuzzLikes').html(data.likes);
		$('#lnkBuzz').attr('href',data.link);
		$('#imgBuzzDP').attr('src',data.DPSrc);
		$('#imgBuzzDP').attr('width',"100");
		
	    }
	}
    });
}

function getTwitterDetails(){
    $.ajax({
	type: 'POST',
	url: '/twitter/status/',
	success: function(data){
	    data = $.parseJSON(data)
	    if (data.result == 'success'){
		$('#spanTwitterLastStatus').html(data.status);
		$('#spanTwitterRetweets').html(data.retweets);
		$('#lnkTwitter').attr('href',data.link);
		$('#imgTwitterDP').attr('src',data.DPSrc);
		$('#imgTwitterDP').attr('width',"100");
	    }
	}
    });
}

function update(){
    var text = $('#txtStatus').val();
    console.log(services);
    var toPost = []
    for (var i = 0; i<services.length; i++){
	if($('#chk'+services[i]).is(":checked")){
	    toPost.push(services[i]);
	}
    }
    console.log(toPost)
    var divSubmitBackup = $('#divSubmit').html()
    $('#divSubmit').html('<img src="/images/ajax-loader.gif"/>');
    var toPostServices = toPost.join(',')
    $.ajax({
		type: 'POST',
		url: '/status',
		data: {"status":text,"services":toPostServices,"alt":"json"},
		success: function(data){
			$('#txtStatus').val("");
			$('#divSubmit').html(divSubmitBackup);
			console.log(data);
			data = $.parseJSON(data);
			if (data.result == 'success'){
				getBuzzDetails();
				getFacebookDetails();
				getTwitterDetails();
			}
		}
    });
    return false;
}

function getFacebookFeedEntry(data){
    var str = "";
    var canComment = false;
    if (["status","link"].indexOf(data.type)<0)
        return {};
    str += "<div class='FeedEntry FacebookFeedEntry' id='Facebook_post_"+data.id+"'><div class='FeedUserLogo'><img src='https://graph.facebook.com/" + data.from.id + "/picture'></img></div>";
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
    str += "</div>";
    str += "<div class='FeedMainContentWrap'>";
    if (data.message){
        str += "<div class='FeedTopMessage'>" + data.message.replace(/\n/mg,"<br>\n");
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

function getBuzzFeedEntry(data){
    var str= "";
    str += "<div class='FeedEntry BuzzFeedEntry' id='Buzz_post_"+data.id+"'><div class='FeedUserLogo'><img width='50px' height=50px' src='" + data.actor.thumbnailUrl + "'></img></div>";
    str += "<div class='FeedContentWrap'>";
    str += "<div class='FeedTitle'>";
    str += "<a target='_blank' href='"+data.actor.profileUrl +"'>";
    str += data.actor.name+ "</a>";
    str += "</div>";
    str += "<div class='FeedMainContentWrap'>";
    str += "<div class='FeedTopMessage'>" + data.object.content + "</div>\n";
    
    if(data.object.attachments && data.object.attachments[0].type=="article"){
        str += "<div class='FeedExtraLinkArea'>";
        if (data.picture){ //FIXME
            str += "<div class='FeedExtraLinkImagePreview'>";
            str += "<img src='" + data.picture + "'/>";
            str += "</div>";
        }
        str += "<div class='FeedExtraLinkContent'>";
        if (data.title && data.title!=data.object.content)
            str += data.title.replace(/\n/mg,"<br>\n") + "<br><br>";
        str += "<a target='_blank' href='" + data.object.attachments[0].links.alternate[0].href + "'>" + data.object.attachments[0].title + "</a><br>";
        str += "<div class='FeedExtraLinkContentCaption'>" + data.object.attachments[0].links.alternate[0].href + "</div>";
        str += "<div class='FeedExtraLinkContentDescription'>" + data.object.attachments[0].content + "</div>";
        str += "</div>";
        str += "<div style='clear:both'></div>";
        str += "</div>";
    }
    str += "<div class='FeedMainContentActions'>";
    var actions = [
        "<a href='#' ><span class='timeago' title='"+data.updated+"'/></a>"
        + (data.source && data.source.title!="Buzz"? " via " + data.source.title : ""),
    
        "<a href='#'>Comment</a>",
    
        "<a href='#'>Like</a>"
    ];
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
            str += " and x others like(s) this";
        }
        str += "</div>";
    }
    if (data.comments){
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
    if (false){
        str += "<div class='FeedMainContentUserComment' style='display:none' id='divFacebook_post_"+data.id+"_UserComment'>";
        str += "<input type='text' id='Facebook_post_"+data.id+"_UserComment'/>";
        str += "<button onclick='postFacebookComment(\"" + data.id + "\");return false;'>Comment</button>";
        str += "</div>";
        str += "<a href='#' id='linkFacebook_post_"+data.id+"_PromptComment' onclick=\"$('#divFacebook_post_"+data.id+"_UserComment').slideDown();$('#linkFacebook_post_"+data.id+"_PromptComment').hide();return false;\" style='margin-top:5px;text-align:center'>Comment</a>";
    }
    str += "</div><div style='clear:both'/>";
    str += "</div>";
    str += "</div>"; //FeedMainContentWrap
    return {"html":str,"time":parseISO8601(data.updated),"stream":"Buzz"}
}
function getTwitterFeedEntry(data){
    var str= "";
    str += "<div class='FeedEntry TwitterFeedEntry' id='Twitter_post_"+data.id_str+"'><div class='FeedUserLogo'><img width='50px' height=50px' src='" + data.user.profile_image_url_https + "'></img></div>";
    str += "<div class='FeedContentWrap'>";
    str += "<div class='FeedTitle'>";
    str += "<a target='_blank' href='https://twitter.com/#!/"+data.user.screen_name +"'>";
    str += data.user.screen_name + "</a>&nbsp;<span class='fineprint' style='color:gray'>"+data.user.name+"</span>";
    str += "</div>";
    str += "<div class='FeedMainContentWrap'>";
    str += "<div class='FeedTopMessage'>" + data.text + "</div>\n";
    
    /*if(data.object.attachments && data.object.attachments[0].type=="article"){
        str += "<div class='FeedExtraLinkArea'>";
        if (data.picture){ //FIXME
            str += "<div class='FeedExtraLinkImagePreview'>";
            str += "<img src='" + data.picture + "'/>";
            str += "</div>";
        }
        str += "<div class='FeedExtraLinkContent'>";
        if (data.title && data.title!=data.object.content)
            str += data.title.replace(/\n/mg,"<br>\n") + "<br><br>";
        str += "<a target='_blank' href='" + data.object.attachments[0].links.alternate[0].href + "'>" + data.object.attachments[0].title + "</a><br>";
        str += "<div class='FeedExtraLinkContentCaption'>" + data.object.attachments[0].links.alternate[0].href + "</div>";
        str += "<div class='FeedExtraLinkContentDescription'>" + data.object.attachments[0].content + "</div>";
        str += "</div>";
        str += "<div style='clear:both'></div>";
        str += "</div>";
    }
    str += "<div class='FeedMainContentActions'>";
    var actions = [
        "<a href='#' ><span class='timeago' title='"+data.updated+"'/></a>"
        + (data.source && data.source.title!="Buzz"? " via " + data.source.title : ""),
    
        "<a href='#'>Comment</a>",
    
        "<a href='#'>Like</a>"
    ];
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
            str += " and x others like(s) this";
        }
        str += "</div>";
    }
    if (data.comments){
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
    if (false){
        str += "<div class='FeedMainContentUserComment' style='display:none' id='divFacebook_post_"+data.id+"_UserComment'>";
        str += "<input type='text' id='Facebook_post_"+data.id+"_UserComment'/>";
        str += "<button onclick='postFacebookComment(\"" + data.id + "\");return false;'>Comment</button>";
        str += "</div>";
        str += "<a href='#' id='linkFacebook_post_"+data.id+"_PromptComment' onclick=\"$('#divFacebook_post_"+data.id+"_UserComment').slideDown();$('#linkFacebook_post_"+data.id+"_PromptComment').hide();return false;\" style='margin-top:5px;text-align:center'>Comment</a>";
    }*/
    str += "</div><div style='clear:both'/>";
    str += "</div>";
    str += "</div>"; //FeedMainContentWrap
    return {"html":str,"time":parseTwitterTime(data.created_at),"stream":"Twitter"}
}

function loadFacebookFeed(url){
    $.ajax({
        method:'GET',
        url:'/facebook/feed/' + (url?'?paging='+encodeURIComponent(url):""),
        success:function(data){
            window.FacebookStream = [];
            for (var i=0; i<data.data.length; i++){
                var temp = getFacebookFeedEntry(data.data[i]);
                if (!temp.html)
                    continue;
                window.FacebookStream.push(temp);
            }
            var temp = getFacebookFeedEntry(data.data[0]);
	    temp.html = "<div class='FeedEntry'><a href='#' onclick='loadFacebookFeed(\""+data.paging.next+"\");return false;'>Load More</a></div>";
	    window.FacebookStream.push(temp);
	    loadUnifiedFeed();
        }
    });
    return false;
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
function postFacebookLike(postId){
    obj = $('#like_'+postId);
    $.ajax({
        type: 'POST',
        url: '/facebook/like/',
        data: {"postId":postId,"like":obj.html()},
        success: function(data){
            console.log(data);
            obj.html(obj.html().toLowerCase() == "like"?"Unlike":"Like");
        }
    });
    return false;
}
function postFacebookComment(postId){
    obj = $('#Facebook_post_'+postId + "_UserComment");
    $.ajax({
        type: 'POST',
        url: '/facebook/comment/',
        data: {"postId":postId,"comment":obj.val()},
        success: function(data){
                console.log(data);
                obj.html(obj.html().toLowerCase() == "like"?"Unlike":"Like");
                getAllFBComments(postId);
        }
    });
    return false;
}
function getAllFBComments(postId){
    $('#Facebook_post_' + postId + "_comments").html('<img src="/images/ajax-loader.gif"/>');
    $.get('/facebook/comments/?id='+postId,function(data){
        var str="";
        for (var i=0; i<data.comments.data.length; i++){
            str += getCommentStr('facebook','https://graph.facebook.com/' + data.comments.data[i].from.id + '/picture',
                    'https://www.facebook.com/profile.php?id=' + data.comments.data[i].from.id,
                    data.comments.data[i].from.name,
                    data.comments.data[i].message,
                    data.comments.data[i].created_time
                );
        }
        $('#Facebook_post_' + postId + "_comments").html(str).hide().slideDown("fast");
        $('.timeago').timeago();
    });
}


function loadBuzzFeed(url){
    $.ajax({
        method:'GET',
        url:'/buzz/feed/' + (url?'?paging='+encodeURIComponent(url):""),
        success:function(data){
            data = data.data;
            window.BuzzStream = [];
            for (var i=0; i<data.items.length; i++){
                var temp = getBuzzFeedEntry(data.items[i]);
                window.BuzzStream.push(temp);
            }
	    
            if (data.links.next){
		var temp = getBuzzFeedEntry(data.items[0]);
		temp.html = "<div class='FeedEntry'><a href='#' onclick='loadBuzzFeed(\""+data.links.next[0].href+"\");return false;'>Load More</a></div>";
		window.BuzzStream.push(temp);
	    }
            loadUnifiedFeed();
        }
    });
}

function loadTwitterFeed(lastId,feedType){
    if (!feedType)
        feedType = "home_timeline";
    $.ajax({
        method:'GET',
        url:'/twitter/feed/?type=' + feedType + (lastId?'?before='+lastId:''),
        success:function(data){
            data = data.data;
            window.TwitterStream= [];
            var lastId;
            for (var i=0; i<data.length; i++){
                var temp = getTwitterFeedEntry(data[i]);
                lastId = data[i].id_str;
                window.TwitterStream.push(temp);
            }
	    var temp = getTwitterFeedEntry(data[0]);
            temp.html = "<div class='FeedEntry'><a href='#' onclick='loadTwitterFeed(\""+lastId+"\");return false;'>Load More</a></div>";
            window.TwitterStream.push(temp);
            loadUnifiedFeed();
        }
    });
}

function loadUnifiedFeed(){
    var str = "";
    var arr = [{"html":""}]
    if (window.FacebookStream.length) arr = arr.concat(window.FacebookStream);
    if (window.BuzzStream.length)  arr = arr.concat(window.BuzzStream);
    if (window.TwitterStream.length) arr = arr.concat(window.TwitterStream);
    arr.sort(function(a,b){return b.time-a.time;});
    for (x in arr){
        str += arr[x].html;
    }
    $('#divUnifiedStreamContent').html(str);
    $('.timeago').timeago();
}