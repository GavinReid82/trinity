document.addEventListener("DOMContentLoaded", function () {
    const startButton = document.getElementById('start-recording');
    const submitButton = document.getElementById('submit-btn');
    const countdownTimer = document.getElementById('countdown-text');
    const mimeType = 'audio/webm;codecs=opus';
    let recorder;
    let chunks = [];
    let countdownInterval;

    startButton.addEventListener('click', function () {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                chunks = [];
                recorder = new MediaRecorder(stream, { mimeType: mimeType });

                recorder.ondataavailable = event => chunks.push(event.data);

                recorder.onstop = () => {
                    console.log('Recording stopped.');
                    const blob = new Blob(chunks, { type: mimeType });
                    chunks = [];

                    // ✅ Use FormData to upload the binary blob
                    const formData = new FormData();
                    formData.append('question_number', document.querySelector("input[name='question_number']").value);
                    formData.append('audio_file', blob, 'audio_record.webm');

                    // ✅ Disable the submit button and show "Submitting..."
                    submitButton.disabled = true;
                    submitButton.innerText = "Submitting...";

                    // ✅ Manually submit FormData using fetch
                    fetch('/speaking/speaking_task_submit', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.text())  // Return plain text to check the server's response
                    .then(data => {
                        console.log("Server response:", data);
                        window.location.href = `/speaking/speaking_task_1_feedback?question_number=${document.querySelector("input[name='question_number']").value}`;
                    })
                    .catch(err => console.error('Error uploading file:', err));
                };

                recorder.start();
                startButton.disabled = true;

                // ✅ Start countdown timer
                let timeLeft = 30;
                countdownTimer.innerText = timeLeft;
                countdownInterval = setInterval(() => {
                    timeLeft--;
                    countdownTimer.innerText = timeLeft;

                    if (timeLeft <= 0) {
                        clearInterval(countdownInterval);
                        recorder.stop();  // Automatically stop recording
                    }
                }, 1000);
            })
            .catch(err => console.error('Error accessing microphone:', err));
    });

    // ✅ Stop recording and freeze timer if the user clicks submit early
    const form = document.querySelector('form');
    form.onsubmit = function (event) {
        event.preventDefault();
        if (recorder && recorder.state === "recording") {
            clearInterval(countdownInterval);  // Stop the timer
            recorder.stop();
        }
    };
});
