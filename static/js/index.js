function editUser() {
    var username = document.querySelector("#username").value;
    var email = document.querySelector("#email").value;

    document.querySelector("#username-taken").classList.add("d-none");
    document.querySelector("#edit-user-error-occurred").classList.add("d-none");
    
    username === "" ? document.querySelector("#username").classList.add("is-invalid") : document.querySelector("#username").classList.remove("is-invalid");
    
    if (username === "") return;
    
    document.querySelector("#save-user").classList.add("d-none");
    document.querySelector("#save-user-loading").classList.remove("d-none");

    fetch("/api/user",
        {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "PUT",
            body: JSON.stringify({username: username, email: email})
        })
    .then((res) => { return res.json() })
    .then((json) => {
        if (json.status == "ok") {
            window.location.reload();
        } else if (json.status == "error" && json.error == "username_taken") {
            document.querySelector("#username-taken").classList.remove("d-none");
        } else if (json.status == "error") {
            document.querySelector("#edit-user-error-occurred").classList.remove("d-none");
        }

        document.querySelector("#save-user").classList.remove("d-none");
        document.querySelector("#save-user-loading").classList.add("d-none");
    })
    .catch((res) => {
        document.querySelector("#edit-user-error-occurred").classList.remove("d-none");
        document.querySelector("#save-user").classList.remove("d-none");
        document.querySelector("#save-user-loading").classList.add("d-none");
    })
}

function changePassword() {
    var password = document.querySelector("#password").value;
    var retypePassword = document.querySelector("#retype-password").value;

    password == "" ? document.querySelector("#password").classList.add("is-invalid") : document.querySelector("#password").classList.remove("is-invalid");
    retypePassword == "" ? document.querySelector("#retype-password").classList.add("is-invalid") : document.querySelector("#retype-password").classList.remove("is-invalid");
    
    if (password === "" || retypePassword === "") return;
    
    password === retypePassword ? document.querySelector("#passwords-not-same").classList.add("d-none") : document.querySelector("#passwords-not-same").classList.remove("d-none");
    
    if (password !== retypePassword) return;

    document.querySelector("#change-password-error-occurred").classList.add("d-none");
    
    document.querySelector("#change-password").classList.add("d-none");
    document.querySelector("#change-password-loading").classList.remove("d-none");

    fetch("/api/user/password",
        {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "PUT",
            body: JSON.stringify({password: password})
        })
    .then((res) => { return res.json() })
    .then((json) => {
        if (json.status == "ok") {
            window.location.reload();
        } else if (json.status == "error") {
            document.querySelector("#change-password-error-occurred").classList.remove("d-none");
        }

        document.querySelector("#change-password").classList.remove("d-none");
        document.querySelector("#change-password-loading").classList.add("d-none");
    })
    .catch((res) => {
        document.querySelector("#change-password-error-occurred").classList.remove("d-none");
        document.querySelector("#change-password").classList.remove("d-none");
        document.querySelector("#change-password-loading").classList.add("d-none");
    })
}

function enable2FA() {
    document.querySelector("#enable-2fa").classList.add("d-none");
    document.querySelector("#enable-2fa-loading").classList.remove("d-none");

    fetch("/api/user/2fa",
        {
            method: "POST",
        })
    .then(() => { window.location.reload(); });
}

function disable2FA() {
    document.querySelector("#disable-2fa").classList.add("d-none");
    document.querySelector("#disable-2fa-loading").classList.remove("d-none");

    fetch("/api/user/2fa",
        {
            method: "DELETE",
        })
    .then(() => { window.location.reload(); });
}

function powerAction(evt) {
    var deviceID = evt.currentTarget.parentElement.parentElement.getAttribute("device-id");
    var actionName = evt.currentTarget.className.match(/device-(\w+)-button/)[1];

    if (!(["wake", "shutdown", "reboot", "logout", "sleep", "hibernate"].includes(actionName))) return;

    evt.currentTarget.classList.add("d-none");
    evt.currentTarget.parentElement.querySelector(`.device-${actionName}-loading-button`).classList.remove("d-none");

    fetch(`/api/device/${deviceID}/${actionName}`, { method: "POST" })
    .then((res) => {
        var deviceID = res.url.match(/\/api\/device\/(\w+)\/(\w+)/)[1];
        var actionName = res.url.match(/\/api\/device\/(\w+)\/(\w+)/)[2];

        document.querySelector(`[device-id="${deviceID}"]`).querySelector(`.device-${actionName}-button`).classList.remove("d-none");
        document.querySelector(`[device-id="${deviceID}"]`).querySelector(`.device-${actionName}-loading-button`).classList.add("d-none");
    });
}

document.querySelector("#save-user").addEventListener("click", editUser);
document.querySelector("#change-password").addEventListener("click", changePassword);

if (document.querySelector("#status-2fa").innerHTML === "enabled") (() => {
    document.querySelector("#disable-2fa").addEventListener("click", disable2FA);

    new QRCode(document.querySelector("#qr-2fa"), {
        text: document.querySelector("#totp-url").innerHTML,
        width: 256,
        height: 256,
        colorDark : "#000000",
        colorLight : "#ffffff",
        correctLevel : QRCode.CorrectLevel.H
    });
})();
else (() => {
    document.querySelector("#enable-2fa").addEventListener("click", enable2FA);
})();

document.querySelectorAll([".device-wake-button", ".device-shutdown-button", ".device-reboot-button", ".device-logout-button", ".device-sleep-button", ".device-hibernate-button"]).forEach(e => { e.addEventListener("click", powerAction); });
