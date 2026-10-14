const questions =
    JSON.parse(document.getElementById("questions-data").textContent);

const deadline =
    JSON.parse(document.getElementById("deadline").textContent);

const attemptId =
    JSON.parse(document.getElementById("attempt-id").textContent);

let currentQuestion = 0;
const answers = {};

// Expose to window so palette sync in template can read them
window.__questions = questions;
window.__answers = answers;
window.__currentQuestion = currentQuestion;

window.__goTo = function(index) {
    currentQuestion = index;
    window.__currentQuestion = currentQuestion;
    renderQuestion();
};

const questionNumber = document.getElementById("question-number");
const questionText   = document.getElementById("question-text");

// New structure: option wrapper + inner text span
const optionEls = {
    A: document.getElementById("option-A"),
    B: document.getElementById("option-B"),
    C: document.getElementById("option-C"),
    D: document.getElementById("option-D"),
};
const optionTextEls = {
    A: document.getElementById("option-A-text"),
    B: document.getElementById("option-B-text"),
    C: document.getElementById("option-C-text"),
    D: document.getElementById("option-D-text"),
};

// Fallback: old single-element structure (no inner spans)
function setOptionText(letter, text) {
    if (optionTextEls[letter]) {
        optionTextEls[letter].textContent = text;
    } else if (optionEls[letter]) {
        optionEls[letter].textContent = letter + '. ' + text;
    }
}

// Render markdown safely + highlight code blocks
function renderMarkdown(targetEl, rawText) {
    if (!targetEl) return;
    var raw = rawText || '';

    var htmlFromMd;
    if (typeof marked !== 'undefined') {
        htmlFromMd = marked.parse(raw);
    } else {
        // Fallback if marked fails to load
        htmlFromMd = raw
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');
    }

    if (typeof DOMPurify !== 'undefined') {
        targetEl.innerHTML = DOMPurify.sanitize(htmlFromMd);
    } else {
        targetEl.innerHTML = htmlFromMd;
    }

    // Syntax-highlight any code blocks
    if (typeof hljs !== 'undefined') {
        targetEl.querySelectorAll('pre code').forEach(function(block) {
            hljs.highlightElement(block);
        });
    }
}

const prevBtn   = document.getElementById("prev-btn");
const nextBtn   = document.getElementById("next-btn");
const submitBtn = document.getElementById("submit-btn");
const timer     = document.getElementById("timer");


function renderQuestion() {
    const question = questions[currentQuestion];

    questionNumber.textContent =
        `Question ${currentQuestion + 1} of ${questions.length}`;

    // Render markdown → sanitized HTML
    renderMarkdown(questionText, question.question_desc);

    // ⚡ Append question image if present
    if (question.question_image) {
        const img = document.createElement('img');
        img.src = question.question_image;
        img.alt = 'Question diagram';
        img.className = 'q-diagram';
        questionText.appendChild(img);
    }

    setOptionText('A', question.option_a);
    setOptionText('B', question.option_b);
    setOptionText('C', question.option_c);
    setOptionText('D', question.option_d);

    prevBtn.disabled = (currentQuestion === 0);

    if (currentQuestion === questions.length - 1) {
        nextBtn.style.display = "none";
        submitBtn.style.display = "block";
    } else {
        nextBtn.style.display = "block";
        submitBtn.style.display = "none";
    }

    showSelectedAnswer();
    window.__currentQuestion = currentQuestion;
}


function selectAnswer(answer) {
    const questionId = questions[currentQuestion].id;
    answers[questionId] = answer;
    showSelectedAnswer();
}


function showSelectedAnswer() {
    const questionId = questions[currentQuestion].id;
    const selected = answers[questionId];

    ['A','B','C','D'].forEach(function(letter) {
        const el = optionEls[letter];
        if (!el) return;
        el.classList.toggle('selected', selected === letter);
    });
}


// Bind click handlers
['A','B','C','D'].forEach(function(letter) {
    const el = optionEls[letter];
    if (el) el.addEventListener('click', function() { selectAnswer(letter); });
});

nextBtn.addEventListener("click", function() {
    if (currentQuestion < questions.length - 1) {
        currentQuestion++;
        window.__currentQuestion = currentQuestion;
        renderQuestion();
    }
});

prevBtn.addEventListener("click", function() {
    if (currentQuestion > 0) {
        currentQuestion--;
        window.__currentQuestion = currentQuestion;
        renderQuestion();
    }
});


// ---- TIMER ----
let timerStarted = false;

function updateTimer() {
    const timeRemaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    timer.textContent = minutes + ':' + String(seconds).padStart(2, '0');

    if (timeRemaining === 0 && timerStarted) {
        clearInterval(timerInterval);
        submitTest(false);
    }
    timerStarted = true;
}

const timerInterval = setInterval(updateTimer, 1000);


// ---- SUBMISSION ----
let isSubmitting = false;

function getCookie(name) {
    const value = '; ' + document.cookie;
    const parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function submitTest(confirmBeforeSubmit) {
    if (isSubmitting) return;

    if (confirmBeforeSubmit) {
        const answeredCount   = Object.keys(answers).length;
        const unansweredCount = questions.length - answeredCount;
        let message = 'Are you sure you want to submit the test?';
        if (unansweredCount > 0) {
            message += '\n\nYou have ' + unansweredCount +
                ' unanswered question' + (unansweredCount === 1 ? '' : 's') + '.';
        }
        if (!window.confirm(message)) return;
    }

    isSubmitting = true;
    window.__submitting = true;
    clearInterval(timerInterval);
    timer.textContent = 'Submitting…';

    let csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) csrfToken = input.value;
    }

    const lowercasedAnswers = {};
    for (const qid in answers) {
        lowercasedAnswers[qid] = answers[qid].toLowerCase();
    }

    const body = new URLSearchParams();
    body.append('attempt_id', attemptId);
    body.append('answers', JSON.stringify(lowercasedAnswers));

    fetch('/mocktests/submit_test/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body.toString(),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.success) {
            window.location.replace(data.redirect_url);
        } else {
            isSubmitting = false;
            window.__submitting = false;
            alert(data.message || 'Submission failed.');
            timer.textContent = 'Error';
        }
    })
    .catch(function(err) {
        console.error('Submit error:', err);
        isSubmitting = false;
        window.__submitting = false;
        alert('Network error. Please try again.');
        timer.textContent = 'Error';
    });
}

submitBtn.addEventListener("click", function() { submitTest(true); });

renderQuestion();
updateTimer();