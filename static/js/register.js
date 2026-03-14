// static/js/register.js
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureBtn = document.getElementById('capture');
const submitBtn = document.getElementById('submitReg');
const preview = document.getElementById('preview');
const msg = document.getElementById('msg');

let capturedDataUrl = null;

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

submitBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  const name = document.getElementById('name').value.trim();
  const aadhaar = document.getElementById('aadhaar').value.trim();
  if(!name || !aadhaar || !capturedDataUrl){ alert('Complete all fields and capture photo'); return; }
  submitBtn.disabled = true;
  msg.textContent = 'Registering...';

  try {
    const resp = await fetch('/api/register', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ name, aadhaar, image: capturedDataUrl })
    });
    const j = await resp.json();
    if(j.success){
      msg.textContent = 'Registered successfully!';
    } else {
      msg.textContent = 'Error: ' + j.error;
    }
  } catch(err){
    msg.textContent = 'Server error: ' + err.message;
  } finally {
    submitBtn.disabled = false;
  }
});

startCamera();
