document.addEventListener('DOMContentLoaded', function () {
    function printDiv (divName) {
        var printContents = document.getElementById(divName).cloneNode(true).innerHTML;
        var originalContents = document.body.innerHTML;

        document.body.innerHTML = printContents;

        window.print();

        document.body.innerHTML = originalContents;
    }

    document.querySelector("#print").addEventListener('click', function(event) {
//        event.preventDefault();
        printDiv("printableArea");
    });
});