/**
 * Renders node info table
 * @param {array} pathways object
 */
function displayInferredHierarchy(pathways) {

    var dynamicTable = document.getElementById('info-table');

    while (dynamicTable.rows.length > 0) {
        dynamicTable.deleteRow(0);
    }

    console.log(pathways)
}
