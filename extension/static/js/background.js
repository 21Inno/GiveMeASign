//--------------Add button in context menu-----------------
function createPopup(selectionText) {
    (async () => {
        const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
        const response = await chrome.tabs.sendMessage(tab.id, {_action: "createPopup",mot:selectionText});
        console.log(response);
})();
}

function openNewTab(info,tab) {

    chrome.tabs.create({ url: "https://dico.corpus-lsfb.be/"});
}

chrome.runtime.onInstalled.addListener(function() {

    chrome.contextMenus.create({
        id: "translate",
        title: "Traduire le mot :  \"%s\"",
        contexts: ["all"],
    });
});

var contextMenuLinkToDict = {
    "id" : "linkToDict",
    "title" :"Aller sur le dictionnaire LSFB",
    "contexts" : ["selection"],

};
chrome.runtime.onInstalled.addListener(function() {
    chrome.contextMenus.create(contextMenuLinkToDict);
});

chrome.contextMenus.onClicked.addListener(function(info, tab) {
    if (tab) {
        if (info.menuItemId === "translate"){


            /*chrome.scripting.executeScript({
              target : {tabId : tab.id},
              func : getSurroundingText,
              args : [ info.selectionText ],
            })
            .then(() => console.log("injected a function"));*/
            createPopup(info.selectionText);

        }
        if (info.menuItemId === "linkToDict"){
            openNewTab();
        }
    }
});


//-----------------------------------------------------
