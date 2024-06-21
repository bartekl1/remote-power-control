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

function addDevice() {    
    document.querySelector("#add-device").classList.add("d-none");
    document.querySelector("#add-device-loading").classList.remove("d-none");

    fetch("/api/device",
        {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "POST",
            body: JSON.stringify({
                name: document.querySelector("#add-device-name").value,
                mac_address: document.querySelector("#add-device-mac-address").value,
                ip_address: document.querySelector("#add-device-ip-address").value,
                ssh_username: document.querySelector("#add-device-ssh-username").value,
                ssh_key_type: document.querySelector("#add-device-ssh-key-type").value,
                ssh_key: document.querySelector("#add-device-ssh-key").value,
                ssh_password: document.querySelector("#add-device-ssh-password").value,
                shutdown_command: document.querySelector("#add-device-shutdown-command").value,
                reboot_command: document.querySelector("#add-device-reboot-command").value,
                logout_command: document.querySelector("#add-device-logout-command").value,
                sleep_command: document.querySelector("#add-device-sleep-command").value,
                hibernate_command: document.querySelector("#add-device-hibernate-command").value,
            })
        })
    .then(() => { window.location.reload(); });
}

function editDevice() {    
    document.querySelector("#edit-device").classList.add("d-none");
    document.querySelector("#edit-device-loading").classList.remove("d-none");

    fetch(`/api/device/${document.querySelector("#edit-device-id").innerText}`,
        {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "PUT",
            body: JSON.stringify({
                name: document.querySelector("#edit-device-name").value,
                mac_address: document.querySelector("#edit-device-mac-address").value,
                ip_address: document.querySelector("#edit-device-ip-address").value,
                shutdown_command: document.querySelector("#edit-device-shutdown-command").value,
                reboot_command: document.querySelector("#edit-device-reboot-command").value,
                logout_command: document.querySelector("#edit-device-logout-command").value,
                sleep_command: document.querySelector("#edit-device-sleep-command").value,
                hibernate_command: document.querySelector("#edit-device-hibernate-command").value,
            })
        })
    .then(() => { window.location.reload(); });
}

function editDeviceCredentials() {    
    document.querySelector("#edit-device-credentials").classList.add("d-none");
    document.querySelector("#edit-device-credentials-loading").classList.remove("d-none");

    fetch(`/api/device/${document.querySelector("#edit-device-credentials-id").innerText}/credentials`,
        {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "PUT",
            body: JSON.stringify({
                ssh_username: document.querySelector("#edit-device-credentials-ssh-username").value,
                ssh_key_type: document.querySelector("#edit-device-credentials-ssh-key-type").value,
                ssh_key: document.querySelector("#edit-device-credentials-ssh-key").value,
                ssh_password: document.querySelector("#edit-device-credentials-ssh-password").value,
            })
        })
    .then(() => { window.location.reload(); });
}

function deleteDevice() {    
    document.querySelector("#delete-device").classList.add("d-none");
    document.querySelector("#delete-device-loading").classList.remove("d-none");

    fetch(`/api/device/${document.querySelector("#delete-device-id").innerText}`, { method: "DELETE" })
    .then(() => { window.location.reload(); });
}

function prepareRenameToken(evt) {
    evt.currentTarget.classList.add("d-none");
    evt.currentTarget.parentElement.parentElement.parentElement.querySelector(".token-name-div").classList.add("d-none");
    evt.currentTarget.parentElement.parentElement.parentElement.querySelector(".token-rename-div").classList.remove("d-none");
    evt.currentTarget.parentElement.parentElement.parentElement.querySelector(".token-rename-input").value = evt.currentTarget.parentElement.parentElement.parentElement.querySelector(".token-name").innerText;
}

function cancelRenameToken(evt) {
    evt.currentTarget.parentElement.parentElement.parentElement.parentElement.querySelector(".token-rename-div").classList.add("d-none");
    evt.currentTarget.parentElement.parentElement.parentElement.parentElement.querySelector(".token-rename-button").classList.remove("d-none");
    evt.currentTarget.parentElement.parentElement.parentElement.parentElement.querySelector(".token-name-div").classList.remove("d-none");
}

