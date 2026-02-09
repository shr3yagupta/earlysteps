let questions = [
  "Does your child respond to their name?",
  "Does your child make eye contact?",
  "Does your child try to speak words?"
];

let current = 0;
let score = 0;

function startCheck() {
  current = 0;
  score = 0;
  document.getElementById("question").innerText = questions[current];
}

function answer(value) {
  if (value === "yes") {
    score++;
  }

  current++;

  if (current < questions.length) {
    document.getElementById("question").innerText = questions[current];
  } else {
    showResult();
  }
}

function showResult() {
  let result =
    score >= 2
      ? "✅ Development looks on track"
      : "⚠️ Consider professional screening";

  document.getElementById("question").innerText = result;
}
