// Initialize dark mode
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
}

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
    if (event.matches) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
});

// Global variables
let videoData = null;

// Get elements
const youtubeUrlInput = document.getElementById('youtubeUrl');
const qualitySelect = document.getElementById('quality');
const infoBtn = document.getElementById('infoBtn');
const downloadBtn = document.getElementById('downloadBtn');
const resultDiv = document.getElementById('result');
const loadingDiv = document.getElementById('loading');
const errorMessageDiv = document.getElementById('errorMessage');
const errorTextP = document.getElementById('errorText');
const successMessageDiv = document.getElementById('successMessage');
const successTextP = document.getElementById('successText');
const videoInfoDiv = document.getElementById('videoInfo');
const videoTitleH2 = document.getElementById('videoTitle');
const videoThumbnailDiv = document.getElementById('videoThumbnail');
const videoDetailsDiv = document.getElementById('videoDetails');
const downloadLinkDiv = document.getElementById('downloadLink');

// Add event listeners
infoBtn.addEventListener('click', getVideoInfo);
downloadBtn.addEventListener('click', downloadVideo);

// Function to get video information
async function getVideoInfo() {
    const url = youtubeUrlInput.value.trim();
    
    if (!url) {
        showError("الرجاء إدخال رابط يوتيوب");
        return;
    }
    
    showLoading("جاري جلب معلومات الفيديو...");
    
    try {
        const response = await fetch('/api/video-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || "حدث خطأ أثناء جلب معلومات الفيديو");
        }
        
        // Save video data
        videoData = data;
        
        // Show video information
        showVideoInfo(data);
        
        // Update quality options
        updateQualityOptions(data.available_qualities);
        
        // Show download button
        downloadBtn.classList.remove('hidden');
        
        hideLoading();
    } catch (error) {
        showError(error.message);
    }
}

// Function to download video
async function downloadVideo() {
    const url = youtubeUrlInput.value.trim();
    const quality = qualitySelect.value;
    
    if (!url) {
        showError("الرجاء إدخال رابط يوتيوب");
        return;
    }
    
    showLoading("جاري تنزيل الفيديو...");
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, quality }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || "حدث خطأ أثناء تنزيل الفيديو");
        }
        
        // Show success message
        showSuccess(data.message);
        
        // Add download link
        downloadLinkDiv.innerHTML = `
            <a href="${data.download_url}" class="inline-block bg-primary hover:bg-opacity-90 text-white font-medium py-2 px-4 rounded-md transition duration-200 text-center w-full">
                تنزيل الفيديو (${videoData.title})
            </a>
        `;
        
        hideLoading();
    } catch (error) {
        showError(error.message);
    }
}

// Function to show video information
function showVideoInfo(data) {
    videoInfoDiv.classList.remove('hidden');
    
    videoTitleH2.textContent = data.title;
    
    if (data.thumbnail) {
        videoThumbnailDiv.innerHTML = `<img src="${data.thumbnail}" alt="${data.title}" class="w-full h-full object-cover">`;
    }
    
    // Format duration from seconds to MM:SS
    let duration = "مدة غير معروفة";
    if (data.duration) {
        const minutes = Math.floor(data.duration / 60);
        const seconds = data.duration % 60;
        duration = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }
    
    videoDetailsDiv.innerHTML = `
        <p><strong>القناة:</strong> ${data.author || 'غير معروف'}</p>
        <p><strong>المدة:</strong> ${duration}</p>
    `;
}

// Function to update quality options
function updateQualityOptions(qualities) {
    // Clear current options
    qualitySelect.innerHTML = '<option value="highest">أعلى جودة</option>';
    
    // Add available qualities
    if (qualities && qualities.length > 0) {
        qualities.forEach(quality => {
            const option = document.createElement('option');
            option.value = quality;
            option.textContent = quality;
            qualitySelect.appendChild(option);
        });
    }
}

// Utility functions
function showLoading(message) {
    resultDiv.classList.remove('hidden');
    loadingDiv.classList.remove('hidden');
    document.getElementById('loadingText').textContent = message;
    errorMessageDiv.classList.add('hidden');
    successMessageDiv.classList.add('hidden');
}

function hideLoading() {
    loadingDiv.classList.add('hidden');
}

function showError(message) {
    resultDiv.classList.remove('hidden');
    loadingDiv.classList.add('hidden');
    errorMessageDiv.classList.remove('hidden');
    errorTextP.textContent = message;
    successMessageDiv.classList.add('hidden');
}

function showSuccess(message) {
    resultDiv.classList.remove('hidden');
    loadingDiv.classList.add('hidden');
    successMessageDiv.classList.remove('hidden');
    successTextP.textContent = message;
    errorMessageDiv.classList.add('hidden');
}