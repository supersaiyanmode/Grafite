$(function(){
    
});



function checkNewUserPasswordValidity(){
    var pwd = $("#txtNewUserPassword").val();
    var pwd1 = $("#txtNewUserPasswordConfirm").val();
    if (pwd == "" || pwd1 == "")
	return false;
    
    if (pwd != pwd1){
        alert("Passwords dont match!");
        return false;
    }
    var request = {"type":"setPassword","password":pwd}
    $.post('/register',request,function(data,text,jqXHR){
        data = $.parseJSON(data);
        if (data.result=='success'){
            alert("Success!");
        }else{
            alert("Error: "+data.message);
        }
    });
    return false;
}

function sendVerificationCode(){
    var email = $.trim($("#txtNewUserEmail").val());
    if (email == "")
        return false;
    
    var request = {"type":"sendVerificationCode","email":email}
    $.post('/register',request,function(data,text,jqXHR){
        data = $.parseJSON(data);
        if (data.result=='success'){
            alert("Email Sent. Follow the instructions in the Email. This page will refresh autoatically once you are done.");
            setTimeout(checkPinged,3000);
        }else{
            alert("Error: "+data.message);
        }
    });
    return false;
}

function checkPinged(){
    var request = {"type":"pinged"}
    $.post('/register',request,function(data,text,jqXHR){
        data = $.parseJSON(data);
        if (data.result=='success'){
            if (data.value){
                location.href = "/";
                return;
            }
        }else{
            console.log("Hasn't pinged till now!");
            setTimeout(checkPinged,3000);
        }
    });
    return false;
}