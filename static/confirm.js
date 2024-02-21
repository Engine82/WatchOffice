// Alert to make sure user wants to remove this member
document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#remove').addEventListener('submit', function(event) {
        let element = document.getElementById('member');
        let name = element.options[element.selectedIndex].innerText;
        if(!window.confirm('Are you sure you want to remove ' + name + ' ?')) {
            event.preventDefault();
        };
    });
});