function renameToken(evt) {
    evt.currentTarget.disabled = true;
    evt.currentTarget.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    evt.currentTarget.parentElement.parentElement.querySelector(".token-rename-cancel").disabled = true;
    evt.currentTarget.parentElement.parentElement.parentElement.parentElement.querySelector(".token-name").innerHTML = evt.currentTarget.parentElement.parentElement.querySelector(".token-rename-input").value;

    fetch(`/api/user/access_tokens/${evt.currentTarget.parentElement.parentElement.parentElement.parentElement.querySelector(".token-id").innerText}`,
        {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "PUT",
            body: JSON.stringify({
                name: evt.currentTarget.parentElement.parentElement.querySelector(".token-rename-input").value
            })
        })
    .then((res) => {
        document.querySelector(`[token-id="${res.url.match(/\/api\/user\/access_tokens\/(\w+)/)[1]}"`).querySelector(".token-rename-div").classList.add("d-none");
        document.querySelector(`[token-id="${res.url.match(/\/api\/user\/access_tokens\/(\w+)/)[1]}"`).querySelector(".token-rename-button").classList.remove("d-none");
        document.querySelector(`[token-id="${res.url.match(/\/api\/user\/access_tokens\/(\w+)/)[1]}"`).querySelector(".token-name-div").classList.remove("d-none");
        document.querySelector(`[token-id="${res.url.match(/\/api\/user\/access_tokens\/(\w+)/)[1]}"`).querySelector(".token-rename-submit").disabled = false;
        document.querySelector(`[token-id="${res.url.match(/\/api\/user\/access_tokens\/(\w+)/)[1]}"`).querySelector(".token-rename-submit").innerHTML = '<i class="bi bi-check-lg"></i>';
        document.querySelector(`[token-id="${res.url.match(/\/api\/user\/access_tokens\/(\w+)/)[1]}"`).querySelector(".token-rename-cancel").disabled = false;
    });
}

function deleteToken(evt) {
    evt.currentTarget.classList.add("d-none");
    evt.currentTarget.parentElement.parentElement.querySelector(".token-delete-loading-button").classList.remove("d-none");

    fetch(`/api/user/access_tokens/${evt.currentTarget.parentElement.parentElement.parentElement.querySelector(".token-id").innerText}`, { method: "DELETE" })
    .then((res) => { document.querySelector(`[token-id="${res.url.match(/\/api\/user\/access_tokens\/(\w+)/)[1]}"`).remove(); });
}

