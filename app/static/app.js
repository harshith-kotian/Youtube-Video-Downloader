document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('download-form');
    const videoUrlInput = document.getElementById('video-url');
    const videoInfo = document.getElementById('video-info');
    const loading = document.getElementById('loading');
    const videoDetails = document.getElementById('video-details');
    const thumbnail = document.getElementById('thumbnail');
    const videoTitle = document.getElementById('video-title');
    const videoChannel = document.getElementById('video-channel');
    const videoDuration = document.getElementById('video-duration');
    const downloadOptions = document.getElementById('download-options');
    const formatList = document.getElementById('format-list');
    const errorMessage = document.getElementById('error-message');

    const API_BASE_URL = 'https://youtube-video-downloader-0xa1.onrender.com';

    const formatDuration = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    const showError = (message) => {
        errorMessage.querySelector('p').textContent = message;
        errorMessage.classList.remove('hidden');
        loading.classList.add('hidden');
    };

    const resetUI = () => {
        videoDetails.classList.add('hidden');
        downloadOptions.classList.add('hidden');
        errorMessage.classList.add('hidden');
        videoInfo.classList.remove('hidden');
        loading.classList.remove('hidden');
    };

    const showSuccessMessage = () => {
        formatList.innerHTML = `
            <div class="bg-green-900/50 border border-green-800 text-green-200 p-6 rounded-lg text-center">
                <span class="material-icons text-4xl mb-2">check_circle</span>
                <h3 class="text-xl font-semibold mb-2">Download Complete!</h3>
                <p>Thank you for using our service!</p>
                <button onclick="location.reload()" class="mt-4 bg-green-600 hover:bg-green-700 px-4 py-2 rounded">
                    Download Another Video
                </button>
            </div>
        `;
    };

    videoUrlInput.addEventListener('input', () => {
        errorMessage.classList.add('hidden');
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const videoUrl = videoUrlInput.value.trim();
        if (!videoUrl) return;

        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[a-zA-Z0-9_-]+/;
        if (!youtubeRegex.test(videoUrl)) {
            showError('Please enter a valid YouTube URL');
            return;
        }

        resetUI();

        try {
            const response = await fetch(`${API_BASE_URL}/api/info?url=${encodeURIComponent(videoUrl)}`);
            
            if (!response.ok) {
                throw new Error("Failed to fetch video information.");
            }

            const data = await response.json();

            loading.classList.add('hidden');
            videoDetails.classList.remove('hidden');
            downloadOptions.classList.remove('hidden');

            thumbnail.innerHTML = `<img src="${data.thumbnail}" alt="Video thumbnail" class="w-full rounded-lg">`;
            videoTitle.textContent = data.title;
            videoChannel.textContent = `Channel: ${data.channel}`;
            videoDuration.textContent = `Duration: ${formatDuration(data.duration)}`;

            formatList.innerHTML = '';

            data.formats.forEach(format => {
                const formatItem = document.createElement('div');
                formatItem.className = 'bg-zinc-800 p-3 rounded-lg flex justify-between items-center mb-3';
                
                const formatInfo = document.createElement('div');
                formatInfo.innerHTML = `
                    <p class="font-medium">${format.quality}</p>
                    <p class="text-sm text-zinc-400">${format.type} · ${format.size}</p>
                `;

                const downloadBtn = document.createElement('button');
                downloadBtn.className = 'bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2';
                downloadBtn.innerHTML = `
                    <span class="material-icons text-sm">download</span>
                    <span>Download</span>
                `;
                
                downloadBtn.addEventListener('click', async () => {
                    downloadBtn.disabled = true;
                    downloadBtn.innerHTML = `
                        <span class="material-icons text-sm animate-spin">autorenew</span>
                        <span>Downloading...</span>
                    `;
                    
                    try {
                        const downloadResponse = await fetch(
                            `${API_BASE_URL}/api/download?url=${encodeURIComponent(videoUrl)}&itag=${format.itag}`
                        );
                        
                        if (!downloadResponse.ok) {
                            throw new Error("Download failed.");
                        }

                        const blob = await downloadResponse.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${data.title.replace(/[^a-z0-9]/gi, '_').substring(0, 50)}.mp4`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        
                        setTimeout(() => {
                            URL.revokeObjectURL(url);
                            showSuccessMessage();
                        }, 100);
                        
                    } catch (err) {
                        showError(err.message || "Download failed, please try again.");
                        downloadBtn.disabled = false;
                        downloadBtn.innerHTML = `
                            <span class="material-icons text-sm">download</span>
                            <span>Download</span>
                        `;
                    }
                });

                formatItem.appendChild(formatInfo);
                formatItem.appendChild(downloadBtn);
                formatList.appendChild(formatItem);
            });

        } catch (error) {
            showError(error.message || 'An error occurred. Please try again.');
        }
    });
});