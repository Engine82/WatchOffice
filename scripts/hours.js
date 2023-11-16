/*
document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('form').addEventListener('change', function() {
        if (document.querySelector('#hours_1').) {
        document.getElementsByClassName("hours_1").style.display = "none";
        }
        else {
        document.getElementsByClassName("hours_1").style.display = "block";
        }
    });
});


const selectElement = document.querySelector('.day');
const choice = document.querySelector('#hours_input_1');

selectElement.addEventListener("change", (event) => {
    hours_input_1.
});  */

document.addEventListener('DOMContentLoaded', function() {
    document.getElementsByClassName('day').addEventListener('change', function() {
        if (document.getElementsByClassName('#hours_1') == 'hours') {
        document.getElementsByClassName("hours_1").style.display = "none";
        }
        else {
        document.getElementsByClassName("hours_1").style.display = "block";
        }
    });
});