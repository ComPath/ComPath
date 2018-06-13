/** Network controller
 **
 * @requires: jquery, cytoscape.js
 */


var colours_resource = { // Object resource name -> colour
    reactome: "#d9534f",
    kegg: "#5cb85c",
    wikipathways: "#5bc0de",
    msig: "#777777"
};

var defaultEdgeOpacity = 0.7;

function showMappings(url) {
    window.location = url + "&mappings=True";
}

function getProperty(dict, prop) {
    if (dict[prop] !== undefined) return dict[prop];
    else return "grey";
}

/**
 * Creates a new row in Node/Edge info table
 */
function insertRow(table, row, column1, column2) {
    row = table.insertRow(row);
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
        nodeObject["Pathway Name"] = "<a target='_blank' href='/pathway/" + node.data('resource') + "/" + node.data('resource_id') + "'>" + node.data('name') + "</a>";
    }
    if (node.data('url')) {
        nodeObject["Pathway Link"] = "<a target='_blank' href='" + node.data('url') + "'>" + node.data('resource').toUpperCase()+ "<span class=\"glyphicon glyphicon-new-window\"></span></a>" + "</a>";
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

    if (edge.data('source')) {
        edgeObject["Source"] = edge.data('source');
    }
    if (edge.data('target')) {
        edgeObject["Target"] = edge.data('target');
    }
    if (edge.data('type')) {
        edgeObject["Mapping type"] = edge.data('type');
    }
    if (edge.data('similarity')) {
        edgeObject["Similarity"] = edge.data('similarity');
    }

    var row = 0;
    $.each(edgeObject, function (key, value) {
        insertRow(dynamicTable, row, key, value);
        row++
    });
}

