document.addEventListener('DOMContentLoaded', (event) => {
    const textElement = document.querySelector('#about p');
    const text = textElement.textContent;
    textElement.textContent = '';

    let index = 0;
    function type() {
        if (index < text.length) {
            textElement.textContent += text.charAt(index);
            index++;
            setTimeout(type, 100);  // Adjust typing speed here
        }
    }
    
    type();
});
