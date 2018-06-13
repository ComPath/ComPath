/** This JS controls the overview page of ComPath
 **
 * @requires: jquery, d3
 */

$(document).ready(function () {

    // Autocompletion in the first input
    $('#input-1').autocomplete({
        source: function (request, response) {
            $.ajax({
                url: "/api/autocompletion/pathway_name",
                dataType: "json",
                data: {
                    resource: $('#select-1').find(":selected").val(),
                    q: request.term
                },
                success: function (data) {
                    response(data); // functionName
                }
            });
        }, minLength: 2
    });
});

/**
 * * Dynamically adds/deletes pathways inputs
 */
$(function () {

    var cloneCount = 1; // Avoid duplicate ids

    // Remove button click
    $(document).on(
        'click',
        '[data-role="dynamic-fields"] > .form-inline [data-role="remove"]',
        function (e) {
            e.preventDefault();
            $(this).closest('.form-inline').remove();
        }
    );
    // Add button click
    $(document).on(
        'click',
        '[data-role="dynamic-fields"] > .form-inline [data-role="add"]',
        function (e) {
            e.preventDefault();
            var container = $(this).closest('[data-role="dynamic-fields"]');
            var new_field_group = container.children().filter('.form-inline:first-child').clone();

            pathwayNameInput = $(new_field_group.find('input')[0]); // get input
            resourceSelect = $(new_field_group.find('select')[0]); // get select

            // Increment the counter and save the variable to change the id of the cloned form
            cloneCount++;
            var currentCounter = cloneCount;

            // Empty current value and id to set up auto completion
            pathwayNameInput.attr('id', 'input-' + currentCounter);
            resourceSelect.attr('id', 'select-' + currentCounter);
            pathwayNameInput[0].value = '';
            resourceSelect[0].value = '';

            pathwayNameInput.autocomplete({
                source: function (request, response) {
                    $.ajax({
                        url: "/api/autocompletion/pathway_name",
                        dataType: "json",
                        data: {
                            resource: $('#select-' + currentCounter).find(":selected").val(),
                            q: request.term
                        },
                        success: function (data) {
                            response(data); // functionName
                        }
                    });
                }, minLength: 2
            });

            container.append(new_field_group);
        }
    );
});


/**
 * Creates a new row in Node/Edge info table
 * @param {object} table: table object
 * @param {int} row: row number
 * @param {string} column1: string for column1
 * @param {string} column2: string for column2
 */
function insertRow(table, row, column1, column2) {

    var row = table.insertRow(row);
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    cell1.innerHTML = column1;
    cell2.innerHTML = column2;
}

/**
 * Renders node info table
 * @param {object} data object
 */
function populateInfoTable(data) {

    var dynamicTable = document.getElementById('info-table');

    while (dynamicTable.rows.length > 0) {
        dynamicTable.deleteRow(0);
    }
    delete data.sets;

    var tableObject = {};


    if ("intersection" in data) {
        tableObject["Pathway(s)"] = data["intersection"];
    }
    else {
        tableObject["Pathway(s)"] = data["label"];
    }

    tableObject["Gene Set Size"] = data["size"];

    tableObject["Gene Set"] = data["gene_set"].join(", ") + ' <a id="export-link" href="#"><span onclick="exportGenes();" class=\"glyphicon glyphicon-new-window\"></span></a>';

    window.gene_set = data["gene_set"];

    var row = 0;
    $.each(tableObject, function (key, value) {
        insertRow(dynamicTable, row, key, value);
        row++
    });

}

function exportGenes() {
    var anchor = document.querySelector('#export-link');

    anchor.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(window.gene_set.join("\n"));
    anchor.download = 'gene_set.txt';

}

$(document).ready(function () {

    var form = $("#venn-diagram-form");

    form.on("submit", function (e) {

            e.preventDefault();

            $.ajax({
                url: "/query/overlap?" + form.serialize(),
                type: 'GET',
                dataType: "json",
                success: function (data) {

                    // Adapted from https://github.com/benfred/venn.js/

                    var Venndiv = d3.select("#overlap-venn-diagram");

                    Venndiv.attr("align", "center"); // Align center the diagram

                    var geneOverlap = venn.VennDiagram(); // Plot the Venn Diagram
                    Venndiv.datum(data).call(geneOverlap); // Stick data

                    // Add table creation
                    Venndiv.selectAll("g").on("dblclick", function (d, i) {
                        populateInfoTable(d);
                    })
                },
                error: function () {
                    alert("Invalid Query. Please make sure you have selected at least 2 pathways.")
                }
            });

            return false;
        }
    );
});
