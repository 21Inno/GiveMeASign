document.addEventListener("DOMContentLoaded", function() {
    chrome.storage.session.get(["IsLoggedIn","group_user","username_user"]).then((result) => {
        if(result.IsLoggedIn === "true"){
            console.log("in if true ");
            const loginForm = document.getElementById("loginLsfb-form");
            console.log(result.group_user);
            console.log(result.username_user);
            let group = result.group_user;
            let username = result.username_user;
            showLogoutButton(group,username,loginForm);
        } else {
            console.log("in else ");
            const loginForm = document.getElementById("loginLsfb-form");
            console.log("in else2 ");
            loginForm.addEventListener("submit", function(event) {
                event.preventDefault();
                const formData = new FormData(loginForm);
                fetch("http://127.0.0.1:5000/login", {
                    method: "POST",
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                    // Handle server response
                        if (data.group_user) {
                            let group = data.group_user;
                            let username = data.username_user;
                            chrome.storage.session.set({ IsLoggedIn: "true", group_user:group,username_user:username }).then(() => {
                              console.log("Value is set to " + "IsLoggedIn");
                            });
                            showLogoutButton(group,username,loginForm);
                        } else {
                            alert("Login failed. Please try again.");
                        }
                    })
                        .catch(error => {
                            console.error(error);
                        });
            });

        }


    });


});

    function showLogoutButton(group,username,loginForm) {

        document.getElementById("toDashboard").style.display = "block"
        const logoutButton = document.createElement("button");
        logoutButton.textContent = "Logout";
        logoutButton.addEventListener("click", function() {
            fetch("http://127.0.0.1:5000/logout", {
                method: "POST"
            }).then(response => response.json())
                .then(data => {
                    if (data.login_state === "false") {
                        chrome.storage.session.set({ IsLoggedIn: "false", group_user:"Public",username_user:"ano" }).then(() => {
                              console.log("Value is set to " + "IsLoggedIn");
                            });
                        showLoginForm(logoutButton);

                    } else {
                        alert("Logout failed. Please try again.");
                    }
                })
                .catch(error => {
                    console.error(error);
                });
        });
        loginForm.replaceWith(logoutButton);
    }

    function showLoginForm(logoutButton) {
        document.getElementById("toDashboard").style.display = "none"
        //document.getElementById("groud_id").style.display = "none"
        //document.getElementById("username_id").style.display = "none"
        const loginFormContainer = document.createElement("div");
        loginFormContainer.innerHTML = `
           <form id="loginLsfb-form" method="post">
            <label for="group-name">Nom du Groupe :</label>
            <input type="text" id="group-name" name="group-name"><br>
            <label for="username">Pseudo :</label>
            <input type="text" id="username" name="username"><br>
            <label for="password">Mot de passe :</label>
            <input type="password" id="password" name="password"><br>
            <input id="submitLogin" type="submit" value="Login">
            </form>
            `;
        const loginForm = loginFormContainer.querySelector("#loginLsfb-form");
        loginForm.addEventListener("submit", function(event) {
            event.preventDefault();
            const formData = new FormData(loginForm);
            fetch("http://127.0.0.1:5000/login", {
                method: "POST",
                body: formData
            }).then(response => response.json())
                .then(data => {
                    if (data.group_user) {
                        let group = data.group_user;
                        let username = data.username_user;
                        chrome.storage.session.set({ IsLoggedIn: "true", group_user:group,username_user:username }).then(() => {
                              console.log("Value is set to " + "IsLoggedIn");
                            });
                        showLogoutButton(group,username,loginForm);
                    } else {
                        alert("Login failed. Please try again.");
                    }
                })
                .catch(error => {
                    console.error(error);
                });
        });
        logoutButton.replaceWith(loginFormContainer);
    }