const host = window.location.hostname;
const baseUrl = `http://${host}:8080`;
const stream = document.getElementById('stream');
const placeholder = document.getElementById('placeholder');
const statusText = document.getElementById('status');
const streamUrl = document.getElementById('streamUrl');
const snapshotLink = document.getElementById('snapshotLink');

stream.src = `${baseUrl}/stream.mjpg`;
snapshotLink.href = `${baseUrl}/snapshot.jpg`;
streamUrl.textContent = `${baseUrl}/stream.mjpg`;

stream.addEventListener('load', () => {
  placeholder.style.display = 'none';
  stream.style.display = 'block';
});

stream.addEventListener('error', () => {
  statusText.textContent = `Cannot load ${baseUrl}/stream.mjpg`;
});

async function refreshHealth() {
  try {
    const response = await fetch(`${baseUrl}/health`, { cache: 'no-store' });
    statusText.textContent = (await response.text()).trim();
  } catch (error) {
    statusText.textContent = `Run Debian OpenCV service on ${baseUrl}`;
  }
}

refreshHealth();
setInterval(refreshHealth, 1000);
