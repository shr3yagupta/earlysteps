const BASE_URL = "https://earlysteps-backend.onrender.com";

let token = null;
let answers = [];

async function requestOTP() {
  const identifier = document.getElementById("identifier").value;

  const res = await fetch(`${BASE_URL}/auth/request-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier })
  });

  if (res.ok) {
    alert("OTP sent! Check Render logs for demo.");
    document.getElementById("otpBox").style.display = "block";
  } else {
    alert("Error sending OTP");
  }
}

async function verifyOTP() {
  const identifier = document.getElementById("identifier").value;
  const otp = document.getElementById("otpInput").value;

  const res = await fetch(`${BASE_URL}/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier, otp })
  });

  const data = await res.json();

  if (res.ok) {
    token = data.token;
    alert("Login successful!");
    document.getElementById("loginSection").style.display = "none";
    document.getElementById("profileSection").style.display = "block";
loadProfiles();

  } else {
    alert("Invalid OTP");
  }
}

async function createProfile() {
  const name = document.getElementById("childName").value;
  const age = document.getElementById("childAge").value;

  await fetch(`${BASE_URL}/profiles`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ name, age })
  });

  loadProfiles();
}

async function loadProfiles() {
  const res = await fetch(`${BASE_URL}/profiles`, {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });

  const data = await res.json();
  const list = document.getElementById("profileList");
  list.innerHTML = "";

  data.forEach(p => {
    const li = document.createElement("li");
    li.innerHTML = `${p.name} (Age: ${p.age})
      <button onclick="selectProfile('${p.name}')">Select</button>`;
    list.appendChild(li);
  });
}

function selectProfile(name) {
  alert("Selected profile: " + name);
  document.getElementById("profileSection").style.display = "none";
  document.getElementById("appSection").style.display = "block";
}

async function submitAnswer(answer) {
  answers.push(answer);

  const res = await fetch(`${BASE_URL}/check`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ answers })
  });

  const data = await res.json();

  if (res.ok) {
    document.getElementById("result").innerText = data.result;
  } else {
    document.getElementById("result").innerText = "Unauthorized. Please login.";
  }
}
