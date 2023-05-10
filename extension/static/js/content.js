
chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    switch (request._action) {
        case "createPopup":
            let mot = request.mot
            let context = getSurroundingText(mot)
            console.log(context)
            getGifsAndCreatePopup(mot, context)
            sendResponse({ status: "ok" });
            break;
    }
});

function getGifsAndCreatePopup(mot, context) {
    fetch("http://127.0.0.1:5000/translate", {
        method: "POST",
        headers: new Headers({
            "Content-Type": "application/json"
        }),
        body: JSON.stringify({ selected_word: mot, contextWords: context })
    })
        .then(response => response.json())
        .then(data => {
            let gifs = data.corpus;
            let group = data.groupName;

            console.log(gifs);
            if (gifs.length === 0) {

                //faire un modal pour ici
                createModalError(mot)
            } else {
                createModal(mot, gifs, group)
            }
        });
}

function createModal(mot, gifs, group) {
    // Create modal elements
    const modal = document.createElement('div');
    modal.className = "modal12";
    //modal.classList.add('modal');
    const modalContent = document.createElement('div');
    modalContent.className = "modal12-content"
    //modalContent.classList.add('modal-content');
    // Create heading
    const wordFound = document.createElement('h3');
    wordFound.innerHTML = "Les traductions LSFB possibles du mot : " + mot
    // Create navbar
    const navbar = document.createElement('div');
    navbar.classList.add('navbar');

    // Create icon
    const image = document.createElement('img');
    image.src = 'https://dico.corpus-lsfb.be/logo.5345690b.svg';
    image.alt = 'Logo';
    navbar.appendChild(image);
    // Create close button
    const closeButton = document.createElement('span');
    closeButton.classList.add('close');
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', function () {
        // Remove modal from the DOM when close button is clicked
        modal.remove();
    });
    navbar.appendChild(closeButton)

    //gif
    const gifImage = document.createElement('img');
    gifImage.classList.add('gif-image');

    // gloss and keyword(s)
    const glossName = document.createElement('span');
    const keywords = document.createElement('p');
    //sources and authors
    const source = document.createElement('p');
    const author = document.createElement('p');
    //button previous
    const prevButton = document.createElement('button');
    prevButton.classList.add('prev-button');
    prevButton.innerText = 'Précédent';
    //button next
    const nextButton = document.createElement('button');
    nextButton.classList.add('next-button');
    nextButton.innerText = 'Suivant';
    // add button to open a new tab with examples
    const exampleButton = document.createElement('a');
    exampleButton.classList.add('example-button');
    exampleButton.innerText = 'Voir exemple(s)';
    exampleButton.target = "_blank";

    // add to history button
    const historyButton = document.createElement('button');
    historyButton.classList.add('history-button');
    historyButton.innerText = 'Ajout à l\'historique';

    let svg=document.createElement('div')
    svg.id='svg-container' 

    // Add event listeners to previous and next buttons
    let currentGifIndex = 0;
    prevButton.addEventListener('click', () => {
        currentGifIndex = (currentGifIndex - 1 + gifs.length) % gifs.length;
        gifImage.src = gifs[currentGifIndex][1];
        glossName.innerHTML = gifs[currentGifIndex][0]
        keywords.innerHTML = gifs[currentGifIndex][2]
        source.innerHTML = "Source : ".concat(gifs[currentGifIndex][4])
        author.innerHTML = "Auteur : ".concat(gifs[currentGifIndex][3])
        exampleButton.href = 'https://dico.corpus-lsfb.be/plugin?gloss='.concat(gifs[currentGifIndex][0]);

        if (gifs[currentGifIndex][4] !== "CorpusLSFB") {
            exampleButton.style.display = "none"
        } else {
            exampleButton.style.display = "block";
        }
        if (group === 'Public') {
            historyButton.style.display = "none";
        } else {
            historyButton.style.display = "block";
            historyButton.disabled = false;
            historyButton.innerHTML = "Ajout à l\'historique"
        }


    });

    nextButton.addEventListener('click', () => {
        currentGifIndex = (currentGifIndex + 1) % gifs.length;
        gifImage.src = gifs[currentGifIndex][1];
        glossName.innerHTML = gifs[currentGifIndex][0]
        keywords.innerHTML = gifs[currentGifIndex][2]
        source.innerHTML = "Source : ".concat(gifs[currentGifIndex][4])
        author.innerHTML = "Auteur : ".concat(gifs[currentGifIndex][3])
        exampleButton.href = 'https://dico.corpus-lsfb.be/plugin?gloss='.concat(gifs[currentGifIndex][0]);

        if (gifs[currentGifIndex][4] !== "CorpusLSFB") {
            exampleButton.style.display = "none"
        } else {
            exampleButton.style.display = "block";
        }
        if (group === 'Public') {
            historyButton.style.display = "none";
        } else {
            historyButton.style.display = "block";
            historyButton.disabled = false;
            historyButton.innerHTML = "Ajout à l\'historique"
        }
    });

    // Set initial GIF image source
    gifImage.src = gifs[currentGifIndex][1];
    glossName.innerHTML = "Gloss : ".concat(gifs[currentGifIndex][0]);
    keywords.innerHTML = "Mots-clés : ".concat(gifs[currentGifIndex][2]);
    source.innerHTML = "Source : ".concat(gifs[currentGifIndex][4]);
    author.innerHTML = "Auteur : ".concat(gifs[currentGifIndex][3]);
    exampleButton.href = 'https://dico.corpus-lsfb.be/plugin?gloss='.concat(gifs[currentGifIndex][0]);

    const br = document.createElement('br');
    if (gifs[currentGifIndex][4] !== "CorpusLSFB") {
        exampleButton.style.display = "none";
    } else { exampleButton.style.display = "block"; }
    historyButton.addEventListener('click', function () {
        fetch("http://127.0.0.1:5000/addHistory", {
            method: "POST",
            headers: new Headers({
                "Content-Type": "application/json"
            }),
            body: JSON.stringify({ gloss_name: gifs[currentGifIndex][0], keywords: gifs[currentGifIndex][2], url: gifs[currentGifIndex][1], selected_word: mot })
        })
            .then(response => response.json())
            .then(data => {
                historyButton.disabled = true;
                historyButton.innerHTML = data;
                var svgContainer = document.getElementById("svg-container");
                var svgElement = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                // Définir le contenu SVG comme le code fourni
                svgElement.innerHTML = '<svg fill="#000000" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="25px" height="25px" viewBox="0 0 381.322 381.322" xml:space="preserve"><g><path d="M296.582,6.053v369.21c0,2.376-1.383,4.516-3.534,5.503c-0.804,0.372-1.667,0.55-2.518,0.55 c-1.419,0-2.838-0.503-3.961-1.472l-95.907-82.84l-95.912,82.84c-1.797,1.554-4.327,1.921-6.475,0.922 c-2.148-0.987-3.535-3.127-3.535-5.503V6.053C84.741,2.704,87.445,0,90.793,0H290.53C293.875,0,296.582,2.704,296.582,6.053z"/></g></svg>';
                svgContainer.appendChild(svgElement);
            });
    });
    if (group === 'Public') {
        historyButton.style.display = "none";
    } else {
        historyButton.style.display = "block";
        historyButton.disabled = false;
        historyButton.innerHTML = "Ajout à l\'historique"
    }

    // Add elements to modal content
    modalContent.appendChild(navbar);
    modalContent.appendChild(wordFound);
    modalContent.appendChild(gifImage);
    modalContent.appendChild(br)
    modalContent.appendChild(prevButton);
    modalContent.appendChild(nextButton);
    modalContent.appendChild(br)
    modalContent.appendChild(glossName);
    modalContent.appendChild(keywords);
    //modalContent.appendChild(br);
    modalContent.appendChild(source);
    modalContent.appendChild(author);
    modalContent.appendChild(svg);
    modalContent.appendChild(historyButton);
    modalContent.appendChild(exampleButton);


    // Add modal content to modal and add modal to document
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
}


