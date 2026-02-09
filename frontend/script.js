let answers = [];

function answerYes() {
  answers.push("yes");
  sendToBackend();
}

function answerNo() {
  answers.push("no");
  sendToBackend();
}

async function sendToBackend() {
  const resultEl = document.getElementById("result");
  resultEl.innerText = "Checking...";

  try {
    const res = await fetch("https://earlysteps-backend.onrender.com/check", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ answers })
    });

    const data = await res.json();
    resultEl.innerText = data.result;
  } catch (err) {
    resultEl.innerText = "Backend not reachable";
  }
}