function startCy(data) {
    fetch('/static/json/cy-style.json', {mode: 'no-cors'})
        .then(function (res) {
            return res.json()
        })
        .then(function (style) {

            var range2 = 20 - 1; // Max value range x,y to normalize
            var defaultEdgeWidth = 3;

            //Set style atributes
            data['nodes'].forEach(function (value, i) {
                data['nodes'][i]['data']['label'] = value['data']['name'];
                data['nodes'][i]['data']['color'] = getProperty(colours_resource, value['data']['resource']);
            });

            data['edges'].forEach(function (value, i) {

                if ('similarity' in value['data']) {
                    // If edge belongs to original pathway set comparison, set width of the edge based on similarity
                    data['edges'][i]['data']['width'] = value['data']['similarity'] * range2 + 1;
                    data['edges'][i]['data']['style'] = 'solid';
                }
                else {
                    // The edge represents as a mapping: set different color and width
                    data['edges'][i]['data']['width'] = defaultEdgeWidth;
                    data['edges'][i]['data']['style'] = 'dashed';
                }
            });

            // Add edge property styling to stylesheet
            style[1]["style"]["width"] = "data(width)";
            style[1]["style"]["line-style"] = "data(style)";

            var cy = cytoscape({

                boxSelectionEnabled: false,

                autounselectify: true,

                layout: {
                    fit: true,
                    name: 'grid'
                },

                // TODO: Fix Max zoom
                minZoom: 2,
                maxZoom: 2,
                padding: 15,
                container: document.getElementById('network'),
                elements: {
                    'nodes': data["nodes"],
                    'edges': data["edges"]
                },
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


            cy.$('node').on('grab', function (e) {
                var ele = e.target;
                ele.connectedEdges().style({'line-color': 'black'});
            });


            cy.$('node').on('free', function (e) {
                var ele = e.target;
                ele.connectedEdges().style({'line-color': '#cccccc'});
            });


            layout.run();

            var $config = $('#config');
            var $btnParam = $('<div class="param"></div>');
            $config.append($btnParam);

            var buttons = [
                {
                    label: '<i class="fa fa-random"></i>',
                    layoutOpts: {
                        randomize: true,
                        flow: {axis: 'x', minSeparation: 50}
                    }
                }
            ];

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
            var edgePanel = $("#edge-list"); // Edge submit_data div

            edgePanel.append("<ul id='edge-list-ul' class='list-group checked-list-box not-rounded'></ul>");

            $.each(edges, function (key, e) {
                $("#edge-list-ul").append("<li class='list-group-item'><input class='edge-checkbox' type='checkbox'><span>" +
                    nodeNames[e.data('source')] + ' ' + e.data('type') + ' ' + nodeNames[e.data('target')] + "</span></li>");

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


            function makeSlider(opts, divId) {
                var $input = $('<input style="width: 80%"></input>');
                var $targetId = $('#' + divId);

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

            /**
             * Resets default styles for nodes/edges/text
             */
            function resetAttributes() {
                // Reset visibility and opacity
                cy.filter('node').style("opacity", "1");
                cy.filter('edge').style("opacity", defaultEdgeOpacity);
            }

            /**
             * Highlights nodes from array using property as filter and changes the opacity of the rest of nodes
             * @param {array} nodeArray
             * @param {string} property of the edge to filter
             */
            function highlightNodes(nodeArray, property) {

                nodes = cy.filter("node");


                // Filter not mapped nodes to change opacity
                var nodesNotInArray = nodes.filter(function (nodeObject) {
                    return nodeArray.indexOf(nodeObject.data(property)) < 0;
                });

                // Not mapped links
                var notMappedEdges = cy.filter("edge").filter(function (edgeObject) {
                    // Source and target should be present in the edge
                    return !(nodeArray.indexOf(nodes[edgeObject.data('source')].data(property)) >= 0 || nodeArray.indexOf(nodes[edgeObject.data('target')].data(property)) >= 0);
                });


                nodesNotInArray.style("opacity", "0.3");
                notMappedEdges.style("opacity", "0.2");
            }

            /**
             * Changes the opacity to 0.1 of edges that are not in array
             * @param {array} edgeArray
             * @param {string} property of the edge to filter
             */
            function highlightEdges(edgeArray, property) {

                // Array with names of the nodes in the selected edge
                var nodesInEdges = [];
                nodes = cy.filter("node");

                // Filtered not selected links

                var edgesNotInArray = cy.filter("edge").filter(function (edgeObject) {
                    if (edgeArray.indexOf(nodes[edgeObject.data('source')].data(property) + " &lt;-&gt; " + nodes[edgeObject.data('target')].data(property)) >= 0) {
                        nodesInEdges.push(nodes[edgeObject.data('source')].data(property));
                        nodesInEdges.push(nodes[edgeObject.data('target')].data(property));
                    }
                    else return edgeObject;
                });

                var nodesNotInEdges = cy.filter("node").filter(function (nodeObject) {
                    return (nodesInEdges.indexOf(nodeObject.data(property)) < 0);
                });

                nodesNotInEdges.style("opacity", "0.3");
                edgesNotInArray.style("opacity", "0.2");

            }

            /**
             * Resets default styles for nodes/edges/text on double click
             */
            function resetAttributesDoubleClick() {
                cy.on('tap', function () {
                    resetAttributes();
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

                $(".edge-checkbox:checked").each(function (idx, li) {
                    checkedItems.push(li.parentElement.childNodes[1].innerHTML);
                });

                resetAttributes();

                highlightEdges(checkedItems, 'name');

                resetAttributesDoubleClick();
            });


            $("#threshold-slider").bind("change", function () {

                nodes = cy.filter("node");
                var edgesInThreshold = [];

                var range = $('#threshold-slider').val().split(','); // Array of size two with min,max value of the range

                $.each(cy.filter("edge"), function (key, value) {
                    similarity = value.data('similarity');

                    if (similarity) {
                        if (similarity <= range[1] && similarity >= range[0]) {
                            edgesInThreshold.push(nodes[value.data('source')].data('name') + " &lt;-&gt; " + nodes[value.data('target')].data('name'));
                        }
                    }

                });

                resetAttributes();

                highlightEdges(edgesInThreshold, 'name');

                resetAttributesDoubleClick();

            });


            $('#config-toggle').on('click', function () {
                $('body').toggleClass('config-closed');
                cy.resize();
            });

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

}
