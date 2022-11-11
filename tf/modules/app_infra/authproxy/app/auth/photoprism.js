console.log(response);
let data = JSON.parse(response.body);
localStorage.setItem("data", JSON.stringify(data.data));
localStorage.setItem("session_id", data.id);
window.location.replace(authproxy_rd);
