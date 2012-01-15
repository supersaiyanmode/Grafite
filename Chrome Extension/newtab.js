backgroundPage = chrome.extension.getBackgroundPage();
function loadTickerData(){
    $('#divTicker').html(backgroundPage.getFacebookTickerData());
}
$(function(){
    //setInterval(loadTickerData,20000);
    loadTickerData();
});