// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

// 页面中的主要 DOM 节点。
const recentDetectionsElement = document.getElementById('recentDetections');
const feedbackContentElement = document.getElementById('feedback-content');

// 最多保留多少条最近检测记录。
const MAX_RECENT_SCANS = 5;
let scans = [];

// 前后端实时通信通道。
const socket = io();

// 错误提示区域。
let errorContainer = document.getElementById('error-container');

// 视频流 iframe 的访问地址。
// 手机摄像头流会由开发板在 4912 端口提供出来。
const currentHostname = window.location.hostname;
const targetPort = 4912;
const targetPath = '/embed';
const streamUrl = `http://${currentHostname}:${targetPort}${targetPath}`;

// 当前摄像头连接状态。
let webcamState = {
    clientName: "",
    status: "disconnected",
    secret: null,
    protocol: "",
    ip: "",
    port: 0
};


// 页面加载完成后初始化整个前端应用。
document.addEventListener('DOMContentLoaded', () => {
    initSocketIO();
    initializeConfidenceSlider();
    updateFeedback(null);
    renderDetections();
    updateDisplay();

    const confidencePopoverText = "Minimum confidence score for detected objects. Lower values show more results but may include false positives.";
    const feedbackPopoverText = "An animation will appear here when the camera detects:<ul><li>Cat<li>Clock<li>Cup<li>Dog<li>Plant";

    // 绑定悬浮提示。
    document.querySelectorAll('.info-btn.confidence').forEach(img => {
        const popover = img.nextElementSibling;
        img.addEventListener('mouseenter', () => {
            popover.textContent = confidencePopoverText;
            popover.style.display = 'block';
        });
        img.addEventListener('mouseleave', () => {
            popover.style.display = 'none';
        });
    });

    document.querySelectorAll('.info-btn.feedback').forEach(img => {
        const popover = img.nextElementSibling;
        img.addEventListener('mouseenter', () => {
            popover.innerHTML = feedbackPopoverText;
            popover.style.display = 'block';
        });
        img.addEventListener('mouseleave', () => {
            popover.style.display = 'none';
        });
    });
});

function updateDisplay() {
    // 根据当前摄像头状态决定页面展示：
    // - disconnected: 显示二维码
    // - streaming: 显示视频流
    const body = document.getRootNode().body;
    body.setAttribute('data-webcam-status', webcamState.status);
    const dynamicIframe = document.getElementById('dynamicIframe');
    const clientName = document.getElementById('clientName');

    if (webcamState.status == "streaming") {
        dynamicIframe.src = streamUrl;
        dynamicIframe.height = Math.min((window.innerWidth - 60) * 4/3 + 60, 768);
        dynamicIframe.width = Math.min(768, (window.innerWidth - 60));
        clientName.textContent = `${webcamState.clientName || "Unknown Device"} connected`;
        clientName.innerHTML += '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 1C6.61553 1 5.26216 1.41054 4.11101 2.17971C2.95987 2.94888 2.06266 4.04213 1.53285 5.32122C1.00303 6.6003 0.86441 8.00776 1.13451 9.36563C1.4046 10.7235 2.07129 11.9708 3.05026 12.9497C4.02922 13.9287 5.2765 14.5954 6.63437 14.8655C7.99224 15.1356 9.3997 14.997 10.6788 14.4672C11.9579 13.9373 13.0511 13.0401 13.8203 11.889C14.5895 10.7378 15 9.38447 15 8C15 6.14348 14.2625 4.36301 12.9497 3.05025C11.637 1.7375 9.85652 1 8 1ZM11.855 6.355L7.355 10.855C7.30852 10.9019 7.25322 10.9391 7.19229 10.9644C7.13136 10.9898 7.06601 11.0029 7 11.0029C6.934 11.0029 6.86864 10.9898 6.80771 10.9644C6.74679 10.9391 6.69148 10.9019 6.645 10.855L4.145 8.355C4.05085 8.26085 3.99796 8.13315 3.99796 8C3.99796 7.86685 4.05085 7.73915 4.145 7.645C4.23915 7.55085 4.36685 7.49795 4.5 7.49795C4.63315 7.49795 4.76085 7.55085 4.855 7.645L7 9.795L11.145 5.645C11.2392 5.55085 11.3669 5.49795 11.5 5.49795C11.6332 5.49795 11.7609 5.55085 11.855 5.645C11.9492 5.73915 12.002 5.86685 12.002 6C12.002 6.13315 11.9492 6.26085 11.855 6.355Z" fill="#16A588"/></svg>';
    } else if (webcamState.status != "connected") {
        clientName.textContent = 'No Device Connected';
        if (webcamState.secret) {
            generateQRCode(webcamState.secret, webcamState.protocol, webcamState.ip, webcamState.port);
        }
    }
}

