const form = document.getElementById('captionForm');
const videoInput = document.getElementById('videoInput');
const dropzone = document.getElementById('dropzone');
const filePill = document.getElementById('filePill');
const submitBtn = document.getElementById('submitBtn');
const submitText = document.getElementById('submitText');
const spinner = document.getElementById('spinner');
const fontSize = document.getElementById('fontSize');
const fontSizeValue = document.getElementById('fontSizeValue');
const positionRange = document.getElementById('positionRange');
const positionValue = document.getElementById('positionValue');
const positionPreset = document.getElementById('positionPreset');
const hotwords = document.getElementById('hotwords');
const exportVolume = document.getElementById('exportVolume');
const exportVolumeValue = document.getElementById('exportVolumeValue');
const progressWrap = document.getElementById('progressWrap');
const progressTitle = document.getElementById('progressTitle');
const progressPercent = document.getElementById('progressPercent');
const progressBar = document.getElementById('progressBar');
const result = document.getElementById('result');
const resultVideo = document.getElementById('resultVideo');
const downloadBtn = document.getElementById('downloadBtn');
const startOverBtn = document.getElementById('startOverBtn');
const detectedLanguage = document.getElementById('detectedLanguage');
const errorBox = document.getElementById('errorBox');
const templateGrid = document.getElementById('templateGrid');
const sourcePreviewWrap = document.getElementById('sourcePreviewWrap');
const sourcePreview = document.getElementById('sourcePreview');
const sourceAudioBtn = document.getElementById('sourceAudioBtn');
const sourceVolume = document.getElementById('sourceVolume');
const sourceVolumeValue = document.getElementById('sourceVolumeValue');
const captionOverlay = document.getElementById('captionOverlay');
const resultAudioBtn = document.getElementById('resultAudioBtn');
const resultVolume = document.getElementById('resultVolume');
const resultVolumeValue = document.getElementById('resultVolumeValue');
const language = document.getElementById('language');

let resultUrl = null;
let sourceUrl = null;
let selectedTemplate = 'bold_white';

const templates = [
  {id:'bold_white', name:'Bold White', tag:'Oversized', a:'MAKE IT', b:'BOLD', cls:'t-bold-white'},
  {id:'white_yellow', name:'White + Yellow', tag:'Creator', a:'THIS IS', b:'IMPORTANT', cls:'t-white-yellow'},
  {id:'yellow_glow', name:'Yellow Glow', tag:'Glow', a:'CAPTIONS', b:'', cls:'t-yellow-glow'},
  {id:'creator_bold', name:'Creator Bold', tag:'Big text', a:'UNIQUE', b:'BOLD', cls:'t-creator-bold'},
  {id:'clean_white', name:'Clean White', tag:'Minimal', a:'simple', b:'captions', cls:'t-clean'},
  {id:'yellow_bold', name:'Yellow Bold', tag:'High contrast', a:'INSTAGRAM', b:'', cls:'t-yellow-bold'},
  {id:'black_box', name:'Black Box', tag:'Readable', a:'READABLE', b:'ANYWHERE', cls:'t-black-box'},
  {id:'white_box', name:'White Box', tag:'Modern', a:'CLEAN', b:'CARD', cls:'t-white-box'},
  {id:'red_alert', name:'Red Alert', tag:'Punchy', a:'STOP', b:'SCROLLING', cls:'t-red-alert'},
  {id:'cyan_pop', name:'Cyan Pop', tag:'Neon', a:'WATCH', b:'THIS', cls:'t-cyan'},
  {id:'blue_electric', name:'Blue Electric', tag:'Tech', a:'LEVEL UP', b:'NOW', cls:'t-blue'},
  {id:'pink_creator', name:'Pink Creator', tag:'Social', a:'MAKE', b:'CONTENT', cls:'t-pink'},
  {id:'soft_aesthetic', name:'Soft Aesthetic', tag:'Vlog', a:'a little', b:'different', cls:'t-aesthetic'},
  {id:'typewriter', name:'Typewriter', tag:'Story', a:'TELL THE', b:'STORY', cls:'t-typewriter'},
  {id:'minimal_shadow', name:'Minimal Shadow', tag:'Clean', a:'SAY IT', b:'CLEARLY', cls:'t-minimal'},
  {id:'news_ticker', name:'News Ticker', tag:'Headline', a:'BREAKING', b:'NEWS', cls:'t-news'},
  {id:'purple_neon', name:'Purple Neon', tag:'Night', a:'CREATE', b:'MORE', cls:'t-purple'},
  {id:'green_focus', name:'Green Focus', tag:'Energy', a:'FOCUS', b:'HERE', cls:'t-green'}
];

