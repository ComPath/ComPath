/** This JS controls the pathway page
 **
 * @requires: jquery
 */

function addHyperLinkPathway(resource, pathwayId, pathwayName) {
    return '<a target="_blank" href="/pathway/' + resource + '/' + pathwayId + '">' + pathwayName + '</a>'
}

/**
 * Creates a new row in Node/Edge info table
 * @param {object} table: table object
 * @param {int} row: row number
 * @param {string} columnNumber: number of column
 * @param {string} pathwayInfo: string for the column
 */
function insertRow(table, row, columnNumber, pathwayInfo) {

    var row = table.insertRow(row);
    var cell = row.insertCell(columnNumber);
    cell.innerHTML = addHyperLinkPathway(pathwayInfo[0], pathwayInfo[1], pathwayInfo[2]);

    var cell = row.insertCell(1);
    cell.innerHTML = pathwayInfo[3];

}

/**
 * Clear table rows
 * @param {str} tableId id of the table
 * @param {array} rows
 */
function updateDynamicTable(tableId, rows) {

    var table = document.getElementById(tableId);

    var row = table.insertRow(0);
    var pathwayName = row.insertCell(0);
    pathwayName.innerHTML = "<b>Pathway Name</b>";

    var similarityHeading = row.insertCell(1);
    similarityHeading.innerHTML = "<b>Similarity</b>";

    var row = 1;
    $.each(rows, function (key, value) {
        insertRow(table, row, 0, value);
        row++
    });
}


/**
 * Clear table rows
 * @param {str} tableId id of the table
 */
function clearTable(tableId) {

    var table = document.getElementById(tableId);

    while (table.rows.length > 0) {
        table.deleteRow(0);
    }
}

$(document).ready(function () {

    $("#infer-mappings").on('click', function (e) {

        $.ajax({
            type: "GET",
            url: "/pathway/infer/hierarchy",
            data: {
                'resource': resource,
                'pathway_name': pathwayName,
                'pathway_id': pathwayId
            },
            dataType: "json",
            global: false,
            error: function (request) {
                alert('Problem with request');
            },
            success: function (response) {
                console.log(response);

                clearTable('info-table');

                updateDynamicTable('info-table', response);
            }
        });

    });

    $("#suggest-by-name").on('click', function (e) {

        $.ajax({
            type: "GET",
            url: "/suggest_mappings/name/" + pathwayName,
            dataType: "json",
            global: false,
            error: function (request) {
                alert('Problem with request');
            },
            success: function (response) {

                clearTable('info-table');

                updateDynamicTable('info-table', response);
            }
        });

    });


});

