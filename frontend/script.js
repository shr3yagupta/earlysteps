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
    document.getElementById("appSection").style.display = "block";
  } else {
    alert("Invalid OTP");
  }
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
