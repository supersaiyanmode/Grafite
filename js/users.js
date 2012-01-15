$(function(){
    $('#imgSearchLoading').hide();

    $('#txtSearch').change(function(){
	$('#imgSearchLoading').show();
	$.ajax({
		type: 'GET',
		url: '/users/?type=search&q='+encodeURIComponent($.trim($('#txtSearch').val())),
		success: function(data){
			console.log(data);
			var response = $.parseJSON(data);
			if (response.result=='success'){
			    loadUsers(response.data);
			}
			$('#imgSearchLoading').hide();
		}
	});
    });
});

function loadUsers(users){
    str = "";
    for (var i=0; i<users.length; i++){
	str+= "\
	<a href='"+users[i].url+"'>\
	<img src='"+users[i].dp+"' width='30px' height='30px'/>\
	<span class='profileBlock'>"+users[i].nickname+"</span>\
	</a>\n";
    }
    $('#divSearchResults').html(str);
}