/*
loop through each row and column in table
    if cell has "vacancy"
        if element.innerText == "vacancy"
        cell + 1 make "24" selected set element.????? = "24" 

*/

document.addEventListener('DOMContentLoaded', function () {
    // iterate through each table in the page
    let tables = document.getElementsByTagName("table");

    for (let table of tables) {

        // iterate through each cell in the table
        for (var i = 0, row; row = table.rows[i]; i++) {
            for (var j = 0, cell; cell = row.cells[j]; j++) {

                // if the cell reads "vacancy," set that status to out 24
                let txt = cell.innerText;
                if (txt == 'vacancy') {
                    nextCell = row.cells[j+1]
                    nextCell.children[0].value = '24';
                }
                
            }
        }
    }
});