document.addEventListener('DOMContentLoaded', (event) => {
    const mainSection = document.querySelector('#main');
    const paragraphs = mainSection.querySelectorAll('p');
    
    let textArray = [];
    paragraphs.forEach(p => {
        textArray.push(p.textContent);
        p.textContent = '';
    });

    let index = 0;
    let paragraphIndex = 0;

    function type() {
        if (paragraphIndex < textArray.length) {
            if (index < textArray[paragraphIndex].length) {
                paragraphs[paragraphIndex].textContent += textArray[paragraphIndex].charAt(index);
                index++;
                setTimeout(type, 35);  // Adjust typing speed here
            } else {
                index = 0;
                paragraphIndex++;
                if (paragraphIndex < textArray.length) {
                    setTimeout(type, 35);  // Pause before starting next paragraph
                }
            }
        }
    }
    
    type();

    
});

