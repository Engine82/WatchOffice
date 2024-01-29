const uName = document.getElementById("username");
const fName = document.getElementById("first_name");
const lName = document.getElementById("last_name");
const password = document.getElementById("password");
const password2 = document.getElementById("password2");
const form = document.getElementById("form");
const errorElement = document.getElementById('error');


let formListen = (event) => {
    event.preventDefault();
    console.log("preventDefaults")
    checkInputs();
}

form.addEventListener("submit", formListen);


const setError = (element, message) => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector(".error");

    errorDisplay.innerText = message;
    inputControl.classList.add('error');
    inputControl.classList.remove('success');
}

const setSuccess = (element) => {
    const inputControl = element.parentElement;
    const errorDisplay = inputControl.querySelector(".error");

    errorDisplay.innerText = '';
    inputControl.classList.add('success');
    inputControl.classList.remove('error')    ;
}

function checkInputs() {

    // get values, remove white space from ends of inputs
    const uNameV = uName.value.trim();
    const fNameV = fName.value.trim();
    const lNameV = lName.value.trim();
    const passwordV = password.value.trim();
    const passwordV2 = password2.value.trim();
    let successes = 0;

    if (uNameV === '') {
        setError(uName, 'Username is required');
    } else {
        setSuccess(uName);
        successes++;
    }

    if (fNameV === '') {
        setError(fName, 'First name is required');
    } else {
        setSuccess(fName);
        successes++;
    }

    if (lNameV === '') {
        setError(lName, 'Last name is required');
    } else {
        setSuccess(lName);
        successes++;
    }

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

    console.log("Successes: ", successes);
    if (successes === 5) {
        form.removeEventListener("submit", formListen);
        console.log("Listener removed")
        form.submit();
        console.log("form submitted");
    }
}