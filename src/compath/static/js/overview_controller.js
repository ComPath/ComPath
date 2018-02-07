/** This JS controls the overview page of ComPath
 **
 * @requires: jquery, d3
 */


/**
 * * Resource list
 */
var resourceList = ["KEGG", "WikiPathways", "Reactome"];

firstResourceInput = $('#first-resource-input');

// Autocompletion in the first input
firstResourceInput.autocomplete({
    source: resourceList
});


// Autocompletion in the first input
$('#first-pathway-input').autocomplete({
    source: function (request, response) {
        $.ajax({
            url: "/api/autocompletion/pathway_name",
            dataType: "json",
            data: {
                resource: firstResourceInput.val(),
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

            pathwayNameInput = $(new_field_group.find('input')[0]);
            resourceInput = $(new_field_group.find('input')[1]);

            pathwayNameInput[0].value = '';
            resourceInput[0].value = '';

            pathwayNameInput.value = ''; // Empty current value and start autocompletion
            resourceInput.value = ''; // Empty current value and start autocompletion

            pathwayNameInput.autocomplete({
                source: function (request, response) {
                    $.ajax({
                        url: "/api/autocompletion/pathway_name",
                        dataType: "json",
                        data: {
                            resource: resourceInput.val(),
                            q: request.term
                        },
                        success: function (data) {
                            response(data); // functionName
                        }
                    });
                }, minLength: 2
            });
            resourceInput.autocomplete({
                source: resourceList
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
                success: function (dataOverlap) {
                    console.log(dataOverlap)
                },
                error: function (request) {
                    alert(request.responseText);
                }
            });

            return false;
        }
    );

});
