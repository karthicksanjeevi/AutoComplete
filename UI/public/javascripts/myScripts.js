function KeyPress() {
    var Value = document.getElementById("word");
    var s = Value.value;

    $.ajax({
        url: '/api/getSuggestion',
        method: 'GET',
        crossDomain: true,
        data: {"word" : s},
        dataType: 'json',
        timeout: 0,
        cache: true,
        async: false,
        statusCode: {
            404: function() {
                alert('Unable To access Server');
            }
        },
        success: function(result) { receivedSuggestion(result) },
        error: function(jqXHR, textStatus, errorThrown) { console.log(textStatus); }
    });
}

function receivedSuggestion(data){
	$('#result').empty();
	for(var i = 0; i < data.status.length; i++){
		$('#result').append('<li>' + data.status[i] + '</li>')
	}
}
