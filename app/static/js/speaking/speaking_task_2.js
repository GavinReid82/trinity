document.addEventListener("DOMContentLoaded", function () {
    const startButton = document.getElementById('start-recording');
    const startFollowUpButton = document.getElementById('start-follow-up');
    const submitButton = document.getElementById('submit-btn');
    const countdownTimer = document.getElementById('countdown-text');
    const followUpTimer = document.getElementById('follow-up-countdown');
    const mainTask = document.getElementById('main-task');
    const followUp = document.getElementById('follow-up');
    const stageInput = document.getElementById('stage');
    
    const mimeType = 'audio/webm;codecs=opus';
    let recorder;
    let chunks = [];
    let countdownInterval;
    let isMainTask = true;

    function startRecording(duration, timerElement, nextStage) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                chunks = [];
                recorder = new MediaRecorder(stream, { mimeType: mimeType });

                recorder.ondataavailable = event => chunks.push(event.data);

                recorder.onstop = () => {
                    console.log('Recording stopped.');
                    const blob = new Blob(chunks, { type: mimeType });
                    chunks = [];

                    const formData = new FormData();
                    formData.append('stage', stageInput.value);
                    formData.append('audio_file', blob, 'audio_record.webm');

                    submitButton.disabled = true;
                    submitButton.innerText = "Submitting...";

                    fetch('/speaking/speaking_task_2_submit', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.follow_up_question) {
                            showFollowUp(data.follow_up_question);
                            submitButton.disabled = false;
                        } else {
                            window.location.href = '/speaking/speaking_task_2_feedback';
                        }
                    })
                    .catch(err => {
                        console.error('Error uploading file:', err);
                        window.location.href = '/speaking/speaking_task_2_feedback';
                    });
                };

                recorder.start();
                let timeLeft = duration;
                timerElement.innerText = timeLeft;

                countdownInterval = setInterval(() => {
                    timeLeft--;
                    timerElement.innerText = timeLeft;

                    if (timeLeft <= 0) {
                        clearInterval(countdownInterval);
                        recorder.stop();
                    }
                }, 1000);
            })
            .catch(err => console.error('Error accessing microphone:', err));
    }

    function showFollowUp(question) {
        mainTask.classList.add('d-none');
        followUp.classList.remove('d-none');
        document.getElementById('follow-up-question').textContent = question;
        stageInput.value = 'follow_up';
        isMainTask = false;
        submitButton.innerText = "Submit recording and get feedback";
    }

    startButton.addEventListener('click', function() {
        this.disabled = true;
        startRecording(120, countdownTimer, 'follow_up');
    });

    startFollowUpButton.addEventListener('click', function() {
        this.disabled = true;
        startRecording(30, followUpTimer, 'feedback');
    });

    const form = document.querySelector('form');
    form.onsubmit = function(event) {
        event.preventDefault();
        if (recorder && recorder.state === "recording") {
            clearInterval(countdownInterval);
            recorder.stop();
        }
        return false; // Prevent form from submitting normally
    };
});