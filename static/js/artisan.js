document.addEventListener("DOMContentLoaded", () => {

    // ============================================================
    // ELEMENTS
    // ============================================================

    const frontInput = document.getElementById("front-input");
    const sideInput = document.getElementById("side-input");
    const detailInput = document.getElementById("detail-input");

    const frontPreview = document.getElementById("front-preview");
    const sidePreview = document.getElementById("side-preview");
    const detailPreview = document.getElementById("detail-preview");

    const frontPlaceholder = document.getElementById("front-placeholder");
    const sidePlaceholder = document.getElementById("side-placeholder");
    const detailPlaceholder = document.getElementById("detail-placeholder");

    const continueButton =
        document.getElementById("continue-photos-button");

    const photoCountMessage =
        document.getElementById("photo-count-message");

    const uploadError =
        document.getElementById("upload-error");

    const uploadPanel =
        document.getElementById("upload-panel");

    const loadingPanel =
        document.getElementById("loading-panel");

    const comparePanel =
        document.getElementById("compare-panel");


    let selectedPhotos = {
        front: null,
        side: null,
        detail: null
    };


    // ============================================================
    // HELPERS
    // ============================================================

    function getElement(id) {
        return document.getElementById(id);
    }


    function showUploadError(message) {

        if (!uploadError) {
            alert(message);
            return;
        }

        uploadError.textContent = message;
        uploadError.style.display = "block";
    }


    function hideUploadError() {

        if (!uploadError) {
            return;
        }

        uploadError.textContent = "";
        uploadError.style.display = "none";
    }


    function formatFileSize(bytes) {

        if (bytes < 1024 * 1024) {
            return `${Math.round(bytes / 1024)} KB`;
        }

        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }


    function isValidImage(file) {

        if (!file) {
            return false;
        }

        const allowedTypes = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp"
        ];

        return allowedTypes.includes(file.type);
    }


    function isValidFileSize(file) {

        if (!file) {
            return false;
        }

        const MAX_SIZE = 8 * 1024 * 1024;

        return file.size <= MAX_SIZE;
    }


    // ============================================================
    // PHOTO COUNT
    // ============================================================

    function updatePhotoCount() {

        const photos = [
            selectedPhotos.front,
            selectedPhotos.side,
            selectedPhotos.detail
        ].filter(Boolean);

        const count = photos.length;


        if (photoCountMessage) {

            if (count === 0) {

                photoCountMessage.textContent =
                    "Please upload 3 product photos.";

            } else if (count === 1) {

                photoCountMessage.textContent =
                    "1 of 3 photos selected.";

            } else if (count === 2) {

                photoCountMessage.textContent =
                    "2 of 3 photos selected.";

            } else {

                photoCountMessage.textContent =
                    "✓ All 3 product photos are ready.";
            }
        }


        if (continueButton) {

            continueButton.disabled = count !== 3;

            if (count === 3) {
                continueButton.classList.add("ready");
            } else {
                continueButton.classList.remove("ready");
            }
        }


        updatePhotoStatus(
            "front",
            selectedPhotos.front
        );

        updatePhotoStatus(
            "side",
            selectedPhotos.side
        );

        updatePhotoStatus(
            "detail",
            selectedPhotos.detail
        );
    }


    function updatePhotoStatus(type, file) {

        const statusElement =
            getElement(`${type}-status`);

        if (!statusElement) {
            return;
        }


        if (file) {

            statusElement.textContent =
                "✓ Photo selected";

            statusElement.classList.add(
                "selected"
            );

        } else {

            statusElement.textContent =
                "Photo required";

            statusElement.classList.remove(
                "selected"
            );
        }
    }


    // ============================================================
    // PHOTO PREVIEW
    // ============================================================

    function previewPhoto(file, type) {

        if (!file) {
            return;
        }

        const preview =
            getElement(`${type}-preview`);

        const placeholder =
            getElement(`${type}-placeholder`);


        if (!preview) {
            return;
        }


        const imageURL =
            URL.createObjectURL(file);


        preview.src = imageURL;
        preview.style.display = "block";


        if (placeholder) {
            placeholder.style.display = "none";
        }


        preview.onload = () => {
            URL.revokeObjectURL(imageURL);
        };
    }


    function clearPhotoPreview(type) {

        const preview =
            getElement(`${type}-preview`);

        const placeholder =
            getElement(`${type}-placeholder`);


        if (preview) {

            preview.src = "";
            preview.style.display = "none";
        }


        if (placeholder) {
            placeholder.style.display = "";
        }
    }


    // ============================================================
    // HANDLE PHOTO SELECTION
    // ============================================================

    function handlePhotoSelection(file, type) {

        hideUploadError();


        if (!file) {
            return;
        }


        if (!isValidImage(file)) {

            showUploadError(
                "Please select a JPG, JPEG, PNG or WEBP image."
            );


            const input =
                getElement(`${type}-input`);


            if (input) {
                input.value = "";
            }


            return;
        }


        if (!isValidFileSize(file)) {

            showUploadError(
                `"${file.name}" is ${formatFileSize(file.size)}. Maximum allowed size is 8 MB.`
            );


            const input =
                getElement(`${type}-input`);


            if (input) {
                input.value = "";
            }


            return;
        }


        selectedPhotos[type] = file;


        previewPhoto(
            file,
            type
        );


        updatePhotoCount();
    }


    // ============================================================
    // INPUT EVENTS
    // ============================================================

    if (frontInput) {

        frontInput.addEventListener(
            "change",
            () => {

                handlePhotoSelection(
                    frontInput.files[0],
                    "front"
                );
            }
        );
    }


    if (sideInput) {

        sideInput.addEventListener(
            "change",
            () => {

                handlePhotoSelection(
                    sideInput.files[0],
                    "side"
                );
            }
        );
    }


    if (detailInput) {

        detailInput.addEventListener(
            "change",
            () => {

                handlePhotoSelection(
                    detailInput.files[0],
                    "detail"
                );
            }
        );
    }


    // ============================================================
    // PROCESSING SCREEN
    // ============================================================

    function resetProcessingScreen() {

        const fill =
            getElement("processing-progress-fill");

        const text =
            getElement("processing-progress-text");


        if (fill) {
            fill.style.width = "10%";
        }


        if (text) {
            text.textContent =
                "Preparing your photos...";
        }


        const steps =
            document.querySelectorAll(
                ".processing-step"
            );


        steps.forEach((step, index) => {

            step.classList.remove(
                "current"
            );


            if (index < 2) {
                step.classList.add(
                    "active"
                );
            } else {
                step.classList.remove(
                    "active"
                );
            }
        });


        resetProcessingStepText();
    }


    function resetProcessingStepText() {

        const stepEnhance =
            getElement("step-enhance");

        const stepBackground =
            getElement("step-background");

        const stepGallery =
            getElement("step-gallery");


        if (stepEnhance) {

            const text =
                stepEnhance.querySelector("p");

            if (text) {
                text.textContent =
                    "Enhancing product images";
            }
        }


        if (stepBackground) {

            const text =
                stepBackground.querySelector("p");

            if (text) {
                text.textContent =
                    "Creating studio presentation";
            }
        }


        if (stepGallery) {

            const text =
                stepGallery.querySelector("p");

            if (text) {
                text.textContent =
                    "Preparing customer gallery";
            }
        }
    }


    function showEnhancementLoading() {

        if (uploadPanel) {
            uploadPanel.style.display = "none";
        }


        if (comparePanel) {
            comparePanel.style.display = "none";
        }


        if (loadingPanel) {
            loadingPanel.style.display = "block";
        }


        resetProcessingScreen();


        updateProcessingStep(
            "step-enhance",
            "✨ Enhancing product images..."
        );


        animateProcessingProgress();
    }


    function updateProcessingStep(
        stepId,
        message
    ) {

        const step =
            getElement(stepId);


        if (!step) {
            return;
        }


        step.classList.add(
            "current"
        );


        const text =
            step.querySelector("p");


        if (text && message) {
            text.textContent =
                message;
        }
    }


    function completeProcessingStep(
        stepId,
        message
    ) {

        const step =
            getElement(stepId);


        if (!step) {
            return;
        }


        step.classList.remove(
            "current"
        );


        step.classList.add(
            "active"
        );


        const text =
            step.querySelector("p");


        if (text && message) {
            text.textContent =
                message;
        }


        const icon =
            step.querySelector("span");


        if (icon) {
            icon.textContent = "✓";
        }
    }


    // ============================================================
    // AI PROCESSING ANIMATION
    // ============================================================

    let processingTimers = [];


    function clearProcessingTimers() {

        processingTimers.forEach(
            timer => {
                clearTimeout(timer);
            }
        );

        processingTimers = [];
    }


    function animateProcessingProgress() {

        clearProcessingTimers();


        const fill =
            getElement(
                "processing-progress-fill"
            );

        const text =
            getElement(
                "processing-progress-text"
            );


        if (!fill || !text) {
            return;
        }


        fill.style.width = "10%";

        text.textContent =
            "Preparing your photos...";


        processingTimers.push(

            setTimeout(() => {

                fill.style.width = "30%";

                text.textContent =
                    "Checking photo quality...";


                completeProcessingStep(
                    "step-quality",
                    "Photo quality checked"
                );

            }, 600)
        );


        processingTimers.push(

            setTimeout(() => {

                fill.style.width = "55%";

                text.textContent =
                    "✨ KalaSetu AI is enhancing your product photos...";


                updateProcessingStep(
                    "step-enhance",
                    "✨ Enhancing product images..."
                );

            }, 1300)
        );


        processingTimers.push(

            setTimeout(() => {

                fill.style.width = "72%";

                text.textContent =
                    "Improving lighting, colour and clarity...";


                updateProcessingStep(
                    "step-enhance",
                    "Improving lighting and clarity..."
                );

            }, 2500)
        );


        processingTimers.push(

            setTimeout(() => {

                fill.style.width = "84%";

                text.textContent =
                    "Creating a clean studio presentation...";


                completeProcessingStep(
                    "step-enhance",
                    "Product images enhanced"
                );


                updateProcessingStep(
                    "step-background",
                    "Creating studio presentation..."
                );

            }, 4000)
        );


        processingTimers.push(

            setTimeout(() => {

                fill.style.width = "94%";

                text.textContent =
                    "Preparing your customer gallery...";


                completeProcessingStep(
                    "step-background",
                    "Studio presentation created"
                );


                updateProcessingStep(
                    "step-gallery",
                    "Preparing customer gallery..."
                );

            }, 6000)
        );
    }


    function completeProcessing() {

        clearProcessingTimers();


        const fill =
            getElement(
                "processing-progress-fill"
            );

        const text =
            getElement(
                "processing-progress-text"
            );


        if (fill) {
            fill.style.width = "100%";
        }


        if (text) {
            text.textContent =
                "✓ Your enhanced product photos are ready!";
        }


        completeProcessingStep(
            "step-enhance",
            "Product images enhanced"
        );


        completeProcessingStep(
            "step-background",
            "Studio presentation created"
        );


        completeProcessingStep(
            "step-gallery",
            "Customer gallery ready"
        );
    }


    // ============================================================
    // UPLOAD THREE PHOTOS
    // ============================================================

    async function uploadThreePhotos() {

        hideUploadError();


        if (
            !selectedPhotos.front ||
            !selectedPhotos.side ||
            !selectedPhotos.detail
        ) {

            showUploadError(
                "Please upload all 3 product photos before continuing."
            );

            return;
        }


        showEnhancementLoading();


        const formData =
            new FormData();


        formData.append(
            "front_image",
            selectedPhotos.front
        );


        formData.append(
            "side_image",
            selectedPhotos.side
        );


        formData.append(
            "detail_image",
            selectedPhotos.detail
        );


        try {

            if (
                typeof UPLOAD_URL === "undefined" ||
                !UPLOAD_URL
            ) {

                throw new Error(
                    "Upload URL is not configured."
                );
            }


            const response =
                await fetch(
                    UPLOAD_URL,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            let data;


            try {

                data =
                    await response.json();

                console.log(
                    "KalaSetu upload response:",
                    data
                );

            } catch (jsonError) {

                throw new Error(
                    "The server returned an invalid response."
                );
            }


            if (!response.ok) {

                throw new Error(
                    data.error ||
                    data.message ||
                    "Image processing failed."
                );
            }


            if (
                data.success === false ||
                data.error
            ) {

                throw new Error(
                    data.error ||
                    "Image processing failed."
                );
            }


            completeProcessing();


            setTimeout(() => {

                showCompareScreen(
                    data
                );

            }, 500);


        } catch (error) {

            console.error(
                "KalaSetu image enhancement error:",
                error
            );


            clearProcessingTimers();


            if (loadingPanel) {
                loadingPanel.style.display =
                    "none";
            }


            if (uploadPanel) {
                uploadPanel.style.display =
                    "block";
            }


            showUploadError(
                error.message ||
                "Something went wrong while enhancing your photos. Please try again."
            );
        }
    }


    // ============================================================
    // CONTINUE BUTTON
    // ============================================================

    if (continueButton) {

        continueButton.addEventListener(
            "click",
            uploadThreePhotos
        );
    }


    // ============================================================
    // COMPARISON SCREEN
    // ============================================================

    function showCompareScreen(data) {

        clearProcessingTimers();


        if (loadingPanel) {
            loadingPanel.style.display =
                "none";
        }


        if (uploadPanel) {
            uploadPanel.style.display =
                "none";
        }


        if (comparePanel) {
            comparePanel.style.display =
                "block";
        }


        console.log(
            "KalaSetu comparison data:",
            data
        );


        const originalMain =
            document.getElementById(
                "original-image"
            );


        const enhancedMain =
            document.getElementById(
                "enhanced-image"
            );


        if (
            originalMain &&
            data.front_original
        ) {

            originalMain.src =
                data.front_original;

            originalMain.style.display =
                "block";
        }


        if (
            enhancedMain &&
            data.front_enhanced
        ) {

            enhancedMain.src =
                data.front_enhanced;

            enhancedMain.style.display =
                "block";
        }


        const galleryFront =
            document.getElementById(
                "gallery-front-img"
            );


        const gallerySide =
            document.getElementById(
                "gallery-side-img"
            );


        const galleryDetail =
            document.getElementById(
                "gallery-detail-img"
            );


        if (
            galleryFront &&
            data.front_enhanced
        ) {

            galleryFront.src =
                data.front_enhanced;

            galleryFront.style.display =
                "block";
        }


        if (
            gallerySide &&
            data.side_enhanced
        ) {

            gallerySide.src =
                data.side_enhanced;

            gallerySide.style.display =
                "block";
        }


        if (
            galleryDetail &&
            data.detail_enhanced
        ) {

            galleryDetail.src =
                data.detail_enhanced;

            galleryDetail.style.display =
                "block";
        }


        window.kalaSetuOriginalImages = {

            front:
                data.front_original,

            side:
                data.side_original,

            detail:
                data.detail_original
        };


        window.kalaSetuEnhancedImages = {

            front:
                data.front_enhanced,

            side:
                data.side_enhanced,

            detail:
                data.detail_enhanced
        };
    }


    // ============================================================
    // IMAGE HELPERS
    // ============================================================

    function setImageSource(
        id,
        source
    ) {

        const image =
            getElement(id);


        if (!image || !source) {
            return;
        }


        image.src = source;
    }


    function getLocalObjectURL(type) {

        const file =
            selectedPhotos[type];


        if (!file) {
            return null;
        }


        return URL.createObjectURL(
            file
        );
    }


    // ============================================================
    // USE ENHANCED IMAGE
    // ============================================================

    const useEnhancedButton =
        getElement(
            "use-enhanced"
        );


    if (useEnhancedButton) {

        useEnhancedButton.addEventListener(
            "click",
            () => {

                chooseImage(
                    "enhanced"
                );
            }
        );
    }


    // ============================================================
    // KEEP ORIGINAL
    // ============================================================

    const keepOriginalButton =
        getElement(
            "keep-original"
        );


    if (keepOriginalButton) {

        keepOriginalButton.addEventListener(
            "click",
            () => {

                chooseImage(
                    "original"
                );
            }
        );
    }


    // ============================================================
    // CHOOSE IMAGE
    // ============================================================

    async function chooseImage(type) {

        try {

            const images =
                type === "enhanced"
                    ? window.kalaSetuEnhancedImages
                    : window.kalaSetuOriginalImages;


            const front =
                images?.front ||
                getLocalObjectURL(
                    "front"
                );


            const side =
                images?.side ||
                getLocalObjectURL(
                    "side"
                );


            const detail =
                images?.detail ||
                getLocalObjectURL(
                    "detail"
                );


            if (
                typeof CHOOSE_IMAGE_URL === "undefined" ||
                !CHOOSE_IMAGE_URL
            ) {

                console.warn(
                    "CHOOSE_IMAGE_URL is not configured."
                );

                return;
            }


            const formData =
                new FormData();


            formData.append(
                "image_type",
                type
            );


            if (front) {

                formData.append(
                    "front_image",
                    front
                );
            }


            if (side) {

                formData.append(
                    "side_image",
                    side
                );
            }


            if (detail) {

                formData.append(
                    "detail_image",
                    detail
                );
            }


            const response =
                await fetch(
                    CHOOSE_IMAGE_URL,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Unable to save image selection."
                );
            }


            if (data.redirect) {

                window.location.href =
                    data.redirect;
            }


        } catch (error) {

            console.error(
                "Image selection error:",
                error
            );


            showUploadError(
                error.message ||
                "Unable to save your image selection."
            );
        }
    }


    // ============================================================
    // PASSWORD SHOW / HIDE
    // ============================================================

    const passwordToggle =
        document.querySelector(
            ".password-toggle"
        );


    if (passwordToggle) {

        passwordToggle.addEventListener(
            "click",
            () => {

                const targetId =
                    passwordToggle.dataset.target;


                const passwordInput =
                    targetId
                        ? getElement(targetId)
                        : document.querySelector(
                            'input[type="password"]'
                        );


                if (!passwordInput) {
                    return;
                }


                if (
                    passwordInput.type ===
                    "password"
                ) {

                    passwordInput.type =
                        "text";

                    passwordToggle.textContent =
                        "Hide";

                } else {

                    passwordInput.type =
                        "password";

                    passwordToggle.textContent =
                        "Show";
                }
            }
        );
    }


    // ============================================================
    // GENERIC PASSWORD TOGGLE
    // ============================================================

    document
        .querySelectorAll(
            "[data-password-toggle]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const targetId =
                        button.dataset
                            .passwordToggle;


                    const input =
                        getElement(
                            targetId
                        );


                    if (!input) {
                        return;
                    }


                    if (
                        input.type ===
                        "password"
                    ) {

                        input.type =
                            "text";

                        button.textContent =
                            "Hide";

                    } else {

                        input.type =
                            "password";

                        button.textContent =
                            "Show";
                    }
                }
            );
        });


    // ============================================================
    // ============================================================
    // QUESTIONS PAGE
    // ============================================================
    // ============================================================


    const questionListenButtons =
        document.querySelectorAll(
            ".question-listen-btn"
        );


    const questionMicButtons =
        document.querySelectorAll(
            ".question-mic-btn"
        );


    const questionGenerateButton =
        document.getElementById(
            "generate-catalog-btn"
        );


    const generatingPanel =
        document.getElementById(
            "generating-panel"
        );


    const answerError =
        document.getElementById(
            "answer-error"
        );


    // ============================================================
    // CURRENT LANGUAGE
    // ============================================================

    const currentLanguage =
        document.documentElement
            .getAttribute("lang") ||
        "en";


    // ============================================================
    // SPEECH RECOGNITION LANGUAGE
    // ============================================================

    const questionSpeechLanguages = {

        en: "en-IN",

        mr: "mr-IN",

        hi: "hi-IN"
    };


    // ============================================================
    // SPEAKER LANGUAGE
    // ============================================================

    /*
     * Chrome commonly does not provide a Marathi TTS voice.
     *
     * Therefore:
     *
     * English -> English
     * Hindi   -> Hindi
     * Marathi -> Hindi voice for practical fallback
     */

    const questionSpeakerLanguages = {

        en: "en-IN",

        mr: "hi-IN",

        hi: "hi-IN"
    };


    const questionRecognitionLanguage =
        questionSpeechLanguages[
            currentLanguage
        ] || "en-IN";


    const questionSpeakerLanguage =
        questionSpeakerLanguages[
            currentLanguage
        ] || "en-IN";


    // ============================================================
    // QUESTIONS DATA
    // ============================================================

    /*
     * questions.html must contain:
     *
     * window.QUESTIONS = {{ questions|tojson }};
     */

    if (
        !Array.isArray(
            window.QUESTIONS
        )
    ) {

        console.warn(
            "KalaSetu: window.QUESTIONS is not available."
        );
    }


    // ============================================================
    // SPEAKER VOICES LOADING
    // ============================================================

    if (
        window.speechSynthesis
    ) {

        window.speechSynthesis.onvoiceschanged =
            () => {

                const voices =
                    window.speechSynthesis
                        .getVoices();


                console.log(
                    "KalaSetu voices loaded:",
                    voices
                );
            };
    }


    // ============================================================
    // QUESTIONS SPEAKER
    // ============================================================

    let activeSpeakingButton = null;


    function stopQuestionSpeaking() {

        if (
            window.speechSynthesis
        ) {

            window.speechSynthesis.cancel();
        }


        if (activeSpeakingButton) {

            activeSpeakingButton.classList.remove(
                "speaking"
            );

            activeSpeakingButton =
                null;
        }
    }


    function speakQuestion(
        button,
        index
    ) {

        if (
            !window.speechSynthesis
        ) {

            alert(
                "Speaker is not supported in this browser."
            );

            return;
        }


        if (
            !Array.isArray(
                window.QUESTIONS
            )
        ) {

            console.warn(
                "KalaSetu: Questions data is not available."
            );

            return;
        }


        const question =
            window.QUESTIONS[index];


        if (!question) {
            return;
        }


        const text =
            typeof question === "object"
                ? question.text
                : question;


        if (!text) {
            return;
        }


        // Stop previous speech

        window.speechSynthesis.cancel();


        if (activeSpeakingButton) {

            activeSpeakingButton.classList.remove(
                "speaking"
            );

            activeSpeakingButton =
                null;
        }


        // Create utterance

        const utterance =
            new SpeechSynthesisUtterance(
                text
            );


        utterance.lang =
            questionSpeakerLanguage;


        utterance.rate =
            0.80;


        utterance.pitch =
            1;


        utterance.volume =
            1;


        // ========================================================
        // FIND BEST VOICE
        // ========================================================

        const voices =
            window.speechSynthesis
                .getVoices();


        let selectedVoice =
            null;


        // Exact language

        selectedVoice =
            voices.find(
                voice =>
                    voice.lang &&
                    voice.lang.toLowerCase() ===
                    questionSpeakerLanguage.toLowerCase()
            );


        // Same language family

        if (!selectedVoice) {

            const languageCode =
                questionSpeakerLanguage
                    .split("-")[0]
                    .toLowerCase();


            selectedVoice =
                voices.find(
                    voice =>
                        voice.lang &&
                        voice.lang
                            .toLowerCase()
                            .startsWith(
                                languageCode
                            )
                );
        }


        // Marathi -> Hindi fallback

        if (
            !selectedVoice &&
            currentLanguage === "mr"
        ) {

            selectedVoice =
                voices.find(
                    voice =>
                        voice.lang &&
                        voice.lang
                            .toLowerCase()
                            .startsWith("hi")
                );
        }


        if (selectedVoice) {

            utterance.voice =
                selectedVoice;
        }


        // ========================================================
        // SPEECH START
        // ========================================================

        utterance.onstart =
            () => {

                activeSpeakingButton =
                    button;


                button.classList.add(
                    "speaking"
                );
            };


        // ========================================================
        // SPEECH END
        // ========================================================

        utterance.onend =
            () => {

                if (
                    activeSpeakingButton ===
                    button
                ) {

                    button.classList.remove(
                        "speaking"
                    );


                    activeSpeakingButton =
                        null;
                }
            };


        // ========================================================
        // SPEECH ERROR
        // ========================================================

        utterance.onerror =
            event => {

                console.error(
                    "KalaSetu speaker error:",
                    event.error
                );


                button.classList.remove(
                    "speaking"
                );


                if (
                    activeSpeakingButton ===
                    button
                ) {

                    activeSpeakingButton =
                        null;
                }
            };


        // ========================================================
        // START SPEECH
        // ========================================================

        window.speechSynthesis.speak(
            utterance
        );


        console.log(
            "KalaSetu speaking:",
            text,
            "Language:",
            questionSpeakerLanguage,
            "Voice:",
            selectedVoice
                ? selectedVoice.name
                : "Browser default"
        );
    }


    // ============================================================
    // SPEAKER BUTTON EVENTS
    // ============================================================

    questionListenButtons.forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    const index =
                        Number(
                            button.dataset
                                .questionIndex
                        );


                    /*
                     * If same button is speaking,
                     * clicking again stops it.
                     */

                    if (
                        activeSpeakingButton ===
                        button
                    ) {

                        stopQuestionSpeaking();

                        return;
                    }


                    speakQuestion(
                        button,
                        index
                    );
                }
            );
        }
    );


    // ============================================================
    // QUESTIONS MICROPHONE
    // ============================================================

    let questionRecognition =
        null;


    let activeQuestionMic =
        null;


    let activeQuestionInput =
        null;


    const QuestionSpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    function resetQuestionMic() {

        if (activeQuestionMic) {

            activeQuestionMic.classList.remove(
                "recording"
            );


            activeQuestionMic.textContent =
                "🎙️";
        }


        activeQuestionMic =
            null;


        activeQuestionInput =
            null;
    }


    function stopQuestionRecording() {

        if (
            questionRecognition
        ) {

            try {

                questionRecognition.stop();

            } catch (error) {

                console.warn(
                    "Question recognition stop:",
                    error
                );
            }
        }
    }


    function startQuestionRecording(
        button,
        input
    ) {

        if (
            !QuestionSpeechRecognition
        ) {

            alert(
                "Voice input is not supported in this browser. Please type your answer."
            );

            return;
        }


        // Stop existing recognition

        if (
            questionRecognition
        ) {

            try {

                questionRecognition.stop();

            } catch (error) {

                console.warn(
                    error
                );
            }
        }


        // Stop speaker

        stopQuestionSpeaking();


        // Create NEW recognition object

        questionRecognition =
            new QuestionSpeechRecognition();


        questionRecognition.continuous =
            false;


        questionRecognition.interimResults =
            false;


        questionRecognition.maxAlternatives =
            3;


        questionRecognition.lang =
            questionRecognitionLanguage;


        activeQuestionMic =
            button;


        activeQuestionInput =
            input;


        // ========================================================
        // RECOGNITION START
        // ========================================================

        questionRecognition.onstart =
            () => {

                button.classList.add(
                    "recording"
                );


                button.textContent =
                    "⏹";
            };


        // ========================================================
        // RECOGNITION RESULT
        // ========================================================

        questionRecognition.onresult =
            event => {

                if (
                    !activeQuestionInput
                ) {

                    return;
                }


                const transcript =
                    event
                        .results[0][0]
                        .transcript;


                activeQuestionInput.value =
                    transcript;


                activeQuestionInput.dispatchEvent(
                    new Event(
                        "input",
                        {
                            bubbles: true
                        }
                    )
                );
            };


        // ========================================================
        // RECOGNITION ERROR
        // ========================================================

        questionRecognition.onerror =
            event => {

                console.error(
                    "Question voice recognition error:",
                    event.error
                );


                if (
                    event.error ===
                    "not-allowed"
                ) {

                    alert(
                        "Microphone permission was denied. Please allow microphone access."
                    );
                }


                resetQuestionMic();
            };


        // ========================================================
        // RECOGNITION END
        // ========================================================

        questionRecognition.onend =
            () => {

                resetQuestionMic();


                questionRecognition =
                    null;
            };


        // ========================================================
        // START RECOGNITION
        // ========================================================

        try {

            questionRecognition.start();

        } catch (error) {

            console.warn(
                "Question recognition could not start:",
                error
            );


            resetQuestionMic();


            questionRecognition =
                null;
        }
    }


    // ============================================================
    // QUESTION MICROPHONE BUTTON EVENTS
    // ============================================================

    questionMicButtons.forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    const targetId =
                        button.dataset
                            .voiceInput;


                    const input =
                        document.getElementById(
                            targetId
                        );


                    if (!input) {

                        console.warn(
                            "Question answer input not found:",
                            targetId
                        );

                        return;
                    }


                    if (
                        button.classList.contains(
                            "recording"
                        )
                    ) {

                        stopQuestionRecording();

                    } else {

                        startQuestionRecording(
                            button,
                            input
                        );
                    }
                }
            );
        }
    );


    // ============================================================
    // GENERATE CATALOG
    // ============================================================

    if (
        questionGenerateButton
    ) {

        questionGenerateButton.addEventListener(
            "click",
            async () => {

                // Hide old error

                if (answerError) {

                    answerError.style.display =
                        "none";
                }


                // Stop voice

                stopQuestionRecording();


                // Stop speaker

                stopQuestionSpeaking();


                // Collect answers

                const answers = [];


                for (
                    let index = 0;
                    index < 4;
                    index++
                ) {

                    const input =
                        document.getElementById(
                            `answer-${index}`
                        );


                    const answer =
                        input
                            ? input.value.trim()
                            : "";


                    answers.push(
                        answer
                    );
                }


                // Check empty answers

                const hasEmptyAnswer =
                    answers.some(
                        answer =>
                            !answer
                    );


                if (
                    hasEmptyAnswer
                ) {

                    if (answerError) {

                        answerError.textContent =
                            MSG_PLEASE_ANSWER ||
                            "Please answer all questions.";


                        answerError.style.display =
                            "block";
                    }


                    // Focus first empty field

                    for (
                        let index = 0;
                        index < 4;
                        index++
                    ) {

                        if (
                            !answers[index]
                        ) {

                            const input =
                                document.getElementById(
                                    `answer-${index}`
                                );


                            if (input) {
                                input.focus();
                            }


                            break;
                        }
                    }


                    return;
                }


                // Disable button

                questionGenerateButton.disabled =
                    true;


                // Show loading

                if (generatingPanel) {

                    generatingPanel.style.display =
                        "block";


                    generatingPanel.scrollIntoView({
                        behavior: "smooth",
                        block: "center"
                    });
                }


                try {

                    if (
                        typeof GENERATE_URL ===
                        "undefined" ||
                        !GENERATE_URL
                    ) {

                        throw new Error(
                            "Catalog generation URL is not configured."
                        );
                    }


                    const formData =
                        new FormData();


                    formData.append(
                        "answer_0",
                        answers[0]
                    );


                    formData.append(
                        "answer_1",
                        answers[1]
                    );


                    formData.append(
                        "answer_2",
                        answers[2]
                    );


                    formData.append(
                        "answer_3",
                        answers[3]
                    );
                    console.log("KalaSetu answers:", answers);
                    console.log("Material being sent:", answers[0]);
                    console.log("Making time being sent:", answers[1]);
                    console.log("Making cost being sent:", answers[2]);
                    console.log("Size being sent:", answers[3]);


                    formData.append(
                        "answers",
                        JSON.stringify(
                            answers
                        )
                    );


                    formData.append(
                        "language",
                        currentLanguage
                    );


                    // Send question keys

                    if (
                        Array.isArray(
                            window.QUESTIONS
                        )
                    ) {

                        const questionKeys =
                            window.QUESTIONS.map(
                                question => {

                                    if (
                                        typeof question ===
                                        "object"
                                    ) {

                                        return question.key ||
                                            "";
                                    }

                                    return "";
                                }
                            );


                        formData.append(
                            "question_keys",
                            JSON.stringify(
                                questionKeys
                            )
                        );
                    }


                    // Send request

                    const response =
                        await fetch(
                            GENERATE_URL,
                            {
                                method: "POST",
                                body: formData
                            }
                        );


                    let data = null;


                    const contentType =
                        response.headers.get(
                            "content-type"
                        ) || "";


                    if (
                        contentType.includes(
                            "application/json"
                        )
                    ) {

                        data =
                            await response.json();

                    } else {

                        if (
                            response.redirected
                        ) {

                            window.location.href =
                                response.url;

                            return;
                        }


                        const text =
                            await response.text();


                        console.log(
                            "Catalog generation response:",
                            text
                        );
                    }


                    if (!response.ok) {

                        throw new Error(
                            data?.error ||
                            data?.message ||
                            "Unable to generate catalog."
                        );
                    }


                    // JSON redirect

                    if (
                        data &&
                        data.redirect
                    ) {

                        window.location.href =
                            data.redirect;

                        return;
                    }


                    // JSON URL

                    if (
                        data &&
                        data.url
                    ) {

                        window.location.href =
                            data.url;

                        return;
                    }


                    // Normal Flask redirect

                    if (
                        response.redirected
                    ) {

                        window.location.href =
                            response.url;

                        return;
                    }


                    console.log(
                        "Catalog generated:",
                        data
                    );


                } catch (error) {

                    console.error(
                        "KalaSetu catalog generation error:",
                        error
                    );


                    if (answerError) {

                        answerError.textContent =
                            error.message ||
                            "Unable to generate catalog. Please try again.";


                        answerError.style.display =
                            "block";
                    }


                    if (generatingPanel) {

                        generatingPanel.style.display =
                            "none";
                    }


                    questionGenerateButton.disabled =
                        false;
                }
            }
        );
    }


    // ============================================================
    // GENERIC VOICE INPUT
    // ============================================================
    //
    // IMPORTANT:
    // Question microphones are handled separately above.
    // ============================================================

    let recognition =
        null;


    let activeVoiceButton =
        null;


    let activeVoiceInput =
        null;


    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (
        SpeechRecognition
    ) {

        recognition =
            new SpeechRecognition();


        recognition.continuous =
            false;


        recognition.interimResults =
            false;


        recognition.onstart =
            () => {

                if (
                    activeVoiceButton
                ) {

                    activeVoiceButton.classList.add(
                        "recording"
                    );


                    activeVoiceButton.textContent =
                        "⏹ Stop";
                }
            };


        recognition.onresult =
            event => {

                if (
                    !activeVoiceInput
                ) {

                    return;
                }


                const transcript =
                    event
                        .results[0][0]
                        .transcript;


                activeVoiceInput.value =
                    transcript;


                activeVoiceInput.dispatchEvent(
                    new Event(
                        "input",
                        {
                            bubbles: true
                        }
                    )
                );
            };


        recognition.onerror =
            event => {

                console.error(
                    "Voice recognition error:",
                    event.error
                );


                if (
                    event.error ===
                    "not-allowed"
                ) {

                    alert(
                        "Microphone permission was denied. Please allow microphone access."
                    );
                }
            };


        recognition.onend =
            () => {

                if (
                    activeVoiceButton
                ) {

                    activeVoiceButton.classList.remove(
                        "recording"
                    );


                    activeVoiceButton.textContent =
                        "🎤 Speak";
                }


                activeVoiceButton =
                    null;


                activeVoiceInput =
                    null;
            };
    }


    function startVoiceInput(
        button,
        input
    ) {

        if (!recognition) {

            alert(
                "Voice input is not supported in this browser. Please type your answer."
            );

            return;
        }


        activeVoiceButton =
            button;


        activeVoiceInput =
            input;


        const language =
            document.documentElement
                .getAttribute("lang");


        if (
            language === "mr"
        ) {

            recognition.lang =
                "mr-IN";

        } else if (
            language === "hi"
        ) {

            recognition.lang =
                "hi-IN";

        } else {

            recognition.lang =
                "en-IN";
        }


        try {

            recognition.start();

        } catch (error) {

            console.warn(
                "Voice recognition could not start:",
                error
            );
        }
    }


    function stopVoiceInput() {

        if (!recognition) {
            return;
        }


        try {

            recognition.stop();

        } catch (error) {

            console.warn(
                "Voice recognition could not stop:",
                error
            );
        }
    }


    // ============================================================
    // GENERIC VOICE BUTTONS
    // ============================================================

    document
        .querySelectorAll(
            ".voice-button, [data-voice-input]"
        )
        .forEach(
            button => {

                /*
                 * IMPORTANT:
                 * Do not attach generic voice handling
                 * to Questions microphones.
                 */

                if (
                    button.classList.contains(
                        "question-mic-btn"
                    )
                ) {

                    return;
                }


                button.addEventListener(
                    "click",
                    () => {

                        const targetId =
                            button.dataset
                                .voiceInput ||
                            button.dataset.target;


                        let input =
                            null;


                        if (
                            targetId
                        ) {

                            input =
                                getElement(
                                    targetId
                                );
                        }


                        if (!input) {

                            const parent =
                                button.parentElement;


                            if (parent) {

                                input =
                                    parent.querySelector(
                                        "input, textarea"
                                    );
                            }
                        }


                        if (!input) {
                            return;
                        }


                        if (
                            button.classList.contains(
                                "recording"
                            )
                        ) {

                            stopVoiceInput();

                        } else {

                            startVoiceInput(
                                button,
                                input
                            );
                        }
                    }
                );
            }
        );


    // ============================================================
    // DRAG & DROP SUPPORT
    // ============================================================

    document
        .querySelectorAll(
            ".photo-upload-box, .photo-slot, [data-photo-upload]"
        )
        .forEach(
            box => {

                box.addEventListener(
                    "dragover",
                    event => {

                        event.preventDefault();

                        box.classList.add(
                            "drag-over"
                        );
                    }
                );


                box.addEventListener(
                    "dragleave",
                    () => {

                        box.classList.remove(
                            "drag-over"
                        );
                    }
                );


                box.addEventListener(
                    "drop",
                    event => {

                        event.preventDefault();


                        box.classList.remove(
                            "drag-over"
                        );


                        const files =
                            event.dataTransfer.files;


                        if (
                            !files ||
                            !files.length
                        ) {

                            return;
                        }


                        let type =
                            box.dataset.photoUpload;


                        if (!type) {

                            if (
                                box.querySelector(
                                    "#front-input"
                                )
                            ) {

                                type =
                                    "front";

                            } else if (
                                box.querySelector(
                                    "#side-input"
                                )
                            ) {

                                type =
                                    "side";

                            } else if (
                                box.querySelector(
                                    "#detail-input"
                                )
                            ) {

                                type =
                                    "detail";
                            }
                        }


                        if (!type) {
                            return;
                        }


                        handlePhotoSelection(
                            files[0],
                            type
                        );
                    }
                );
            }
        );


    // ============================================================
    // INITIAL STATE
    // ============================================================

    updatePhotoCount();


    console.log(
        "✓ KalaSetu Artisan JavaScript loaded successfully."
    );


    if (
        questionListenButtons.length > 0
    ) {

        console.log(
            "✓ KalaSetu Questions speaker loaded."
        );
    }


    if (
        questionMicButtons.length > 0
    ) {

        console.log(
            "✓ KalaSetu Questions microphone loaded."
        );
    }

});