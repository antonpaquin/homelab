console.log(response);
let data = JSON.parse(response.body);
localStorage.setItem("_deviceId2", data.SessionInfo.DeviceId);
localStorage.setItem("enableAutoLogin", true);
localStorage.setItem("jellyfin_credentials", JSON.stringify({
    Servers: [
        {
            DateLastAccessed: 0,  // TODO
            LastConnectionMode: 2,
            ManualAddress: "http://jellyfin.antonpaqu.in",
            manualAddressOnly: true,
            Name: "",  // TODO
            Id: data.ServerId,
            LocalAddress: "",  // TODO
            AccessToken: data.AccessToken,
            UserId: data.User.Id
        }
    ]
}));
localStorage.setItem("user-" + data.User.Id + "-" + data.ServerId, JSON.stringify(data.User));
window.location.replace(authproxy_rd);
