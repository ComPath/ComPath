/* Counter for how many analysis has been done */
function geneCount() {
    $.get('txt/gene_symbols.txt', function (data) {
        if ($('textarea#text-area').val()) {
            $('span#gene-count').text($('textarea#text-area').val().trim().split(/\r?\n/g).length);
        }
        else {
            $('span#gene-count').text(0);
//			$('span#gene-found').text(0);
        }
    });
}

function insertExample() {
    $.get('resources/txt/geneset_example.txt', function (data) {
        $('textarea#geneset-input').val(data);
        geneCount();
    });
    return false;
}