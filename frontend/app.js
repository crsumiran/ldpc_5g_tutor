const specEl = document.getElementById("spec");
const outEl = document.getElementById("out");
const history = [];

const imgEl = document.getElementById("img");

function compressImage(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        const maxDim = 1024;
        let { width, height } = img;
        const scale = Math.min(1, maxDim / Math.max(width, height));
        width = Math.round(width * scale);
        height = Math.round(height * scale);
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        canvas.getContext("2d").drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL("image/png").split(",")[1]);
      };
      img.onerror = reject;
      img.src = reader.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function load() {
  const r = await fetch("/api/lessons/and2");
  const j = await r.json();
  specEl.textContent = j.spec;
}
load();

document.getElementById("send").onclick = async () => {
  const message = document.getElementById("msg").value;
  const code = document.getElementById("code").value;
  const body = { lesson_id: "and2", message, code, history };
  if (imgEl.files && imgEl.files[0]) {
    body.image = await compressImage(imgEl.files[0]);
  }
  const r = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json();
  history.push({ role: "user", content: message });
  history.push({ role: "assistant", content: j.reply });
  outEl.textContent =
    (j.passed ? "PASSED\n" : "NOT PASSED\n") +
    j.reply +
    (j.executor_output ? "\n\n--- executor ---\n" + j.executor_output : "");
};