
document.addEventListener("DOMContentLoaded", function() {
    /*chrome.tabs.getSelected(null, function(tab) {
      let pageTitle = tab.title;
      if (pageTitle==='Dashboard' || pageTitle==='Dashboard_admin'){
          document.getElementById('toLogin').display = 'none';
          document.getElementById('toDashboard').display = 'block';
          document.getElementById('toLogout').display = 'block';
      }if (pageTitle==='Login Popup' || pageTitle==='Login Admin'|| pageTitle==='Register Admin'){
          document.getElementById('toLogin').display = 'block';
          document.getElementById('toDashboard').display = 'none';
          document.getElementById('toLogout').display = 'none';
      }
    });*/
    fetch("http://127.0.0.1:5000/islog/")
        .then(response => response.json())
        .then(data => {
            if (data._log === 'true'){
                console.log(data._log)
                if (data._role === 'normal'){
                    console.log(data._role)
                    const username = document.createElement("span");
                    username.innerText ="Bonjour ".concat(data._username)
                    const group = document.createElement("span");
                    group.innerText ="Groupe : ".concat(data._group)
                    const div_info = document.getElementById('info')
                    const br = document.createElement('br');
                    div_info.appendChild(username)
                    div_info.appendChild(br)
                    div_info.appendChild(group)
                    document.getElementById('toLogin').style.display = 'none';
                    document.getElementById('toLoginAdmin').style.display = 'none';

                    document.getElementById('toDashboard').style.display = 'block';
                    document.getElementById('toLogout').style.display = 'block';
                }else {
                    console.log(data._role)
                    const username = document.createElement("span");
                    username.innerText ="Bonjour admin : ".concat(data._username)
                    const div_info = document.getElementById('info')
                    div_info.appendChild(username)
                    document.getElementById('toLoginAdmin').style.display = 'none';
                    document.getElementById('toLogin').style.display = 'none';

                    document.getElementById('toDashboardAdmin').style.display = 'block';
                    document.getElementById('toLogoutAdmin').style.display = 'block';
                }

            }else {
                document.getElementById('toLogin').style.display = 'block';
                document.getElementById('toLoginAdmin').style.display = 'block';

                document.getElementById('toDashboard').style.display = 'none';
                document.getElementById('toLogout').style.display = 'none';
                document.getElementById('toDashboardAdmin').style.display = 'none';
                document.getElementById('toLogoutAdmin').style.display = 'none';
            }

        })
        .catch(error => {console.error(error);})


});