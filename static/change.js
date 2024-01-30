const uName = document.getElementById("username");
const fName = document.getElementById("first");
const lName = document.getElementById("last");
const password = document.getElementById("password");
const password2 = document.getElementById("confirm_password");
const rank = document.getElementById("rank");
const platoon = document.getElementById("platoon");
const active = document.getElementById("active");
const elligibile = document.getElementById("elligible");
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

    errorDisplay.innerText = 'no errors';
    inputControl.classList.add('success');
    inputControl.classList.remove('error');
}

const setMasterError = () => {
    const masterError = document.getElementById("master_error");

    masterError.style.visibility = "visible";
}

function checkInputs() {

    // get values, remove white space from ends of inputs
    const uNameV = uName.value.trim();
    const fNameV = fName.value.trim();
    const lNameV = lName.value.trim();
    const passwordV = password.value.trim();
    const passwordV2 = password2.value.trim();

    try {
        var rankV = rank.value.trim();
    }
    catch(err) {
        var rankV = '';
    }

    try {
        var platoonV = platoon.value.trim();
    }
    catch(err) {
        var platoonV = '';
    }

    try {
        var activeV = active.value.trim();
    }
    catch(err) {
        var activeV = '';
    }
    try {
        var elligibleV = ellligible.value.trim();
    }
    catch(err) {
        var elligibleV = '';
    }
    var changes = 0;


    // check each input field for a change
    console.log(changes);
    if (uNameV != '') {
        setSuccess(uName);
        changes++;
        console.log("username")
    }

    console.log(fNameV);
    console.log(changes);
    if (fNameV != '') {
        console.log(fName, fNameV);
        setSuccess(fName);
        changes++;
        console.log("first name")
    }

    console.log(changes);
    if (lNameV != '') {
        setSuccess(lName);
        changes++;
        console.log("last name")
    }

    console.log(changes);
    if (passwordV != '') {
        if (passwordV.length < 8 || passwordV.length > 64) {
            setError(password, 'Password must be between 8 and 64 charactars long')
        } else {
            setSuccess(password);
        }
    }
 
    console.log(changes);
    console.log(passwordV, passwordV2)
    console.log(passwordV.length, passwordV2.length)

    if (passwordV.length > 0 && passwordV2.length == 0) {
        setError(password2, 'Please confirm your password');
    } else if (passwordV2 !== passwordV) {
        setError(password2, 'Passwords do not match')
    } else if (passwordV === passwordV2 && passwordV.length > 0 && passwordV2.length > 0) {
        setSuccess(password2);
        changes++;
        console.log("password");
    } else {
        console.log("Success!")
    }

    console.log(changes);
    if (rankV != '') {
        setSuccess(rank);
        changes++;
        console.log("rank")
    }

    console.log(changes);
    if (platoonV != '') {
        setSuccess(lName);
        changes++;
        console.log("platoon")
    }

    console.log(changes);
    if (activeV != '') {
        setSuccess(lName);
        changes++;
        console.log("active")
    }

    console.log(changes);
    if (elligibleV != '') {
        setSuccess(elligible);
        changes++;
        console.log("elligibility")
    }

    console.log("Changes: ", changes);
    if (changes === 0) {
        setMasterError();
    } else {
        //form.removeEventListener("submit", formListen);
        //form.submit();
        console.log("END")
    }
}