function createToken(evt) {
    evt.currentTarget.disabled = true;
    evt.currentTarget.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    fetch("/api/user/access_tokens",
        {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "POST",
            body: JSON.stringify({
                name: document.querySelector("#new-token-name").value
            })
        })
    .then((res) => { return res.json(); })
    .then((json) => {
        document.querySelector("#new-token-name").value = "";

        var tokenFrame = document.createElement("div");
        tokenFrame.classList.add("token-frame");
        tokenFrame.setAttribute("token-id", json.token_id);
        tokenFrame.innerHTML = `<span class="token-id d-none">{{ token_id }}</span>
        <div class="d-flex">
            <div class="token-name-div">
                <span class="token-name fs-5">{{ token_name }}</span>
            </div>

            <div class="token-rename-div d-none">
                <div class="input-group">
                    <input type="text" class="form-control token-rename-input">
                    <button class="btn btn-outline-secondary token-rename-cancel">
                        <i class="bi bi-x-lg"></i>
                    </button>
                    <button class="btn btn-outline-primary token-rename-submit">
                        <i class="bi bi-check-lg"></i>
                    </button>
                </div>
            </div>

            <div class="ms-auto">
                <button class="btn btn-secondary btn-sm token-rename-button" data-bs-toggle="tooltip" data-bs-placement="bottom" data-bs-original-title="Rename">
                    <i class="bi bi-pencil-fill"></i>
                </button>
                <button class="btn btn-danger btn-sm token-delete-button" data-bs-toggle="tooltip" data-bs-placement="bottom" data-bs-original-title="Delete">
                    <i class="bi bi-trash-fill"></i>
                </button>
                <button class="btn btn-danger btn-sm token-delete-loading-button d-none" disabled>
                    <span class="spinner-border spinner-border-sm"></span>
                </button>
            </div>
        </div>

        <div class="input-group mt-2">
            <input type="text" class="form-control new-token">
            <button class="btn btn-outline-primary new-token-copy">
                <i class="bi bi-clipboard"></i>
            </button>
        </div>
        `;

        tokenFrame.querySelector(".token-id").innerHTML = json.token_id;
        tokenFrame.querySelector(".token-name").innerHTML = json.name;
        tokenFrame.querySelector(".new-token").value = json.token;

        tokenFrame.querySelector(".token-rename-button").addEventListener("click", prepareRenameToken);
        tokenFrame.querySelector(".token-rename-cancel").addEventListener("click", cancelRenameToken);
        tokenFrame.querySelector(".token-rename-submit").addEventListener("click", renameToken);
        tokenFrame.querySelector(".token-delete-button").addEventListener("click", deleteToken);

        document.querySelector("#access-tokens").append(tokenFrame);

        document.querySelector("#create-access-token-button").disabled = false;
        document.querySelector("#create-access-token-button").innerHTML = '<i class="bi bi-plus-lg"></i>';

        tokenFrame.querySelector(".new-token-copy").addEventListener("click", (evt) => {
            navigator.clipboard.writeText(
                evt.currentTarget.parentElement.querySelector("input").value
            );
    
            evt.currentTarget.innerHTML = '<i class="bi bi-clipboard-check"></i>';
    
            setTimeout(
                (el) => {
                    el.innerHTML = '<i class="bi bi-clipboard"></i>';
                },
                2000,
                evt.currentTarget
            );
        });
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

document.querySelector("#add-device-cancel").addEventListener("click", () => {
    document.querySelectorAll([
        "#add-device-name",
        "#add-device-mac-address",
        "#add-device-ip-address",
        "#add-device-ssh-username",
        "#add-device-ssh-key-type",
        "#add-device-ssh-key",
        "#add-device-ssh-password",
        "#add-device-shutdown-command",
        "#add-device-reboot-command",
        "#add-device-logout-command",
        "#add-device-sleep-command",
        "#add-device-hibernate-command",
    ]).forEach(e => {
        e.value = "";
    });
});

document.querySelector("#add-device").addEventListener("click", addDevice);
document.querySelector("#edit-device").addEventListener("click", editDevice);
document.querySelector("#edit-device-credentials").addEventListener("click", editDeviceCredentials);
document.querySelector("#delete-device").addEventListener("click", deleteDevice);

document.querySelectorAll(".device-delete-button").forEach((e) => {
    e.addEventListener("click", (evt) => {
        document.querySelector("#delete-device-name").innerHTML = evt.currentTarget.parentElement.parentElement.querySelector(".device-name").innerText;
        document.querySelector("#delete-device-id").innerHTML = evt.currentTarget.parentElement.parentElement.getAttribute("device-id");
    });
});

document.querySelectorAll(".device-edit-button").forEach((e) => {
    e.addEventListener("click", (evt) => {
        document.querySelector("#edit-device-id").innerHTML = evt.currentTarget.parentElement.parentElement.getAttribute("device-id");
        ["name", "mac-address", "ip-address", "shutdown-command", "reboot-command", "logout-command", "sleep-command", "hibernate-command"].forEach(propertyName => {
            document.querySelector(`#edit-device-${propertyName}`).value = evt.currentTarget.parentElement.parentElement.querySelector(`.device-property-${propertyName}`).innerText;
        });
    });
});

document.querySelectorAll(".device-edit-credentials-button").forEach((e) => {
    e.addEventListener("click", (evt) => {
        document.querySelector("#edit-device-credentials-id").innerHTML = evt.currentTarget.parentElement.parentElement.getAttribute("device-id");
        ["ssh-username", "ssh-key-type", "ssh-key", "ssh-password"].forEach(propertyName => {
            document.querySelector(`#edit-device-credentials-${propertyName}`).value = "";
        });
    });
});

document.querySelectorAll(".token-rename-button").forEach((e) => { e.addEventListener("click", prepareRenameToken); });
document.querySelectorAll(".token-rename-cancel").forEach((e) => { e.addEventListener("click", cancelRenameToken); });
document.querySelectorAll(".token-rename-submit").forEach((e) => { e.addEventListener("click", renameToken); });
document.querySelectorAll(".token-delete-button").forEach((e) => { e.addEventListener("click", deleteToken); });
document.querySelector("#create-access-token-button").addEventListener("click", createToken);
