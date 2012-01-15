$(function(){
    $(':checkbox').iphoneStyle();
    getFacebookDetails();
    getBuzzDetails();
    getTwitterDetails();
});

function getFacebookDetails(){
    $.ajax({
	type: 'POST',
	url: '/facebook/status/',
	success: function(data){
	    data = $.parseJSON(data)
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
	    data = $.parseJSON(data)
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
    services = toPost.join(',')
    $.ajax({
		type: 'POST',
		url: '/status',
		data: {"status":text,"services":services,"alt":"json"},
		success: function(data){
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

function followUser(service){
    $.ajax({
	type: 'GET',
	url: '/' + service.toLowerCase() + "/follow/?gUser=" + gUserId,
	success: function(data){
		console.log(data);
		data = $.parseJSON(data);
		if (data.result == 'success'){
		    $('#span'+ service + 'RelationTrue').toggle("fast");
		    $('#span'+ service + 'RelationFalse').toggle("fast");
		}
	}
    });
}

function unfollowUser(service){
    $.ajax({
	type: 'GET',
	url: '/' + service.toLowerCase() + "/unfollow/?gUser=" + gUserId,
	success: function(data){
		console.log(data);
		data = $.parseJSON(data);
		if (data.result == 'success'){
		    $('#span'+ service + 'RelationTrue').toggle("fast");
		    $('#span'+ service + 'RelationFalse').toggle("fast");
		}
	}
    });
}