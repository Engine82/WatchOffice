// Form validation for add form

// Get user input
const uName = document.getElementById("username");
const fName = document.getElementById("first_name");
const lName = document.getElementById("last_name");
const password = document.getElementById("password");
const password2 = document.getElementById("password2");
const form = document.getElementById("form");
const errorElement = document.getElementById('error');


// Prevent form from submitting when button clicked
let formListen = (event) => {
    event.preventDefault();
    checkInputs();
}

form.addEventListener("submit", formListen);


// Function to display error message
const setError = (element, message) => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector(".error");

    errorDisplay.innerText = message;
    inputControl.classList.add('error');
    inputControl.classList.remove('success');
}

// Function to show input is accepted
const setSuccess = (element) => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector(".error");

    errorDisplay.innerText = '';
    inputControl.classList.add('success');
    inputControl.classList.remove('error')    ;
}

// Function - validate each input field
function checkInputs() {

    // get values, remove white space from ends of inputs
    const uNameV = uName.value.trim();
    const fNameV = fName.value.trim();
    const lNameV = lName.value.trim();
    const passwordV = password.value.trim();
    const passwordV2 = password2.value.trim();
    let successes = 0;

    // Username
    if (uNameV === '') {
        setError(uName, 'Username is required');
    } else {
        setSuccess(uName);
        successes++;
    }

    // First name
    if (fNameV === '') {
        setError(fName, 'First name is required');
    } else {
        setSuccess(fName);
        successes++;
    }

    // Last name
    if (lNameV === '') {
        setError(lName, 'Last name is required');
    } else {
        setSuccess(lName);
        successes++;
    }

    // Password
    if (passwordV === '') {
        setError(password, 'Password is required');
    } else if (passwordV.length < 8 || passwordV.length > 64) {
        setError(password, 'Password must be between 8 and 64 charactars long')
    } else {
        setSuccess(password);
        successes++;
    } 
 
    if (passwordV2 === '') {
        setError(password2, 'Please confirm your password');
    } else if (passwordV2 !== passwordV) {
        setError(password2, 'Passwords do not match')
    } else {
        setSuccess(password2);
        successes++;
    }

    // If everything is accepted, submit the form
    if (successes === 5) {
        form.removeEventListener("submit", formListen);
        form.submit();
    }
}