function generateQRCode(secret, protocol, ip, port) {
    // 生成 Arduino IoT Remote 所需格式的二维码内容。
    const qrCodeContainer = document.getElementById('qrCodeContainer');
    const qrSecretText = document.getElementById('qrSecretText');

    qrCodeContainer.innerHTML = '';
    qrSecretText.textContent = '';

    new QRCode(qrCodeContainer, {
        text: `https://cloud.arduino.cc/installmobileapp?otp=${secret}&protocol=${protocol}&ip=${ip}&port=${port}`,
        width: 128,
        height: 128,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.L,
    });

    qrSecretText.textContent = `Password: ${secret}`;
}

function initSocketIO() {
    // 与后端建立连接后的处理。
    socket.on('connect', () => {
        if (errorContainer) {
            errorContainer.style.display = 'none';
            errorContainer.textContent = '';
        }
    });

    // 与后端断开连接后的处理。
    socket.on('disconnect', () => {
        if (errorContainer) {
            errorContainer.textContent = 'Connection to the board lost. Please check the connection.';
            errorContainer.style.display = 'block';
        }
    });

    // 收到新的检测结果。
    socket.on('detection', async (message) => {
        printDetection(message);
        renderDetections();
        updateFeedback(message);
    });

    // 页面初次连接后，从后端拿到欢迎消息和配对信息。
    socket.on('welcome', async (message) => {
        if (message.status !== "disconnected") {
            webcamState.clientName = message.client_name;
        }
        webcamState.status = message.status;
        webcamState.secret = message.secret;
        webcamState.protocol = message.protocol;
        webcamState.ip = message.ip;
        webcamState.port = message.port;
        updateDisplay();
    });

    // 手机摄像头连接成功。
    socket.on('connected', async (message) => {
        console.log("Webcam connected!");
        webcamState.status = "connected";
        webcamState.clientAddr = message.client_address;
        webcamState.clientName = message.client_name;
        updateDisplay();
    });

    // 手机断开连接。
    socket.on('disconnected', async (message) => {
        console.log("Webcam disconnected!");
        webcamState.status = "disconnected";
        webcamState.clientAddr = "";
        webcamState.clientName = "";
        updateDisplay();
    });

    // 视频流开始传输。
    socket.on('streaming', async (message) => {
        console.log("Webcam streaming started!");
        webcamState.status = "streaming";
        updateDisplay();
        updateConfidenceDisplay();
    });

    // 视频流暂停。
    socket.on('paused', async (message) => {
        console.log("Webcam streaming stopped!");
        webcamState.status = "paused";
        updateDisplay();
    });
}

function updateFeedback(detection) {
    // 针对部分特定目标显示更丰富的反馈内容。
    const objectInfo = {
        "cat": { text: "Meow!", gif: "cat.webp" },
        "cell phone": { text: "Stay connected", gif: "phone.webp" },
        "clock": { text: "Time to go", gif: "clock.webp" },
        "cup": { text: "Need a break?", gif: "cup.webp" },
        "dog": { text: "Walkies?", gif: "dog.webp" },
        "potted plant": { text: "Glow your ideas!", gif: "plant.webp" }
    };

    if (detection && objectInfo[detection.content]) {
        const info = objectInfo[detection.content];
        const confidence = detection.confidence * 100;
        if (feedbackContentElement.getAttribute('data-detection') === detection.content) {
            return;
        }
        feedbackContentElement.setAttribute('data-detection', detection.content);
        feedbackContentElement.innerHTML = `
            <div class="feedback-detection">
                <div class="percentage">${confidence.toFixed(1)}% ${detection.content}</div>
                <img src="img/${info.gif}" alt="${detection.content}">
                <span>${info.text}</span>
            </div>
        `;
    } else if (feedbackContentElement.getAttribute('data-detection') !== 'none') {
        feedbackContentElement.setAttribute('data-detection', 'none');
        feedbackContentElement.innerHTML = `
            <img src="img/stars.svg" alt="Stars">
            <p class="feedback-text">System response will appear here</p>
        `;
    }
}

function printDetection(newDetection) {
    // 新检测结果插入队首，只保留最新的几条。
    scans.unshift(newDetection);
    if (scans.length > MAX_RECENT_SCANS) { scans.pop(); }
}

