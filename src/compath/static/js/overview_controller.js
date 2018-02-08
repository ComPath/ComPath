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
                success: function (data) {

                    // Adapted from https://github.com/benfred/venn.js/

                    var Venndiv = d3.select("#overlap-venn-diagram");

                    Venndiv.attr("align","center"); // Align center the diagram

                    var geneOverlap = venn.VennDiagram(); // Plot the Venn Diagram
                    Venndiv.datum(data).call(geneOverlap); // Stick data

                    // add a tooltip
                    var tooltip = d3.select("body").append("div")
                        .attr("class", "venntooltip");

                    // add listeners to all the groups to display tooltip on mouseover
                    Venndiv.selectAll("g")
                        .on("mouseover", function (d, i) {
                            // sort all the areas relative to the current item
                            venn.sortAreas(Venndiv, d);

                            // Display a tooltip with the current size
                            tooltip.transition().duration(400).style("opacity", .9);
                            tooltip.text(d.size + " genes");

                            // highlight the current path
                            var selection = d3.select(this).transition("tooltip").duration(400);
                            selection.select("path")
                                .style("stroke-width", 3)
                                .style("fill-opacity", d.sets.length == 1 ? .4 : .1)
                                .style("stroke-opacity", 1);
                        })

                        .on("mousemove", function () {
                            tooltip.style("left", (d3.event.pageX) + "px")
                                .style("top", (d3.event.pageY - 28) + "px");
                        })

                        .on("mouseout", function (d, i) {
                            tooltip.transition().duration(400).style("opacity", 0);
                            var selection = d3.select(this).transition("tooltip").duration(400);
                            selection.select("path")
                                .style("stroke-width", 0)
                                .style("fill-opacity", d.sets.length == 1 ? .25 : .0)
                                .style("stroke-opacity", 0);
                        });
                },
                error: function () {
                    alert("Invalid Query. Please make sure you have selected at least 2 pathways.")
                }
            });

            return false;
        }
    );

});
