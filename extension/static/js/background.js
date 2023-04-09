//--------------Add button in context menu-----------------
function createPopup(selectionText) {
    (async () => {
        const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
        const response = await chrome.tabs.sendMessage(tab.id, {_action: "createPopup",mot:selectionText});
        console.log(response);
})();
}


chrome.runtime.onInstalled.addListener(function() {

    chrome.contextMenus.create({
        id: "translate",
        title: "(GiveMeASign) Traduire le mot :  \"%s\"",
        contexts: ["all"],
    });
});

chrome.contextMenus.onClicked.addListener(function(info, tab) {
    if (tab) {
        if (info.menuItemId === "translate"){
            createPopup(info.selectionText);
        }
        /*if (info.menuItemId === "linkToDict"){
            openNewTab();
        }*/
    }
});


//-----------------------------------------------------
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  if (message.message) {
    chrome.action.setPopup({ popup: "popup-loggedin.html" });
  }
});
