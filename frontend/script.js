const BASE_URL = "https://earlysteps-backend.onrender.com";

let token = null;

/* ---------------- LOGIN ---------------- */

async function requestOTP() {
  const identifier = document.getElementById("identifier").value;

  const res = await fetch(`${BASE_URL}/auth/request-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier })
  });

  if (res.ok) {
    alert("OTP generated! Check Render logs for demo.");
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

/* ---------------- PROFILE ---------------- */

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
  localStorage.setItem("selectedChild", name);
  document.getElementById("profileSection").style.display = "none";
  document.getElementById("featureSection").style.display = "block";
}

/* ---------------- QUESTIONNAIRE ---------------- */

const questions = [
  "Does your child respond to their name?",
  "Does your child maintain eye contact?",
  "Does your child point to objects?",
  "Does your child imitate actions?",
  "Does your child speak simple words like mama or bye?",
  "Does your child show interest in playing with others?",
  "Does your child follow simple instructions?"
];

function showQuestionnaire() {
  document.getElementById("featureSection").style.display = "none";
  document.getElementById("questionnaireSection").style.display = "block";

  const container = document.getElementById("questionsContainer");
  container.innerHTML = "";

  questions.forEach((q, i) => {
    container.innerHTML += `
      <p>${q}</p>
      <label><input type="radio" name="q${i}" value="yes"> Yes</label>
      <label><input type="radio" name="q${i}" value="no"> No</label>
    `;
  });
}

async function submitQuestionnaire() {
  const answers = [];

  for (let i = 0; i < questions.length; i++) {
    const selected = document.querySelector(`input[name="q${i}"]:checked`);
    if (!selected) {
      alert("Please answer all questions.");
      return;
    }
    answers.push(selected.value);
  }

  const child = localStorage.getItem("selectedChild");

  const res = await fetch(`${BASE_URL}/questionnaire`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ child, answers })
  });

  const data = await res.json();

  document.getElementById("resultText").innerText =
    "Result for " + child + ": " + data.result;
}
