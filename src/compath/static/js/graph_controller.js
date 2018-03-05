var colours_resource = { // Object resource name -> colour
    reactome: "blue",
    kegg: "red",
    wikipathways: "green"
};


function getProperty(o, prop) {
    if (o[prop] !== undefined) return o[prop];
    else return "grey";
}

/**
 * Returns the url of the json file needed to render cytsocape js visualization
 * @returns {str} url
 */
function getJsonPath() {

    var resource = $("#resource-input").val();

    // Define the path of the json file according to the selection
    var path;
    if (resource === "all-resources") { // All resources vs all resources
        path = "static/json/wikipathways/wikipathways_90.json"
    }
    else {  // resource + range
        path = "static/json/" + resource + "/" + resource + "_" + $("#similarity-range").val() + ".json"
    }

    return path
}

/**
 * Creates a new row in Node/Edge info table
 */
function insertRow(table, row, column1, column2) {
    /*
     <div class="panel panel-default">
     <dl class="dl-horizontal">
     <dt>Node x</dt>
     <dt>Definition</dd>
     <dd>Foo</dt>
     <dt>Definition2</dt>
     <dd>Foo2</dt>
     <dt>Definition3</dd>
     <dd>Foo3</dd>
     </dl>
     </div>*/

    var row = table.insertRow(row);
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    cell1.innerHTML = column1;
    cell2.innerHTML = column2;
}

/**
 * Renders node info table
 * @param {object} node object
 */
function displayNodeInfo(node) {

    var dynamicTable = document.getElementById('info-table');

    while (dynamicTable.rows.length > 0) {
        dynamicTable.deleteRow(0);
    }

    var nodeObject = {};

    if (node.data('id')) {
        nodeObject["Node"] = node.data('id') + " (ID: " + node.data('id') + ")";
    }
    if (node.data('name')) {
        nodeObject["Name"] = node.data('name');
    }
    if (node.data('url')) {
        nodeObject["Pathway Link"] = "<a target='_blank' href='" + node.data('url') + "'>" + node.data('resource').toUpperCase() + "</a>";
    }

    var row = 0;
    $.each(nodeObject, function (key, value) {
        insertRow(dynamicTable, row, key, value);
        row++
    });
}

/**
 * Renders node info table
 * @param {object} edge object
 */
function displayEdgeInfo(edge) {

    var dynamicTable = document.getElementById('info-table');

    while (dynamicTable.rows.length > 0) {
        dynamicTable.deleteRow(0);
    }

    var edgeObject = {};

    if (edge.data('id')) {
        edgeObject["ID"] = edge.data('id');
    }
    if (edge.data('source')) {
        edgeObject["Source"] = edge.data('source');
    }
    if (edge.data('target')) {
        edgeObject["Target"] = edge.data('target');
    }

    var row = 0;
    $.each(edgeObject, function (key, value) {
        insertRow(dynamicTable, row, key, value);
        row++
    });
}

/**
 * Resets default styles for nodes/edges/text
 */
function resetAttributes() {
    // Reset visibility and opacity
    cy.filter('node').style("opacity", "1");
    cy.filter('edge').style("opacity", "1");
}

/**
 * Highlights nodes from array using property as filter and changes the opacity of the rest of nodes
 * @param {array} nodeArray
 * @param {string} property of the edge to filter
 */
function highlightNodes(nodeArray, property) {

    // Filter not mapped nodes to change opacity
    var nodesNotInArray = cy.filter("node").filter(function (nodeObject) {
        return nodeArray.indexOf(nodeObject.data(property)) < 0;
    });


    // TODO: Fix highlight connected Edges.
    // Not mapped links
    var notMappedEdges = cy.filter("edge").filter(function (edgeObject) {
        // Source and target should be present in the edge
        return !(nodeArray.indexOf(edgeObject.data('source')) >= 0 || nodeArray.indexOf(edgeObject.data('target') >= 0));
    });

    console.log(notMappedEdges);

    nodesNotInArray.style("opacity", "0.4");
    notMappedEdges.style("opacity", "0.1");
}

/**
 * Changes the opacity to 0.1 of edges that are not in array
 * @param {array} edgeArray
 * @param {string} property of the edge to filter
 */
