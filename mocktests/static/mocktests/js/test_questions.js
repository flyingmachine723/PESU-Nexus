const review =
    JSON.parse(document.getElementById("review-data").textContent);

let currentQuestion = 0;

const questionCard   = document.getElementById("question-card");
const questionNumber = document.getElementById("question-number");
const questionText   = document.getElementById("question-text");
const explanationText = document.getElementById("explanation-text");
const prevBtn        = document.getElementById("prev-btn");
const nextBtn        = document.getElementById("next-btn");
const pageIndicator  = document.getElementById("page-indicator");
const paletteGrid    = document.getElementById("palette-grid");

const optionRefs = {
    "A": { box: document.getElementById("option-A"), text: document.getElementById("option-A-text"), tag: document.getElementById("option-A-tag") },
    "B": { box: document.getElementById("option-B"), text: document.getElementById("option-B-text"), tag: document.getElementById("option-B-tag") },
    "C": { box: document.getElementById("option-C"), text: document.getElementById("option-C-text"), tag: document.getElementById("option-C-tag") },
    "D": { box: document.getElementById("option-D"), text: document.getElementById("option-D-text"), tag: document.getElementById("option-D-tag") },
};


// Render markdown safely + highlight code blocks
function renderMarkdown(targetEl, rawText) {
    if (!targetEl) return;
    var raw = rawText || '';

    var htmlFromMd;
    if (typeof marked !== 'undefined') {
        htmlFromMd = marked.parse(raw);
    } else {
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

    if (typeof hljs !== 'undefined') {
        targetEl.querySelectorAll('pre code').forEach(function(block) {
            hljs.highlightElement(block);
        });
    }
}


function buildPalette() {
    if (!paletteGrid) return;
    paletteGrid.innerHTML = '';
    review.forEach(function(item, i) {
        var btn = document.createElement('button');
        var cls = 'p-btn';
        if (item.selected === null) cls += ' p-skip';
        else if (item.is_correct)  cls += ' p-correct';
        else                        cls += ' p-wrong';
        if (i === currentQuestion)  cls += ' p-current';
        btn.className = cls;
        btn.textContent = i + 1;
        btn.onclick = function() { currentQuestion = i; renderQuestion(); };
        paletteGrid.appendChild(btn);
    });
}


function renderQuestion() {
    var item = review[currentQuestion];

    // Card border
    questionCard.classList.remove("correct-border", "wrong-border", "unattempted-border");
    if (item.selected === null)  questionCard.classList.add("unattempted-border");
    else if (item.is_correct)    questionCard.classList.add("correct-border");
    else                         questionCard.classList.add("wrong-border");

    questionNumber.textContent = 'Question ' + (currentQuestion + 1) + ' of ' + review.length;

    // Render markdown → sanitized HTML for question text
    renderMarkdown(questionText, item.question_desc);

    // ⚡ Append question image if present
    if (item.question_image) {
        const img = document.createElement('img');
        img.src = item.question_image;
        img.alt = 'Question diagram';
        img.className = 'q-diagram';
        questionText.appendChild(img);
    }

    // Reset options
    ["A","B","C","D"].forEach(function(letter) {
        var ref = optionRefs[letter];
        if (ref.text) ref.text.textContent = item["option_" + letter.toLowerCase()];
        ref.box.classList.remove("selected-correct","selected-wrong","correct-answer");
        if (ref.tag) { ref.tag.textContent = ''; ref.tag.className = 'tag'; }
    });

    // Correct answer highlight
    var correctLetter = item.correct_answer.toUpperCase();
    var correctRef = optionRefs[correctLetter];
    if (correctRef) correctRef.box.classList.add("correct-answer");

    // User's selection
    if (item.selected !== null) {
        var selectedRef = optionRefs[item.selected.toUpperCase()];
        if (selectedRef) {
            if (item.is_correct) {
                selectedRef.box.classList.add("selected-correct");
                if (selectedRef.tag) { selectedRef.tag.textContent = 'Your Answer ✓'; selectedRef.tag.className = 'tag tag-correct'; }
            } else {
                selectedRef.box.classList.add("selected-wrong");
                if (selectedRef.tag) { selectedRef.tag.textContent = 'Your Answer ✗'; selectedRef.tag.className = 'tag tag-wrong'; }
            }
        }
    }

    // Label correct when user got it wrong
    if (!item.is_correct && correctRef && correctRef.tag) {
        correctRef.tag.textContent = 'Correct Answer';
        correctRef.tag.className = 'tag tag-ref';
    }

    // Explanation — rendered as markdown too
    if (explanationText) {
        if (item.explanation) {
            renderMarkdown(explanationText, item.explanation);
        } else {
            explanationText.textContent = 'Explanation coming soon.';
        }
    }

    // Nav
    prevBtn.disabled = (currentQuestion === 0);
    nextBtn.disabled = (currentQuestion === review.length - 1);
    if (pageIndicator) pageIndicator.textContent = (currentQuestion + 1) + ' / ' + review.length;

    buildPalette();
}


prevBtn.addEventListener("click", function() {
    if (currentQuestion > 0) { currentQuestion--; renderQuestion(); }
});
nextBtn.addEventListener("click", function() {
    if (currentQuestion < review.length - 1) { currentQuestion++; renderQuestion(); }
});

renderQuestion();