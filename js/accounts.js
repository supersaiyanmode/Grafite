$(function(){
    $(':checkbox').iphoneStyle();
    
    
    $('#txtURLDP').change(function(){
	$('#imgDPPreview').attr('src',$.trim($('#txtURLDP').val()));
    });
    
    $('.SocialNetworkDPs').click(function(){
	var url = $(this).attr('src');
	$('#imgDPPreview').attr('src',url);
    });
    
    showSettingsDiv('divProfileSettings');
});

function setDP(){
    var url = $('#imgDPPreview').attr('src');
    if (url[0]=='/')
	return false;
    var request = {
	"type":"settings",
	"subtype":"displaypicture",
	"dpUrl": url
    };
    $('#imgDPPreview').attr('src','/images/ajax-loader.gif');
    $.post('/account',request,function(data,text,jqXHR){
	data = $.parseJSON(data);
	console.log(data);
	if (data['result']=='success'){
	    var url = data['url'] + "?cache=" + new Date().getTime();
	    $('#divLoginPopup').show();
	    $(".userDisplayPicture").each(function(){
		$(this).fadeOut(function() { 
		    $(this).load(function() {
			$(this).fadeIn();
			setTimeout(function(){$('#divLoginPopup').hide();},3000);
		    }); 
		    $(this).attr("src", url);
		});
	    });
	}else{
	    alert("Error trying to change DP, please re-check URL or try again later!");
	}
    });
    return false;
}

function setNickname(){
    var nickname = $('#txtNickname').val();
    var request = {
	"type":"settings",
	"subtype":"nickname",
	"nickname":nickname
    };
    $.post('/account',request,function(data,text,jqXHR){
	data = $.parseJSON(data);
	console.log(data);
	if (data['result']=='success'){
	    $('.userNickname').each(function(){
		$(this).html(nickname);
	    })
	}else{
	    alert(data['message']);
	}
    });
    return false;
}

function showSettingsDiv(divId){
    $("#divProfileSettings").hide();
    $("#divGrafiteSettings").hide();
    $("#divAccountSettings").hide();
    
    $("#" + divId).fadeIn();
}