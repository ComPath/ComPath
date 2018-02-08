/** This JS controls the overview page of ComPath
 **
 * @requires: jquery, d3
 */


// Counter for the dynamic form
var counter = 1;

// Autocompletion in the first input
$('#pathway-name-1').autocomplete({
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

/**
 * * Dynamically adds/deletes pathways inputs
 */
$(function () {
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

            // Empty current value and start autocompletion
            pathwayNameInput[0].value = '';
            resourceSelect[0].value = '';

            pathwayNameInput.autocomplete({
                source: function (request, response) {
                    $.ajax({
                        url: "/api/autocompletion/pathway_name",
                        dataType: "json",
                        data: {
                            resource: resourceSelect.val(),
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


$(document).ready(function () {

    var form = $("#venn-diagram-form");

    form.on("submit", function (e) {

            e.preventDefault();

            $.ajax({
                url: "/query/overlap?" + form.serialize(),
                type: 'GET',
                dataType: "json",
                success: function (sets) {
                    console.log(sets);

                    var chart = venn.VennDiagram();
                    d3.select("#overlap-venn-diagram").datum(sets).call(chart);
                },
                error: function (request) {
                    alert(request.responseText);
                }
            });

            return false;
        }
    );

});
