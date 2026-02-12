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
    alert("OTP generated! Check backend logs.");
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
    headers: { "Authorization": `Bearer ${token}` }
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
      <br><br>
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

  document.getElementById("resultText").innerHTML = `
    <h3>Status: ${data.status}</h3>
    <p><strong>AI Developmental Pattern Analysis:</strong></p>
    <p>${data.summary}</p>
    <p style="color:gray;"><strong>${data.reassurance}</strong></p>

    <h4>Suggested Next Steps:</h4>
    <ul>${data.next_steps.map(step => `<li>${step}</li>`).join("")}</ul>

    <p style="color:blue;"><strong>Follow-up:</strong> ${data.follow_up}</p>

    <h4>National Child Helpline (India): 1098</h4>
  `;

  loadNearbySupport();
}

/* ---------------- LOCATION SUPPORT ---------------- */

function getUserLocation() {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      pos => resolve({
        lat: pos.coords.latitude,
        lng: pos.coords.longitude
      }),
      () => reject("Location denied")
    );
  });
}

async function loadNearbySupport() {
  try {
    const location = await getUserLocation();

    const res = await fetch(
      `${BASE_URL}/nearby-support?lat=${location.lat}&lng=${location.lng}`
    );

    const data = await res.json();

    let html = "<h4>Nearby Support Centers:</h4><ul>";
    data.forEach(place => {
      html += `<li><strong>${place.name}</strong><br>${place.address}</li>`;
    });
    html += "</ul>";

    document.getElementById("resultText").innerHTML += html;

  } catch (error) {
    console.log(error);
  }
}

/* ---------------- HISTORY + TREND GRAPH ---------------- */

async function loadHistory() {

  const child = localStorage.getItem("selectedChild");

  const res = await fetch(`${BASE_URL}/history/${child}`, {
    headers: { "Authorization": `Bearer ${token}` }
  });

  const data = await res.json();

  const container = document.getElementById("historySection");
  container.innerHTML = "<h3>Previous Reports</h3>";

  data.forEach(entry => {
    container.innerHTML += `
      <div style="border:1px solid #ccc; padding:10px; margin:10px;">
        <strong>${entry.status}</strong><br>
        ${entry.summary}<br>
        <small>${entry.timestamp}</small>
      </div>
    `;
  });

  drawTrendChart(data);
}

function drawTrendChart(history) {

  const labels = history.map((h, i) => "Check " + (i + 1));

  const scoreMap = {
    "On Track": 1,
    "Needs Monitoring": 2,
    "Extra Support Recommended": 3
  };

  const values = history.map(h => scoreMap[h.status]);

  new Chart(document.getElementById("trendChart"), {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Development Trend',
        data: values,
        borderColor: 'blue',
        fill: false
      }]
    },
    options: {
      scales: {
        y: {
          min: 1,
          max: 3,
          ticks: {
            callback: function(value) {
              return ["On Track", "Needs Monitoring", "Extra Support"][value-1];
            }
          }
        }
      }
    }
  });
}
