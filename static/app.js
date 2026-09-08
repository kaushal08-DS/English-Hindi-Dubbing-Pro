const form = document.getElementById("uploadForm");
const input = document.getElementById("video");
const drop = document.getElementById("drop");
const title = document.getElementById("title");
const meta = document.getElementById("meta");
const start = document.getElementById("start");
const progressPanel = document.getElementById("progressPanel");
const stage = document.getElementById("stage");
const message = document.getElementById("message");
const pct = document.getElementById("pct");
const bar = document.getElementById("bar");
const result = document.getElementById("result");

input.addEventListener("change", showFile);

function showFile() {
  if (!input.files.length) return;
  const f = input.files[0];
  title.textContent = f.name;
  meta.textContent = `${(f.size / 1024 / 1024).toFixed(1)} MB`;
}

["dragenter", "dragover"].forEach(evt => {
  drop.addEventListener(evt, e => {
    e.preventDefault();
    drop.classList.add("drag");
  });
});

["dragleave", "drop"].forEach(evt => {
  drop.addEventListener(evt, e => {
    e.preventDefault();
    drop.classList.remove("drag");
  });
});

drop.addEventListener("drop", e => {
  if (e.dataTransfer.files.length) {
    input.files = e.dataTransfer.files;
    showFile();
  }
});

form.addEventListener("submit", async e => {
  e.preventDefault();

  if (!input.files.length) {
    alert("Choose an English video first.");
    return;
  }

  start.disabled = true;
  start.textContent = "Uploading…";
  progressPanel.classList.remove("hidden");
  result.innerHTML = "";

  try {
    const fd = new FormData(form);
    const r = await fetch("/api/jobs", { method: "POST", body: fd });
    const data = await r.json();

    if (!r.ok) throw new Error(data.error || "Upload failed.");

    poll(data.job_id);
  } catch (err) {
    start.disabled = false;
    start.textContent = "Start AI dubbing";
    stage.textContent = "Error";
    message.textContent = err.message;
  }
});

async function poll(jobId) {
  try {
    const r = await fetch(`/api/jobs/${jobId}`);
    const job = await r.json();

    const p = Number(job.progress || 0);
    stage.textContent = job.stage || "Processing";
    message.textContent = job.message || "";
    pct.textContent = `${p}%`;
    bar.style.width = `${p}%`;

    if (job.status === "completed") {
      start.disabled = false;
      start.textContent = "Dub another video";
      result.innerHTML = `
        <div class="done">
          <div class="success">Completed</div>
          <a href="/api/jobs/${jobId}/download">Download Hindi dubbed MP4</a>
        </div>`;
      return;
    }

    if (job.status === "failed") {
      start.disabled = false;
      start.textContent = "Try again";
      result.innerHTML = `<div class="error">${escapeHtml(job.message || "Processing failed.")}</div>`;
      return;
    }

    setTimeout(() => poll(jobId), 2500);
  } catch (err) {
    setTimeout(() => poll(jobId), 4000);
  }
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, ch => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[ch]));
}
