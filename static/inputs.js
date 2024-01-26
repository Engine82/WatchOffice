const uName = document.getElementById("username");
const fName = document.getElementById("first_name");
const lName = document.getElementById("last_name");
const password = document.getElementById("password");
const form = document.getElementById("form");
const errorElement = document.getElementById('error');

form.addEventListener("click", (e) => {
    e.preventDefault();
    let messages = [];

    // Username
    if (uName.value === '' | uName.value == null) {
        messages.push('Username is required');
    }


    // Name
    if (fName.value === '' | fName.value == null) {
        messages.push('First name is required');
    }

    if (lName.value === '' | lName.value == null) {
        messages.push('Last name is required');
    }


    // Password
    if (password.value.length < 8 || password.value.length > 64) {
        console.log('password length: ', password.value.length)
        messages.push('Password must be between 8 and 64 characters');
    }

    if (password.value === "password" || password.value === "12345678") {
        messages.push('Password not allowed');
    }


    // prevent form from submitting, display error messages
    if (messages.length > 0) {
        e.preventDefault;
        errorElement.innerText = messages.join(",\n");
    } else {
        form.submit;
    }
})