function highlightEdges(edgeArray, property) {

    // Array with names of the nodes in the selected edge
    var nodesInEdges = [];

    // TODO: Fix highlight selected Edges.
    // Filtered not selected links
    var edgesNotInArray = cy.filter("node").filter(function (edgeObject) {

        if (edgeArray.indexOf(edgeObject.data('source') + "->" + edgeObject.data('id') + " " + edgeObject.data('target')) >= 0) {
            nodesInEdges.push(edgeObject.data('source'));
            nodesInEdges.push(edgeObject.data('target'));
        }
        else return edgeObject;
    });

    var nodesNotInEdges = cy.filter("node").filter(function (edgeObject) {
        return (nodesInEdges.indexOf(edgeObject.data('source')) < 0 || nodesInEdges.indexOf(edgeObject.data('target')) < 0);
    });

    nodesNotInEdges.style("opacity", "0.1");
    edgesNotInArray.style("opacity", "0.1");

}

/**
 * Resets default styles for nodes/edges/text on double click
 */
function resetAttributesDoubleClick() {
    // TODO: On double click
    cy.on('tap', function (event) {
        cy.filter("node").style("opacity", "1");
    });
}

function startCy(urlPath) {
    $.getJSON(urlPath, function (data) {
        fetch('/static/json/cy-style.json', {mode: 'no-cors'})
            .then(function (res) {
                return res.json()
            })
            .then(function (style) {

                // TODO: ink width defined by similarity. Fix sliders, I bet the same value is being passed all over again/

                //Set style atributes
                data['nodes'].forEach(function (value, i) {
                    data['nodes'][i]['data']['label'] = value['data']['name'];
                    data['nodes'][i]['classes'] = 'top-left';
                    data['nodes'][i]['data']['color'] = colours_resource[value['data']['resource']];

                });

                var cy = window.cy = cytoscape({

                    boxSelectionEnabled: false,

                    autounselectify: true,

                    layout: {
                        name: 'grid',
                        cols: 5
                    },

                    // TODO: Fix Max zoom
                    minZoom: 2,
                    maxZoom: 2,
                    padding: 15,


                    container: document.getElementById('network'),

                    elements: data,
                    style: style

                });

                var params = {
                    name: 'cola',
                    nodeSpacing: 30,
                    edgeLengthVal: 45,
                    animate: true,
                    randomize: false,
                    maxSimulationTime: 1500
                };
                var layout = makeLayout();
                var running = false;

                cy.on('layoutstart', function () {
                    running = true;
                }).on('layoutstop', function () {
                    running = false;
                });

                layout.run();

                var $config = $('#config');
                var $btnParam = $('<div class="param"></div>');
                $config.append($btnParam);

                var sliders = [
                    {
                        param: 'edgeLengthVal',
                        min: 1,
                        max: 200
                    },

                    {
                        param: 'nodeSpacing',
                        min: 1,
                        max: 50
                    }
                ];

                var buttons = [
                    {
                        label: '<i class="fa fa-random"></i>',
                        layoutOpts: {
                            randomize: true,
                            flow: null
                        }
                    },
                    {
                        label: '<i class="fa fa-long-arrow-down"></i>',
                        layoutOpts: {
                            flow: {axis: 'y', minSeparation: 30}
                        }
                    }
                ];

                makeSlider(sliders[0], 'edge-slider');
                makeSlider(sliders[1], 'node-slider');

                buttons.forEach(makeButton);

                // Node check list
                var nodes = cy.filter('node');
                var nodeNames = [];
                var nodePanel = $("#node-list"); // Node submit_data div

                nodePanel.append("<ul id='node-list-ul' class='list-group checked-list-box not-rounded'></ul>");

                $.each(nodes, function (key, n) {
                    var name = n.data('name');
                    nodeNames.push(name);

                    $("#node-list-ul").append("<li class='list-group-item'><input class='node-checkbox' type='checkbox'>" +
                        "<div class='circle " + n.data('resource') + "'>" + // Set circle colour
                        "</div><span class='node-" + name + "'>" + name + "</span></li>");
                });

                cy.on('click', 'node', function (evt) {
                    displayNodeInfo(this);
                });

                // Edge check list
                var edges = cy.filter('edge');
                var edgesNames = [];
                var edgePanel = $("#edge-list"); // Edge submit_data div

                edgePanel.append("<ul id='edge-list-ul' class='list-group checked-list-box not-rounded'></ul>");

                // TODO: Add the circles with color of each resource
                $.each(edges, function (key, e) {

                    $("#edge-list-ul").append("<li class='list-group-item'><input class='edge-checkbox' type='checkbox'><span>" +
                        nodeNames[e.data('source')] + ' <-> ' + nodeNames[e.data('target')] + "</span></li>");

                });
                cy.on('click', 'edge', function (evt) {
                    displayEdgeInfo(this);
                });


                function makeLayout(opts) {
                    params.randomize = false;
                    params.edgeLength = function (e) {
                        return params.edgeLengthVal / e.data('weight');
                    };

                    for (var i in opts) {
                        params[i] = opts[i];
                    }

                    return cy.layout(params);
                }

                function makeSlider(opts, divId) {
                    var $input = $('<input style="width: 80%"></input>');
                    var $targetId = $('#' + divId);

                    // TODO: Center the sliders
                    $targetId.append('<span class="label label-default"></span>');
                    $targetId.append($input);

                    var p = $input.slider({
                        min: opts.min,
                        max: opts.max,
                        max: opts.max,
                        value: params[opts.param]
                    }).on('slide', _.throttle(function () {
                        params[opts.param] = p.getValue();

                        layout.stop();
                        layout = makeLayout();
                        layout.run();
                    }, 16)).data('slider');
                }


                function makeButton(opts) {
                    var $button = $('<button class="btn btn-default">' + opts.label + '</button>');

                    $btnParam.append($button);

                    $button.on('click', function () {
                        layout.stop();

                        if (opts.fn) {
                            opts.fn();
                        }

                        layout = makeLayout(opts.layoutOpts);
                        layout.run();
                    });
                }

                //Get checked nodes.
                $("#get-checked-nodes").on("click", function (event) {

                    var checkedItems = [];
                    $(".node-checkbox:checked").each(function (idx, li) {
                        checkedItems.push(li.parentElement.childNodes[2].className.replace("node-", ""));
                    });

                    resetAttributes();

                    highlightNodes(checkedItems, 'name');

                    resetAttributesDoubleClick();
                });

                //Get checked edges.
                $("#get-checked-edges").on("click", function (event) {

                    var checkedItems = [];

                    $(".node-checkbox:checked").each(function (idx, li) {
                        checkedItems.push(li.parentElement.childNodes[1].innerHTML);
                    });

                    resetAttributes();

                    highlightEdges(checkedItems, 'name');

                    resetAttributesDoubleClick();
                });


                $('#config-toggle').on('click', function () {
                    $('body').toggleClass('config-closed');
                    cy.resize();
                });

                //Node search box.
                $("#node-search").on("keyup", function () {
                    // Get value from search form (fixing spaces and case insensitive
                    var searchText = $(this).val();
                    searchText = searchText.toLowerCase();
                    searchText = searchText.replace(/\s+/g, "");

                    $.each($("#node-list-ul")[0].childNodes, updateNodeArray);

                    function updateNodeArray() {
                        var currentLiText = $(this).find("span")[0].innerHTML,
                            showCurrentLi = ((currentLiText.toLowerCase()).replace(/\s+/g, "")).indexOf(searchText) !== -1;
                        $(this).toggle(showCurrentLi);
                    }
                });

                //Edge search box.
                $("#edge-search").on("keyup", function () {
                    // Get value from search form (fixing spaces and case insensitive
                    var searchText = $(this).val();
                    searchText = searchText.toLowerCase();
                    searchText = searchText.replace(/\s+/g, "");

                    $.each($("#edge-list-ul")[0].childNodes, updateEdgeArray);

                    function updateEdgeArray() {

                        var currentLiText = $(this).find("span")[0].innerHTML,
                            showCurrentLi = ((currentLiText.toLowerCase()).replace(/\s+/g, "")).indexOf(searchText) !== -1;
                        $(this).toggle(showCurrentLi);
                    }
                });


            });
    });
}


$(document).ready(function () {

    startCy(getJsonPath()); // Generate the default Network

    // When click on refresh network button.
    $('#refresh-network').click(function () {

        //Remove the parameter sliders.
        $('.param').remove();

        $('#node-list').empty(); // Clear node list.
        $('#edge-slider').empty();
        $('#node-slider').empty();
        startCy(getJsonPath()); // Generate new Network with new parameters.
    });

});