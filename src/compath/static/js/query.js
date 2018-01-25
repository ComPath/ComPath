
/* Counter for how many analysis has been done */
function geneCount() {
	$.get('txt/gene_symbols.txt', function(data) {
		if ($('textarea#text-area').val()){
			$('span#gene-count').text($('textarea#text-area').val().trim().split(/\r?\n/g).length);

			/* Counter for genes found in Enrichr library*/
//			genelist = $('textarea#text-area').val().toUpperCase();
//			console.log(data.split("\n").length);
//			console.log(genelist.split("\n").length);
//			intersect = array_intersect(data.split("\n"), genelist.split("\n"));
//			$('span#gene-found').text(intersect.length);
		}
		else{
			$('span#gene-count').text(0);
//			$('span#gene-found').text(0);
		}
	});
}

function insertExample() {
	$.get('resources/txt/geneset_example.txt', function(data) {
		$('textarea#geneset-input').val(data);
		geneCount();
	});
	return false;
}