document.addEventListener('DOMContentLoaded', function () {

    const uploadForm = document.getElementById('uploadForm');
    const loadingDiv = document.getElementById('loading');

    if (uploadForm)
        uploadForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);


            if (loadingDiv) {
                loadingDiv.style.display = 'block';
            }

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (loadingDiv) {
                    loadingDiv.style.display = 'none';
                }
                if (data.questions) {
                    displayQuestions(data.questions);
                } else if (data.error) {
                    alert(data.error);
                }
            })
            .catch(error => {
                if (loadingDiv) {
                    loadingDiv.style.display = 'none';
                }
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            });
        });


    // Handle form submission for JobFit Coach
    const jobFitForm = document.getElementById('jobFitForm');

    if (jobFitForm) {
        jobFitForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const role = document.getElementById('role').value;
            const location = document.getElementById('location').value;


            console.log(`Role: ${role}, Location: ${location}`);

            // Call the API to get job recommendations based on role and location
            fetch('/jobfit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ role, location })
            })
            .then(response => response.json())
            .then(data => {
                const jobListDiv = document.getElementById('job-list');
                if (jobListDiv) {
                    jobListDiv.innerHTML = '';

                    if (data.jobs && data.jobs.length > 0) {
                        data.jobs.forEach(job => {
                            const jobItem = document.createElement('div');
                            jobItem.classList.add('job-item');
                            jobItem.innerHTML = `<h3>${job.title}</h3><p>${job.company}</p><p>${job.location}</p><p>${job.description}</p>`;
                            jobListDiv.appendChild(jobItem);
                        });
                    } else {
                        jobListDiv.innerHTML = '<p>No job recommendations found.</p>';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error fetching job recommendations.');
            });
        });
    }

    // Function to display questions on the frontend
    function displayQuestions(questions) {
        const questionsList = document.getElementById("questions-list");
        if (questionsList) {
            questionsList.innerHTML = "";

            if (questions.length > 0) {
                questions.forEach((question, index) => {
                    const listItem = document.createElement("li");
                    listItem.textContent = `Q${index + 1}: ${question}`;
                    questionsList.appendChild(listItem);
                });
            } else {
                questionsList.innerHTML = "<li>No questions generated.</li>";
            }
        }
    }
});

//online test platform...


let userId = null;
let cheatAttempts = 0;

// Handle User Registration
document.getElementById('user-info-form').addEventListener('submit', (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email })
    })
        .then(response => {
            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            return response.json();
        })
        .then(data => {
            userId = data.user_id;
            alert('Registration successful! Proceed to select test settings.');
            document.getElementById('user-info-form').style.display = 'none';
            document.getElementById('test-settings-form').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Registration failed. Please try again.');
        });
});

// Start Test
document.getElementById('test-settings-form').addEventListener('submit', (e) => {
    e.preventDefault();

    const difficulty = document.getElementById('difficulty').value;

    fetch('/get-questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ difficulty })
    })
        .then(response => {
            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.questions && data.questions.length > 0) {
                displayQuestions(data.questions);
                document.getElementById('test-settings-form').style.display = 'none';
                document.getElementById('test-container').style.display = 'block';
                startTimer(05);
                monitorCheating();
            } else {
                alert('No questions available for the selected difficulty.');
            }
        })
        .catch(error => console.error('Error:', error));
});

// Display Questions
function displayQuestions(questions) {
    const questionsList = document.getElementById('questions-list');
    questionsList.innerHTML = '';
    questions.forEach((q, index) => {
        const questionDiv = document.createElement('div');
        questionDiv.innerHTML = `
            <p><strong>Q${index + 1}:</strong> ${q.question_text}</p>
            ${generateOptions(q.options, q.id)}
        `;
        questionsList.appendChild(questionDiv);
    });
}

// Generate Options for MCQs
function generateOptions(optionsJSON, questionId) {
    const options = JSON.parse(optionsJSON || '{}');
    return Object.entries(options).map(([key, value]) => `
        <label>
            <input type="radio" name="question_${questionId}" value="${key}">
            ${key}: ${value}
        </label>
    `).join('<br>');
}

// Timer Functionality
function startTimer(minutes) {
    let timeLeft = minutes * 60;
    const timerInterval = setInterval(() => {
        const minutesLeft = Math.floor(timeLeft / 60);
        const secondsLeft = timeLeft % 60;
        document.getElementById('timer-value').textContent = `${minutesLeft}:${secondsLeft.toString().padStart(2, '0')}`;
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            submitTest(true);
        }
        timeLeft--;
    }, 1000);
}

// Monitor Cheating
function monitorCheating() {
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            cheatAttempts++;
            logCheatingAction("toggle");
            alert(`You switched tabs. Attempt ${cheatAttempts} recorded.`);
        }
    });

    document.addEventListener("copy", (e) => {
        e.preventDefault();
        logCheatingAction("copy");
        alert("Copying is not allowed!");
    });

    document.addEventListener("paste", (e) => {
        e.preventDefault();
        logCheatingAction("paste");
        alert("Pasting is not allowed!");
    });
}

// Log Cheating Action
function logCheatingAction(action) {
    fetch("/check-cheating", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
    })
        .then((response) => {
            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            return response.json();
        })
        .then((data) => {
            if (data.cheating_detected) {
                alert(data.message);
                submitTest(true); // Auto-submit the test if cheating detected
            }
        })
        .catch((error) => console.error("Error logging cheating action:", error));
}

// Submit Test
document.getElementById('submit-test').addEventListener('click', () => submitTest());

function submitTest(autoSubmit = false) {
    const answers = {};
    document.querySelectorAll('input[type="radio"]:checked').forEach(input => {
        const questionId = input.name.split('_')[1];
        answers[questionId] = input.value;
    });

    fetch('/submit-answers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, answers })
    })
        .then(response => {
            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            return response.json();
        })
        .then(data => {
            alert(autoSubmit ? 'Test auto-submitted due to time or cheating.' : 'Test submitted successfully!');
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to submit test.');
        });
}

//login and registration.....
function myMenuFunction() {
    var i = document.getElementById("navMenu");
    if(i.className === "nav-menu") {
        i.className += " responsive";
    } else {
        i.className = "nav-menu";
    }
}

function showLogin() {
    console.log("Switching to Login form");
    document.getElementById("login").style.left = "4px";
    document.getElementById("registeration").style.right = "-520px";
    document.getElementById("loginBtn").classList.add("white-btn");
    document.getElementById("registerBtn").classList.remove("white-btn");
}

function showRegister() {
    console.log("Switching to Register form");
    document.getElementById("login").style.left = "-510px";
    document.getElementById("registeration").style.right = "5px";
    document.getElementById("loginBtn").classList.remove("white-btn");
    document.getElementById("registerBtn").classList.add("white-btn");
}