function createModalError(mot) {
    console.log("createModalError")

    // Create modal background
    const modal = document.createElement('div');
    modal.classList.add('modal12');

    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.classList.add('modal12-content');

    // Create navbar
    const navbar = document.createElement('div');
    navbar.classList.add('navbar');

    // Create icon
    const image = document.createElement('img');
    image.src = 'https://dico.corpus-lsfb.be/logo.5345690b.svg';
    image.alt = 'Logo';
    navbar.appendChild(image);
    // Create close button
    const closeButton = document.createElement('span');
    closeButton.classList.add('close');
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', function () {
        // Remove modal from the DOM when close button is clicked
        modal.remove();
    });
    navbar.appendChild(closeButton)

    modalContent.appendChild(navbar)
    // Create heading
    const wordMissing = document.createElement('h3');
    wordMissing.innerHTML = "La traduction LSFB mot \"" + mot + "\" n'a pas été trouvée :( ";
    modalContent.appendChild(wordMissing);


    // Create GIF image
    const gifImage = document.createElement('img');
    gifImage.classList.add('modal-image');
    gifImage.src = "https://corpus-lsfb.be/img/pictures/signe_a6c6abc5828211bf536bb341fee37f05.gif"
    modalContent.appendChild(gifImage);

    // Create button
    const button = document.createElement('button');
    button.classList.add('newSign-button');
    button.innerText = 'Proposer un signe';
    button.addEventListener('click', function () {
        // Remove modal
        modal.remove();

        window.open("http://127.0.0.1:5000/upload/" + mot, "_blank");


    });
    const br = document.createElement('br');
    modalContent.appendChild(br)
    modalContent.appendChild(button);

    // Add modal content to modal background
    modal.appendChild(modalContent);
    // Add modal to the DOM
    console.log("createModalErrorEnd");
    document.body.appendChild(modal);
}


function getSurroundingText(selectedText) {
    let parentNode = window.getSelection().anchorNode.parentNode;
    let paragraph = parentNode.textContent;
    //console.log(paragraph)
    const words_1 = paragraph.split(" ");
    console.log(words_1)
    const substringIndex = words_1.indexOf(selectedText.split(" ")[0]);

    // slice the words array to exclude the substring
    const words_tmp = words_1.slice(0, substringIndex).concat(selectedText);
    const words = words_tmp.concat(words_1.slice(words_tmp.length))
    console.log(substringIndex)

    if (substringIndex !== -1) {
        const start = Math.max(0, substringIndex - 4);

        const end = Math.min(substringIndex + 4, words.length);
        const surroundingWords = words.slice(start, end);

        const strValue = surroundingWords.join(' ');
        console.log(strValue);
        return strValue
    }
    return " "


}