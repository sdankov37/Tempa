const API_BASE = 'http://127.0.0.1:8000';  // или 'http://127.0.0.1:8000'

// Элементы
const loginPage = document.getElementById('loginPage');
const mainPage = document.getElementById('mainPage');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const showRegister = document.getElementById('showRegister');
const showLogin = document.getElementById('showLogin');
const loginMessage = document.getElementById('loginMessage');
const logoutBtn = document.getElementById('logoutBtn');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const processBtn = document.getElementById('processBtn');
const statusDiv = document.getElementById('status');
const resultDiv = document.getElementById('result');
const resultImg = document.getElementById('resultImage');
const thresholdSlider = document.getElementById('thresholdSlider');
const thresholdValue = document.getElementById('thresholdValue');
const downloadBtn = document.getElementById('downloadBtn');

let currentTaskId = null;
let currentImageBase64 = '';
let pollingInterval = null;

// --- Аутентификация ---
async function login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include'
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка входа');
    }
    return await res.json();
}

async function register(username, password) {
    const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка регистрации');
    }
    return await res.json();
}

async function logout() {
    await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
    });
}

async function checkAuth() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            credentials: 'include'
        });
        if (res.ok) return true;
        return false;
    } catch {
        return false;
    }
}

function showLoginPage() {
    loginPage.classList.add('active');
    mainPage.classList.remove('active');
}

function showMainPage() {
    loginPage.classList.remove('active');
    mainPage.classList.add('active');
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    loginMessage.textContent = '⏳ Вход...';
    try {
        await login(username, password);
        loginMessage.textContent = '✅ Успешно!';
        setTimeout(() => {
            showMainPage();
            loadUser();
            loginMessage.textContent = '';
        }, 200);
    } catch (err) {
        loginMessage.textContent = '❌ ' + err.message;
    }
});

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    loginMessage.textContent = '⏳ Регистрация...';
    try {
        await register(username, password);
        loginMessage.textContent = '✅ Регистрация успешна! Теперь войдите.';
        registerForm.style.display = 'none';
        loginForm.style.display = 'block';
    } catch (err) {
        loginMessage.textContent = '❌ ' + err.message;
    }
});

showRegister.addEventListener('click', () => {
    loginForm.style.display = 'none';
    registerForm.style.display = 'block';
    loginMessage.textContent = '';
});

showLogin.addEventListener('click', () => {
    registerForm.style.display = 'none';
    loginForm.style.display = 'block';
    loginMessage.textContent = '';
});

logoutBtn.addEventListener('click', async () => {
    await logout();
    showLoginPage();
    if (pollingInterval) clearInterval(pollingInterval);
});

async function loadUser() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' });
        if (res.ok) {
            const data = await res.json();
            document.querySelector('header h1').textContent = `🌡️ Tempa (${data.username})`;
        } else {
            showLoginPage();
        }
    } catch {
        showLoginPage();
    }
}

fileInput.addEventListener('change', () => {
    fileName.textContent = fileInput.files[0] ? `📄 ${fileInput.files[0].name}` : '';
});

processBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
        statusDiv.textContent = '⚠️ Выберите файл.';
        return;
    }
    const tMin = parseFloat(document.getElementById('tMin').value) || 625;
    const tMax = parseFloat(document.getElementById('tMax').value) || 1526.1;
    const threshold = parseFloat(document.getElementById('threshold').value) || 900;
    if (tMin >= tMax) {
        statusDiv.textContent = '⚠️ T_min < T_max';
        return;
    }

    statusDiv.textContent = '⏳ Загрузка файла...';
    processBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('t_min', tMin);
    formData.append('t_max', tMax);
    formData.append('threshold', threshold);

    try {
        const res = await fetch(`${API_BASE}/tasks/upload`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Ошибка загрузки');
        }
        const data = await res.json();
        currentTaskId = data.task_id;
        statusDiv.textContent = `⏳ Задача создана (ID: ${currentTaskId}), ожидание...`;
        startPolling(currentTaskId);
    } catch (err) {
        statusDiv.textContent = '❌ ' + err.message;
        processBtn.disabled = false;
    }
});

function startPolling(taskId) {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/tasks/status/${taskId}`, {
                credentials: 'include'
            });
            if (!res.ok) throw new Error('Ошибка получения статуса');
            const data = await res.json();
            statusDiv.textContent = `⏳ Статус: ${data.status}`;

            if (data.status === 'completed') {
                clearInterval(pollingInterval);
                pollingInterval = null;
                currentImageBase64 = data.result_image;
                resultImg.src = `data:image/png;base64,${data.result_image}`;
                resultDiv.style.display = 'flex';
                thresholdSlider.value = data.threshold;
                thresholdValue.textContent = data.threshold.toFixed(1);
                processBtn.disabled = false;
                statusDiv.textContent = '✅ Готово!';
            } else if (data.status === 'failed') {
                clearInterval(pollingInterval);
                pollingInterval = null;
                processBtn.disabled = false;
                statusDiv.textContent = '❌ Ошибка: ' + (data.error || 'неизвестная ошибка');
            }
        } catch (err) {
            // игнорируем ошибки сети при опросе
        }
    }, 2000);
}

thresholdSlider.addEventListener('input', async () => {
    const val = parseFloat(thresholdSlider.value);
    thresholdValue.textContent = val.toFixed(1);
    if (!currentTaskId) return;
    try {
        const formData = new FormData();
        formData.append('task_id', currentTaskId);
        formData.append('threshold', val);
        const res = await fetch(`${API_BASE}/tasks/recolor`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        if (!res.ok) throw new Error('Ошибка пересчёта');
        const data = await res.json();
        if (data.result_image) {
            currentImageBase64 = data.result_image;
            resultImg.src = `data:image/png;base64,${data.result_image}`;
        }
    } catch (err) {
        console.error('Recolor error:', err);
    }
});

downloadBtn.addEventListener('click', () => {
    if (!currentImageBase64) return;
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${currentImageBase64}`;
    link.download = `tempa_${Date.now()}.png`;
    link.click();
});

(async () => {
    const isAuth = await checkAuth();
    if (isAuth) {
        showMainPage();
        loadUser();
    } else {
        showLoginPage();
    }
})();