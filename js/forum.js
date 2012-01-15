$(function(){
    jQuery.error = console.error;
    
    //Create a New Topic Post button
    $('#btnCreateNewPost').click(function(){
	var request = {"text":$.trim($('#txtAreaCreateNewPost').val()),
			"type":"CreateThreadPost"
	}
	$.post('/forum',request,function(data,text,jqXHR){
	    data = $.parseJSON(data);
	    if (data['result']=='success'){
		    prevHTML = $('#divThreadsContainer').html()
		    $('#divThreadsContainer').html(data['html'] + "\n" + prevHTML)
		    
		    $('#'+data['divId']).hide();
		    $('#'+data['divId']).slideDown();
	    }else{
		    alert("Error");
	    }
	});
	$('#txtAreaCreateNewPost').val("");
	return false;
    });
});

//Comment post button
function postReply(threadId){
    var request = {
	"text":$.trim($('#txtPostComment_threadId_'+threadId).val()),
	"type":"ReplyPost",
	"threadId":''+threadId
    }
    $.post('/forum',request,function(data,text,jqXHR){
	data = $.parseJSON(data);
	if (data['result']=='success'){
		var obj = $('#tblThreadComment_'+threadId+' tr:last');
		
		if (obj.prev().length)
		    obj.prev().after(data['html']);
		else{
		    console.log("First!");
		    var prev = obj.html();
		    obj.html(data['html']+prev);
		}
		
		$('#'+data['divId']).hide();
		$('#'+data['divId']).fadeIn("slow");

	}else{
		alert("Error");
	}
    });
    $('#txtPostComment_threadId_'+threadId).val("")
    return false;
}

function deletePost(postId){
    var request = {
	"type":"DeletePost",
	"postId":''+postId
    };
    $.post('/forum',request,function(data,text,jqXHR){
	data = $.parseJSON(data);
	if (data['result']=='success'){
	    if (data['deleteType'].toLowerCase() == 'thread')
		$('#'+data['toDelete']).slideUp();
	    else
		$('#'+data['toDelete']).fadeOut();
	}else{
	    alert("Error");
	}
    });
    return false;
}