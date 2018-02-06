/** This JS controls the overview page of ComPath
 **
 * @requires: jquery, d3
 */



$(document).ready(function () {

    $("#render-venn-diagram").on("submit", function (e) {


            $.ajax({
                url: "/query/overlap" + $("#render-venn-diagram").serialize(),
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