function renderTemplates() {
  templateGrid.innerHTML = templates.map((t, index) => `
    <label class="template-card ${index === 0 ? 'selected' : ''}">
      <input type="radio" name="template" value="${t.id}" ${index === 0 ? 'checked' : ''}>
      <div class="template-preview ${t.cls}">
        <span>${t.a}</span>
        ${t.b ? `<strong>${t.b}</strong>` : ''}
      </div>
      <div class="template-meta"><strong>${t.name}</strong><span>${t.tag}</span></div>
    </label>
  `).join('');
}

templateGrid.addEventListener('change', event => {
  if (event.target.name !== 'template') return;
  selectedTemplate = event.target.value;
  document.querySelectorAll('.template-card').forEach(card => card.classList.remove('selected'));
  event.target.closest('.template-card').classList.add('selected');
  applyPreviewTemplate();
});

function formatBytes(bytes) {
  const units = ['B','KB','MB','GB'];
  let size = bytes;
  let i = 0;
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function selectFile(file) {
  if (!file) return;
  if (!file.type.startsWith('video/')) {
    showError('Please choose a video file.');
    return;
  }
  const dt = new DataTransfer();
  dt.items.add(file);
  videoInput.files = dt.files;
  filePill.textContent = `${file.name} · ${formatBytes(file.size)}`;
  filePill.hidden = false;
  submitBtn.disabled = false;
  hideError();

  if (sourceUrl) URL.revokeObjectURL(sourceUrl);
  sourceUrl = URL.createObjectURL(file);
  sourcePreview.src = sourceUrl;
  sourcePreview.muted = false;
  sourcePreview.defaultMuted = false;
  sourcePreview.volume = Number(sourceVolume.value) / 100;
  sourcePreview.setAttribute('preload', 'auto');
  sourcePreview.load();
  sourcePreviewWrap.hidden = false;
  sourceAudioBtn.textContent = 'Play with audio';
}

videoInput.addEventListener('change', () => selectFile(videoInput.files[0]));

dropzone.addEventListener('click', () => videoInput.click());
['dragenter','dragover'].forEach(name => dropzone.addEventListener(name, e => {
  e.preventDefault();
  dropzone.classList.add('dragging');
}));
['dragleave','drop'].forEach(name => dropzone.addEventListener(name, e => {
  e.preventDefault();
  dropzone.classList.remove('dragging');
}));
dropzone.addEventListener('drop', e => selectFile(e.dataTransfer.files[0]));

sourceAudioBtn.addEventListener('click', async () => {
  sourcePreview.muted = false;
  sourcePreview.volume = Number(sourceVolume.value) / 100;
  try {
    if (sourcePreview.paused) {
      await sourcePreview.play();
      sourceAudioBtn.textContent = 'Pause audio';
    } else {
      sourcePreview.pause();
      sourceAudioBtn.textContent = 'Play with audio';
    }
  } catch (err) {
    sourceAudioBtn.textContent = 'Click Play on video';
  }
});

sourceVolume.addEventListener('input', () => {
  const value = Number(sourceVolume.value);
  sourcePreview.volume = value / 100;
  sourcePreview.muted = value === 0;
  sourceVolumeValue.textContent = `${value}%`;
});

resultAudioBtn.addEventListener('click', async () => {
  resultVideo.muted = false;
  resultVideo.volume = Number(resultVolume.value) / 100;
  try {
    if (resultVideo.paused) {
      await resultVideo.play();
      resultAudioBtn.textContent = 'Pause audio';
    } else {
      resultVideo.pause();
      resultAudioBtn.textContent = 'Play with audio';
    }
  } catch (err) {
    resultAudioBtn.textContent = 'Click Play on video';
  }
});

resultVolume.addEventListener('input', () => {
  const value = Number(resultVolume.value);
  resultVideo.volume = value / 100;
  resultVideo.muted = value === 0;
  resultVolumeValue.textContent = `${value}%`;
});

fontSize.addEventListener('input', () => {
  fontSizeValue.textContent = fontSize.value;
  applyPreviewTemplate();
});

positionRange.addEventListener('input', () => {
  positionValue.textContent = `${positionRange.value}%`;
  applyPreviewPosition();
});

positionPreset.addEventListener('change', () => {
  const values = {top: 16, upper: 32, center: 50, lower: 68, bottom: 84};
  positionRange.value = values[positionPreset.value] ?? 78;
  positionValue.textContent = `${positionRange.value}%`;
  applyPreviewPosition();
});

function applyPreviewPosition() {
  captionOverlay.style.top = `${positionRange.value}%`;
  captionOverlay.style.transform = 'translate(-50%, -50%)';
}

function applyPreviewTemplate() {
  const template = templates.find(t => t.id === selectedTemplate) || templates[0];
  captionOverlay.className = `caption-overlay ${template.cls}`;
  captionOverlay.innerHTML = `<span>${template.a}</span>${template.b ? `<strong>${template.b}</strong>` : ''}`;
  captionOverlay.style.fontSize = `${Math.max(12, Number(fontSize.value) * 0.42)}px`;
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const file = videoInput.files[0];
  if (!file) return;

  hideError();
  result.hidden = true;
  progressWrap.hidden = false;
  submitBtn.disabled = true;
  submitText.textContent = 'Processing…';
  spinner.hidden = false;
  progressTitle.textContent = 'Uploading video…';
  progressPercent.textContent = '0%';
  progressBar.style.width = '0%';

  const data = new FormData();
  data.append('video', file);
  data.append('language', language.value);
  data.append('position', 'bottom');
  data.append('position_percent', positionRange.value);
  data.append('font_size', fontSize.value);
  data.append('template', selectedTemplate);
  data.append('audio_volume', exportVolume.value);
  data.append('hotwords', hotwords.value.trim());

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/caption');
  xhr.responseType = 'blob';

  xhr.upload.onprogress = e => {
    if (!e.lengthComputable) return;
    const pct = Math.round((e.loaded / e.total) * 100);
    progressPercent.textContent = `${pct}%`;
    progressBar.style.width = `${pct}%`;
    if (pct >= 100) {
      progressTitle.textContent = 'AI is transcribing and rendering your captions…';
      progressPercent.textContent = 'Working';
    }
  };

  xhr.onload = async () => {
    spinner.hidden = true;
    submitText.textContent = 'Generate captions';

    if (xhr.status >= 200 && xhr.status < 300) {
      if (resultUrl) URL.revokeObjectURL(resultUrl);
      resultUrl = URL.createObjectURL(xhr.response);
      resultVideo.src = resultUrl;
      resultVideo.muted = false;
      resultVideo.volume = Number(resultVolume.value) / 100;
      resultAudioBtn.textContent = 'Play with audio';
      downloadBtn.href = resultUrl;
      downloadBtn.download = `captioned-${file.name.replace(/\.[^/.]+$/, '')}.mp4`;

      const lang = xhr.getResponseHeader('X-Detected-Language');
      const mode = xhr.getResponseHeader('X-Caption-Mode');
      detectedLanguage.textContent = `${lang ? `Detected speech: ${lang.toUpperCase()}` : ''}${mode ? ` · Mode: ${mode}` : ''}`;

      form.hidden = true;
      progressWrap.hidden = true;
      result.hidden = false;
    } else {
      let message = 'Something went wrong while processing the video.';
      try {
        const text = await xhr.response.text();
        const parsed = JSON.parse(text);
        message = parsed.detail || message;
      } catch (_) {}
      showError(message);
      resetProcessingState();
    }
  };

  xhr.onerror = () => {
    showError('Network error. Make sure the server is running and try again.');
    resetProcessingState();
  };

  xhr.send(data);
});

