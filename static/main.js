load = function () {
    var page_size = $('#page_size').val();
    var page_no = $('#page_no').val();
    $.get('/ds_chunks/' + page_size + '/' + page_no).done(function (data) {
        window.chunks = JSON.parse(data).response;
        var html = '';
        for (var i = 0; i < window.chunks.length; i++) {
            var chunk = window.chunks[i];
            var check = '';
            if (chunk.is_verified)
                check = 'checked';
            html += `<tr data-chunk='`+chunk.id+`'>
    <td data-label="Id">`+ chunk.id + `</td>
    <td data-label="Audio">
    <audio
      controls
      src="`+ chunk.audio_url + `">
          Your browser does not support the
          <code>audio</code> element.
    </audio>
    </td>
    <td data-label="Job">`+ chunk.ds_trans + `</td>
    <td data-label="Real Transcription" contenteditable="true" onfocusout="crud('real_trans')">`+ chunk.real_trans + `</td>
    <td data-label="Name">
        <input type="checkbox" id="is_verified_`+ chunk.id + `" name="is_verified" ` + check + ` onchange="crud('is_verified')">
        <label for="horns">Is Verified</label></td>
  </tr>`;
        }

        $('#table_body').html(html);
    });
}
crud = function(item){
 if(item=='is_verified'){
  new_is_verified = 'false';
  if($(event.target).is(':checked'))
	 new_is_verified = 'true'
  $.get('/ds_update_is_verified/'+$(event.target).closest('tr').data('chunk')+'?is_verified='+new_is_verified).done(function(){
   load();
  });
 }
 if(item=='real_trans'){
   var new_real_trans = $(event.target).text();
   $.get('/ds_update_real_trans/'+$(event.target).closest('tr').data('chunk')+'?real_trans='+new_real_trans).done(function(){
     load();
   });
 }
}

$(document).ready(function () {
    load();
});

