// waits for all html to load before running
document.addEventListener('DOMContentLoaded', function() {
    // waits 5 seconds then 'fades' all alerts
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.classList.add('fade');
        });
    }, 5000);

    // render the quiz if quizData is avilable
    if (typeof quizData !== 'undefined' && quizData.length > 0) {
        renderQuiz(quizData);
    }

    // handle quiz submission
    const quizForm = document.getElementById('quiz-form');
    if (quizForm) {
        renderQuiz(quizData);

        quizForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevents page from reloading on submission

            // Collect user responses
            const formData = new FormData(quizForm);
            const responses = {};

            // Iterate over form entries and build the responses object
            for (let [name, value] of formData.entries()) {
                responses[name] = value;
            }

            // Frontend validation: Ensures all questions are answered
            const totalQuestions = quizData.length;
            let answeredQuestions = 0;

            for (let i = 0; i < totalQuestions; i++) {
                if (responses[`question_${i}`]) {
                    answeredQuestions += 1;
                }
            }

            if (answeredQuestions < totalQuestions) {
                alert('Please answer all questions before submitting the quiz.');
                return;
            }

            // Send responses to the backend for validation
            fetch('/submit_quiz', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrf_token') // Ensure CSRF protection
                },
                body: JSON.stringify({
                    article_id: quizForm.dataset.articleId, // Pass article ID
                    responses: responses
                })
            })
            .then(response => response.json())
            // feedback
            .then(data => {
                const resultsDiv = document.getElementById('quiz-results');
                if (data.status === 'success') {
                    let feedbackHTML = `<div class="alert alert-success">You scored ${data.score} out of ${data.total}.</div>`;
                    feedbackHTML += `<ul class="list-group">`;
                    data.feedback.forEach((item, index) => {
                        feedbackHTML += `
                            <li class="list-group-item">
                                <strong>Question ${index + 1}:</strong> ${item.question}<br>
                                <strong>Your Answer:</strong> ${item.your_answer}<br>
                                <strong>Correct Answer:</strong> ${item.correct_answer}<br>
                                ${item.is_correct ? '<span class="text-success">Correct</span>' : '<span class="text-danger">Incorrect</span>'}
                            </li>
                        `;
                    });
                    feedbackHTML += `</ul>`;
                    resultsDiv.innerHTML = feedbackHTML;

                    // Disable the form to prevent resubmission
                    quizForm.querySelectorAll('input').forEach(input => input.disabled = true);
                    quizForm.querySelector('button[type="submit"]').disabled = true;
                } else {
                    resultsDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const resultsDiv = document.getElementById('quiz-results');
                resultsDiv.innerHTML = `<div class="alert alert-danger">An error occurred while submitting your quiz. Please try again later.</div>`;
            });
        });
    }
});

// Function to render the quiz
function renderQuiz(quizData) {
    const quizQuestionsDiv = document.getElementById('quiz-questions');

    // Clear any existing content to prevent duplication
    quizQuestionsDiv.innerHTML = '';

    quizData.forEach((questionObj, index) => {
        // Create question container
        const questionDiv = document.createElement('div');
        questionDiv.classList.add('mb-4');

        // Question text
        const questionText = document.createElement('p');
        questionText.innerHTML = `<strong>Question ${index + 1}:</strong> ${questionObj.question}`;
        questionDiv.appendChild(questionText);

        // Options
        questionObj.options.forEach((option, optionIndex) => {
            const optionId = `q${index}_option${optionIndex}`;

            // Option container
            const optionDiv = document.createElement('div');
            optionDiv.classList.add('form-check');

            // Radio input
            const optionInput = document.createElement('input');
            optionInput.classList.add('form-check-input');
            optionInput.type = 'radio';
            optionInput.name = `question_${index}`; // Use a unique name per question
            optionInput.id = optionId;
            optionInput.value = option;

            // Option label
            const optionLabel = document.createElement('label');
            optionLabel.classList.add('form-check-label');
            optionLabel.htmlFor = optionId;
            optionLabel.textContent = option;

            // Append input and label to optionDiv
            optionDiv.appendChild(optionInput);
            optionDiv.appendChild(optionLabel);

            // Append optionDiv to questionDiv
            questionDiv.appendChild(optionDiv);
        });

        // Append questionDiv to quizQuestionsDiv
        quizQuestionsDiv.appendChild(questionDiv);
    });
}

// // Handle Quiz Submission
// const quizForm = document.getElementById('quiz-form');
// if (quizForm) {
//     // Render the quiz once
//     renderQuiz(quizData);

//     quizForm.addEventListener('submit', function(event) {
//         event.preventDefault(); // Prevent default form submission

//         // Collect user responses
//         const formData = new FormData(quizForm);
//         const responses = {};

//         // Iterate over form entries and build the responses object
//         for (let [name, value] of formData.entries()) {
//             responses[name] = value;
//         }

//         // Frontend validation: Ensure all questions are answered
//         const totalQuestions = quizData.length;
//         let answeredQuestions = 0;

//         for (let i = 0; i < totalQuestions; i++) {
//             if (responses[`question_${i}`]) {
//                 answeredQuestions += 1;
//             }
//         }

//         if (answeredQuestions < totalQuestions) {
//             alert('Please answer all questions before submitting the quiz.');
//             return;
//         }

//         // Send responses to the backend for validation
//         fetch('/submit_quiz', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//                 'X-CSRFToken': getCookie('csrf_token') // Ensure CSRF protection
//             },
//             body: JSON.stringify({
//                 article_id: quizForm.dataset.articleId, // Pass article ID
//                 responses: responses
//             })
//         })
//         .then(response => response.json())
//         .then(data => {
//             const resultsDiv = document.getElementById('quiz-results');
//             if (data.status === 'success') {
//                 let feedbackHTML = `<div class="alert alert-success">You scored ${data.score} out of ${data.total}.</div>`;
//                 feedbackHTML += `<ul class="list-group">`;
//                 data.feedback.forEach((item, index) => {
//                     feedbackHTML += `
//                         <li class="list-group-item">
//                             <strong>Question ${index + 1}:</strong> ${item.question}<br>
//                             <strong>Your Answer:</strong> ${item.your_answer}<br>
//                             <strong>Correct Answer:</strong> ${item.correct_answer}<br>
//                             ${item.is_correct ? '<span class="text-success">Correct</span>' : '<span class="text-danger">Incorrect</span>'}
//                         </li>
//                     `;
//                 });
//                 feedbackHTML += `</ul>`;
//                 resultsDiv.innerHTML = feedbackHTML;

//                 // Disable the form to prevent resubmission
//                 quizForm.querySelectorAll('input').forEach(input => input.disabled = true);
//                 quizForm.querySelector('button[type="submit"]').disabled = true;
//             } else {
//                 resultsDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
//             }
//         })
//         .catch(error => {
//             console.error('Error:', error);
//             const resultsDiv = document.getElementById('quiz-results');
//             resultsDiv.innerHTML = `<div class="alert alert-danger">An error occurred while submitting your quiz. Please try again later.</div>`;
//         });
//     });
// }

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}