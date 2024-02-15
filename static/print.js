// Print the appropriate area of html without style when print button is clicked
document.addEventListener('DOMContentLoaded', function () {
    function printDiv (divName) {

        // Assign variables to corresponding areas of HTML
        var printContents = document.getElementById(divName).cloneNode(true).innerHTML;
        var originalContents = document.body.innerHTML;

        // Print ony the hiring results, excluding navbar, buttons, etc
        document.body.innerHTML = printContents;
        window.print();

        // Restore page back to normal
        document.body.innerHTML = originalContents;
        
        // Call this function again so the print button works more than one time
        document.querySelector("#print").addEventListener('click', function(event) {
            printDiv(divName);
        });

    }

    // Call the print function the first time
    document.querySelector("#print").addEventListener('click', function(event) {
        printDiv("printableArea");
    });
});