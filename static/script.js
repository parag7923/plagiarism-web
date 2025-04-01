const socket = io();

document.getElementById("upload-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    // Clear any previous results and reset the progress bar
    clearPreviousResults();

    let formData = new FormData();
    let fileInput = document.getElementById("zip-file");

    if (fileInput.files.length === 0) {
        alert("Please select a ZIP file to upload.");
        return;
    }

    formData.append("file", fileInput.files[0]);

    let processingDiv = document.getElementById("processing");
    let resultsDiv = document.getElementById("results");
    let fileCountDiv = document.getElementById("file-count");
    let progressBar = document.getElementById("progress-bar");
    let progressText = document.getElementById("progress-text");

    processingDiv.classList.remove("hidden");
    resultsDiv.classList.add("hidden");
    document.getElementById("progress-container").classList.remove("hidden");
    fileCountDiv.classList.add("hidden");

    let response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    let data = await response.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    let totalFiles = data.num_files;
    fileCountDiv.innerHTML = `Total files to process: ${totalFiles}`;
    fileCountDiv.classList.remove("hidden");

    socket.emit('process_files', {});
});

// Clear previous results and reset progress bar
function clearPreviousResults() {
    let resultsDiv = document.getElementById("results");
    let plagiarismDetectedDiv = document.getElementById("plagiarism-detected");
    let noPlagiarismDiv = document.getElementById("no-plagiarism");
    let progressBar = document.getElementById("progress-bar");
    let progressText = document.getElementById("progress-text");

    plagiarismDetectedDiv.innerHTML = "";
    noPlagiarismDiv.innerHTML = "";
    resultsDiv.classList.add("hidden");

    // Reset progress bar
    progressBar.value = 0;
    progressText.textContent = "0%";
    document.getElementById("progress-container").classList.add("hidden");
}

// Receive real-time progress updates
socket.on('progress_update', function(data) {
    document.getElementById("progress-bar").value = data.progress;
    document.getElementById("progress-text").textContent = `${Math.round(data.progress)}%`;
});

// Receive final results
socket.on('processing_complete', function(data) {
    let resultsDiv = document.getElementById("results");
    let plagiarismDetectedDiv = document.getElementById("plagiarism-detected");
    let noPlagiarismDiv = document.getElementById("no-plagiarism");

    plagiarismDetectedDiv.innerHTML = "";
    noPlagiarismDiv.innerHTML = "";

    // Hide No Plagiarism Section if Plagiarism Detected
    if (data.plagiarism_groups.length > 0) {
        plagiarismDetectedDiv.innerHTML = "<h3>🚩 Plagiarized Files</h3>";
        data.plagiarism_groups.forEach(group => {
            let p = document.createElement("p");
            p.innerHTML = `Files in this group: <strong>${group.join(', ')}</strong>`;
            plagiarismDetectedDiv.appendChild(p);
        });
    } else {
        // If no plagiarism detected, show this message and hide the plagiarism section
        noPlagiarismDiv.innerHTML = "<h3>✅ No Plagiarism Detected</h3><p>All files are original!</p>";
    }

    resultsDiv.classList.remove("hidden");
});