exportVolume.addEventListener('input', () => {
  exportVolumeValue.textContent = `${exportVolume.value}%`;
});

function resetProcessingState() {
  spinner.hidden = true;
  submitText.textContent = 'Generate captions';
  submitBtn.disabled = !videoInput.files[0];
  progressWrap.hidden = true;
}
function showError(message) { errorBox.textContent = message; errorBox.hidden = false; }
function hideError() { errorBox.hidden = true; errorBox.textContent = ''; }

startOverBtn.addEventListener('click', () => {
  if (resultUrl) { URL.revokeObjectURL(resultUrl); resultUrl = null; }
  resultVideo.removeAttribute('src');
  resultVideo.load();
  if (sourceUrl) { URL.revokeObjectURL(sourceUrl); sourceUrl = null; }
  sourcePreview.removeAttribute('src');
  sourcePreview.load();
  sourcePreviewWrap.hidden = true;
  result.hidden = true;
  form.hidden = false;
  form.reset();
  filePill.hidden = true;
  submitBtn.disabled = true;
  selectedTemplate = 'bold_white';
  document.querySelector('input[name="template"][value="bold_white"]').checked = true;
  document.querySelectorAll('.template-card').forEach(card => card.classList.remove('selected'));
  document.querySelector('input[name="template"][value="bold_white"]').closest('.template-card').classList.add('selected');
  fontSize.value = 54;
  fontSizeValue.textContent = '54';
  positionRange.value = 78;
  positionValue.textContent = '78%';
  positionPreset.value = 'bottom';
  sourceVolume.value = 100;
  sourceVolumeValue.textContent = '100%';
  exportVolume.value = 100;
  exportVolumeValue.textContent = '100%';
  resultVolume.value = 100;
  resultVolumeValue.textContent = '100%';
  applyPreviewTemplate();
  applyPreviewPosition();
  hideError();
});

renderTemplates();
applyPreviewTemplate();
applyPreviewPosition();
