function startCheck() {
  fetch("http://127.0.0.1:8000/")
    .then(res => res.json())
    .then(data => alert(data.message))
    .catch(() => alert("Backend not reachable"));
}
