// Listen for messages from the server
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    if (message.isLoggedIn) {
        // Update the popup with the new content

      document.getElementById('log_link').href = "http://127.0.0.1:5000/logout";
      document.getElementById('log_link').innerHTML = 'Se déconnecter';
    }else {
      // User is not logged in, update popup HTML
    document.getElementById('log_link').href = "http://127.0.0.1:5000/login";
    document.getElementById('log_link').innerHTML = 'Se connecter';
    }
});

