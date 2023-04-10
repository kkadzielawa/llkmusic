let btnTripBar = document.getElementById('hamb');

changeDisplay = () => {
    if (btnTripBar.style.display === "block") {
        btnTripBar.style.display = "none";
    } 
    else {
    btnTripBar.style.display = "block";
    }
}

btnTripBar.addEventListener('click', changeDisplay);