function renderDetections() {
    // 刷新最近检测列表。
    recentDetectionsElement.innerHTML = ``;

    if (scans.length === 0) {
        recentDetectionsElement.innerHTML = `
            <div class="no-recent-scans">
                <img src="./img/no-face.svg">
                No object detected yet
            </div>
        `;
        return;
    }

    scans.forEach((scan) => {
        const row = document.createElement('div');
        row.className = 'scan-container';

        const cellContainer = document.createElement('span');
        cellContainer.className = 'scan-cell-container cell-border';

        const percentText = document.createElement('span');
        percentText.className = 'scan-percentage';
        const value = scan.confidence;
        const result = Math.floor(value * 1000) / 10;
        percentText.innerHTML = `${result}%`;

        const contentText = document.createElement('span');
        contentText.className = 'scan-content';
        contentText.innerHTML = `${scan.content}`;

        const timeText = document.createElement('span');
        timeText.className = 'scan-content-time';

        const options = {
            hour: '2-digit', minute: '2-digit', hour12: false,
            day: '2-digit', month: 'short', year: 'numeric'
        };

        const parts = new Intl.DateTimeFormat('en-GB', options).formatToParts(new Date(scan.timestamp))
            .reduce((acc, part) => ({ ...acc, [part.type]: part.value }), {});

        const formattedDate = `${parts.hour}:${parts.minute} - ${parts.day} ${parts.month} ${parts.year}`;

        timeText.textContent = formattedDate;

        cellContainer.appendChild(percentText);
        cellContainer.appendChild(contentText);
        cellContainer.appendChild(timeText);

        row.appendChild(cellContainer);
        recentDetectionsElement.appendChild(row);
    });
}

function initializeConfidenceSlider() {
    // 初始化检测阈值滑块和输入框。
    const confidenceSlider = document.getElementById('confidenceSlider');
    const confidenceInput = document.getElementById('confidenceInput');
    const confidenceResetButton = document.getElementById('confidenceResetButton');

    confidenceSlider.addEventListener('input', updateConfidenceDisplay);
    confidenceInput.addEventListener('input', handleConfidenceInputChange);
    confidenceInput.addEventListener('blur', validateConfidenceInput);
    updateConfidenceDisplay();

    confidenceResetButton.addEventListener('click', (e) => {
        if (e.target.classList.contains('reset-icon') || e.target.closest('.reset-icon')) {
            resetConfidence();
        }
    });
}

function handleConfidenceInputChange() {
    const confidenceInput = document.getElementById('confidenceInput');
    const confidenceSlider = document.getElementById('confidenceSlider');

    let value = parseInt(confidenceInput.value);

    if (isNaN(value)) value = 50;
    if (value < 0) value = 0;
    if (value > 100) value = 100;

    confidenceSlider.value = value;
    updateConfidenceDisplay();
}

function validateConfidenceInput() {
    const confidenceInput = document.getElementById('confidenceInput');
    let value = parseInt(confidenceInput.value);

    if (isNaN(value)) value = 50;
    if (value < 0) value = 0;
    if (value > 100) value = 100;

    confidenceInput.value = value;
    handleConfidenceInputChange();
}

function updateConfidenceDisplay() {
    const confidenceSlider = document.getElementById('confidenceSlider');
    const confidenceInput = document.getElementById('confidenceInput');
    const confidenceValueDisplay = document.getElementById('confidenceValueDisplay');
    const sliderProgress = document.getElementById('sliderProgress');

    const value = parseInt(confidenceSlider.value);

    // 当视频流处于 streaming 状态时，把阈值发送给后端。
    if (webcamState.status === "streaming") {
        socket.emit('override_th', value / 100);
    }

    const percentage = (value - confidenceSlider.min) / (confidenceSlider.max - confidenceSlider.min) * 100;
    const displayValue = value;

    confidenceValueDisplay.textContent = displayValue;

    if (document.activeElement !== confidenceInput) {
        confidenceInput.value = displayValue;
    }

    sliderProgress.style.width = percentage + '%';
    confidenceValueDisplay.style.left = percentage + '%';
}

function resetConfidence() {
    // 把阈值恢复到默认 50%。
    const confidenceSlider = document.getElementById('confidenceSlider');
    const confidenceInput = document.getElementById('confidenceInput');

    confidenceSlider.value = '50';
    confidenceInput.value = '50';
    updateConfidenceDisplay();
}
