// static/js/vote.js
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureBtn = document.getElementById('capture');
const voteBtn = document.getElementById('voteBtn');
const preview = document.getElementById('preview');
const status = document.getElementById('status');
const candidatesDiv = document.getElementById('candidates');

let capturedDataUrl = null;
let selectedCandidateId = null;

async function loadCandidates(){
  const r = await fetch('/api/candidates');
  const arr = await r.json();
  candidatesDiv.innerHTML = arr.map(c => `
    <label><input type="radio" name="candidate" value="${c.id}"> ${c.name} (${c.party || ''})</label><br>
  `).join('');
  document.querySelectorAll('input[name="candidate"]').forEach(el=>{
    el.addEventListener('change', ()=> selectedCandidateId = el.value);
  });
}

async function startCamera(){
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    video.srcObject = stream;
  } catch(e){
    alert('Unable to access camera: ' + e.message);
  }
}

captureBtn.addEventListener('click', (e) => {
  e.preventDefault();
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  capturedDataUrl = canvas.toDataURL('image/png');
  preview.innerHTML = `<img src="${capturedDataUrl}">`;
});

voteBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  const aadhaar = document.getElementById('aadhaar').value.trim();
  if(!capturedDataUrl){ alert('Capture your face first'); return; }
  if(!selectedCandidateId){ alert('Select a candidate'); return; }
  voteBtn.disabled = true;
  status.textContent = 'Verifying...';

  try {
    const resp = await fetch('/api/verify_and_vote', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ image: capturedDataUrl, candidate_id: selectedCandidateId, aadhaar: aadhaar || null })
    });
    const j = await resp.json();
    if(j.success){
      status.textContent = `Success: ${j.message}. Voter: ${j.user} -> ${j.candidate}`;
    } else {
      status.textContent = `Error: ${j.error || 'Unknown error'}`;
    }
  } catch(err){
    status.textContent = 'Server error: ' + err.message;
  } finally {
    voteBtn.disabled = false;
  }
});

loadCandidates();
startCamera();
