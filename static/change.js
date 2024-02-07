const member = document.getElementById("member");
const uName = document.getElementById("username");
const fName = document.getElementById("first");
const lName = document.getElementById("last");
const password = document.getElementById("password");
const password2 = document.getElementById("confirm_password");
const rank = document.getElementById("rank");
const platoon = document.getElementById("platoon");
const elligible = document.getElementById("elligibility");
const form = document.getElementById("form");
const errorElement = document.getElementById('error');
const masterError = document.getElementById("master_error");


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
    inputControl.classList.remove('error');
}

const setMasterError = (type) => {
    if (type === 1) {
        masterError.style.visibility = "visible";
    } else {
        masterError.style.visibility = "hidden";
    }
}

function checkInputs() {

    // clear previous errors
    setMasterError(0);

    // get values, remove white space from ends of inputs
    const memberV = member.value.trim();
    const uNameV = uName.value.trim();
    const fNameV = fName.value.trim();
    const lNameV = lName.value.trim();
    const passwordV = password.value.trim();
    const passwordV2 = password2.value.trim();

    try {
        console.log(rank)
        var rankV = rank.value;
        console.log(rankV);
    }
    catch(err) {
        var rankV = '';
    }

    try {
        console.log(platoon)
        var platoonV = platoon.value;
        console.log(platoonV);
    }
    catch(err) {
        var platoonV = '';
    }

    try {
        console.log(elligible)
        var elligibleV = elligible.value;
        console.log(elligibleV);
    }
    catch(err) {
        var elligibleV = '';
    }

    var changes = 0;
    var errors = 0;


    // ensure a user has been chosen
    if (memberV === "") {
        setError(member, 'User must be selected');
        errors++;
    } else {
        setSuccess(member);
    }

    // check each input field for a change
    if (uNameV != '') {
        setSuccess(uName);
        changes++;
    } else {
        setSuccess(uName);
    }

    if (fNameV != '') {
        setSuccess(fName);
        changes++;
    } else {
        setSuccess(fName);
    }

    if (lNameV != '') {
        setSuccess(lName);
        changes++;
    } else {
        setSuccess(lName);
    }

    if (passwordV != '') {
        if (passwordV.length < 8 || passwordV.length > 64) {
            setError(password, 'Password must be between 8 and 64 charactars long')
            errors++;
        } else {
            setSuccess(password);
        }
    } else {
        setSuccess(password);
    }

    if (passwordV.length > 0 && passwordV2.length == 0) {
        setError(password2, 'Please confirm your password');
        errors++;
    } else if (passwordV2 !== passwordV) {
        setError(password2, 'Passwords do not match');
        errors++;
    } else if (passwordV === passwordV2 && passwordV.length > 0) {
        setSuccess(password2);
        changes++;
    } else {
        setSuccess(password2);
    }

    console.log(rankV);
    if (rankV != '') {
        setSuccess(rank);
        changes++;
    }

    console.log(platoonV);
    if (platoonV != '') {
        setSuccess(platoon);
        changes++;
    }

    console.log(elligibleV);
    if (elligibleV != '') {
        setSuccess(elligible);
        changes++;
    }

    if (changes === 0 && errors === 0) {
        setMasterError(1);
    } else if (errors > 0) {
        setMasterError(0);
    } else if (changes > 0 && errors === 0) {
        form.removeEventListener("submit", formListen);
        form.submit();
    }
}