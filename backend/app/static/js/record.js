let startButton = document.getElementById("record");//start the record
let stopButton = document.getElementById("stop");//stop the record
let retryButton = document.getElementById("retry");//mauvais signe ? => recommencer la video
retryButton.style.visibility="hidden"
const validateButton = document.createElement('button'); // valider et sauvegarder l enregistrement
validateButton.innerText = "v"
let preview = document.getElementById("vidBox");

stopButton.disabled = true;
retryButton.disabled = true;
validateButton.disabled = true;


const recTime = 6000; // 6 secondes

/*
  We use this function to start the record of the video
  Parameters:
  -----------
  stream : a MediaStream 
  */
function startRecording(stream, length) {

  return new Promise((resolve) => {
    recorder = new MediaRecorder(stream); //create the media recorder
    const chunks = []; //store our blob (the recorded media)

    recorder.ondataavailable = (event) => chunks.push(event.data);


    var clicked = false
    document.getElementById('retry').addEventListener("click", function () {
      clicked = true
    });

    recorder.addEventListener('stop', () => {

      const recordedBlob = new Blob(chunks, { type: 'video/mp4' });
      const recMediaFile = document.createElement('video');
      recMediaFile.setAttribute("id", "vid")
      recMediaFile.src = URL.createObjectURL(recordedBlob);
      recMediaFile.controls = true;
      recMediaFile.autoplay = true;

      // Afficher le fichier enregistré
      document.getElementById('recorder').appendChild(recMediaFile);
      document.getElementById('recorder').appendChild(validateButton);

      // Afficher les boutons "retry" et "valider"
      retryButton.disabled = false;
      validateButton.disabled = false;

      // Envoyer le fichier enregistré si "valider" est appuyé
      validateButton.addEventListener('click', () => {
        console.log("ici1")
        const filename = document.getElementById('mot_record').textContent;
        var formData = new FormData();
        let keywordsInputButton = document.getElementById("keywordsInput");
        //let keywordsInput = keywordsInputButton.value()
        let saveKeywords =document.getElementById("saveKeyword");
        //let valuesKeywords = "Pas de mots-clés";
        let valuesKeywords = keywordsInputButton.value;
        if (valuesKeywords === " "){
          valuesKeywords = "Pas de mots-clés"
        }
        /*saveKeywords.addEventListener('click', () => {
          console.log("ici2")
          valuesKeywords = keywordsInputButton.value;
          alert(valuesKeywords)
        });*/
        let mot_keywords = {keywords:valuesKeywords}
        const blob_mot_keywords = new Blob([JSON.stringify(mot_keywords)], { type: 'application/json' });

        formData.append('video', recordedBlob, filename);
        formData.append('keywords', blob_mot_keywords, valuesKeywords);

        if (clicked) { formData = null }
        fetch('http://127.0.0.1:5000/upload/' + filename, {
          method: 'POST',

          body: formData,
          mode: 'no-cors',
        }).then(() => resolve(chunks));
      });
    });

    recorder.start();

    if (length) {
      setTimeout(() => {
        if (recorder.state === "recording") {
          recorder.stop();
        }
      }, length);
    }
  });
}

function startTimer() {

  /*
  This is a function that starts a countdown timer for 3 seconds before starting
  the recording. We use it to let people prepare themselves before signing
  */

  var counter = 3;
  var timer = setInterval(function () {

    $('#countdown').remove();

    var countdown = $('<span id="countdown">' + (counter === 0 ? '' : counter) + '</span>');

    countdown.appendTo($('.container'));
    setTimeout(() => {
      if (counter > -1) {
        $('#countdown').css({ 'font-size': '40vw', 'opacity': 0 });
      } else {
        $('#countdown').css({ 'font-size': '10vw', 'opacity': 50 });
      }
    }, 20);
    counter--;
    if (counter === -1) clearInterval(timer);
  }, 1000);
}

startButton.addEventListener('click', async () => {

  stopButton.disabled = false;
  retryButton.disabled = true;
  validateButton.disabled = true;
  retryButton.style.visibility ='hidden'


  // Demander l'accès à la caméra
  const stream = await navigator.mediaDevices.getUserMedia({
    video: true,
    audio: false,
  });
  startTimer();
  setTimeout(async () => {
    try {
      preview.srcObject = stream;
      preview.captureStream = preview.captureStream || preview.mozCaptureStream;
      await new Promise((resolve) => (preview.onplaying = resolve));
      return startRecording(preview.captureStream(),recTime);
    }
    catch (error) {
      console.error('getUserMedia error:', error);
    }
  }, 4000)
});

function stopRec(stream) {
  stream.getTracks().forEach((track) => { track.stop(); })
}

stopButton.addEventListener('click', () => {
  stopButton.disabled = true;
  retryButton.disabled = false;
  validateButton.disabled = false;
  stopRec(preview.srcObject);
  retryButton.style.visibility = "visible"
});

retryButton.addEventListener('click', () => {
  const vid = document.querySelector('#vid');
  vid.remove();
  startButton.disabled = false;
  retryButton.disabled = true;
  validateButton.disabled = true;
  retryButton.style.visibility="hidden"

  startButton.click();
  startButton.disabled = true;
});
