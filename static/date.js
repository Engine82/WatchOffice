document.addEventListener('DOMContentLoaded', function () {
    // display date
    var today = new Date().toLocaleDateString()
    console.log(today);
    const dateElem = document.getElementById("date")  
    
    dateElem.textContent = today;
})

