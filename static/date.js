// Add today's date to the top of the hiring results
document.addEventListener('DOMContentLoaded', function () {
    var today = new Date().toLocaleDateString()
    const dateElem = document.getElementById("date")  
    dateElem.textContent = today;
})