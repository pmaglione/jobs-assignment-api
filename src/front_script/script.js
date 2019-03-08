require({
  paths: {
    "jquery-ui": "https://code.jquery.com/ui/1.11.3/jquery-ui.min",
  },
  map: {
    "*" : { "jquery" : "jquery-noconflict" }
  }
}, [ "jquery-noconflict", "jquery-ui"], function() {
  //Ensure MooTools is where it must be
  Window.implement('$', function(el, nc){
    return document.id(el, nc, this.document);
  });

  var $ = window.jQuery;

  var items = $("table[data-eid]");

  $(function() {

    var eids = [];
    items.each(function(i, item) {
      eids.push($(item).data('eid'));
    });

    var job_id = 1357397
    var worker_id = $('#assignment-worker-id').text()

    var getElementUrl = 'https://jobs-assignment-api.herokuapp.com/tasks/'+ job_id +'/'+ worker_id;
    $.getJSON(getElementUrl).done(function(data) {
        if (data.items.length == 0) {
          alert("No more items to assign!")
        } else {
          var eid;
          for(i = 0; i < eids.length; i++) {
            eid = eids[i];
            var item = data.items[0];
            var title_elem = document.getElementById("title-"+eid);
            var content_elem = document.getElementById("content-"+eid);

            $(title_elem).html(item.title);
            $(content_elem).html(item.content);
            $(content_elem).data('item-id', item.id);

            //when item is assigned, store values for report
            $(".job_id").val(job_id);
            $(".worker_id").val(worker_id);
            $(".item_id").val(item.id);
            $(".item_title").val(item.title);
            $(".item_content").val(item.content);
        }
      }
    });

    //intercept submit and send results
    submitVotesUrl = "https://jobs-assignment-api.herokuapp.com/votes"
    $("#job_units").submit(function(e){
      e.preventDefault();
      var form = this;
      item = document.getElementById("content-"+eids[0]);
      item_id = $(item).data('item-id');
      worker_id = $('#assignment-worker-id').text()
      first_item_vote = $('input:radio:checked')[0].value
      item_data = JSON.stringify({'job_id': job_id, 'worker_id': worker_id, 'item_id': item_id, 'vote': first_item_vote})

      $.ajax({
        url:submitVotesUrl,
        type:"POST",
        data:item_data,
        contentType:"application/json; charset=utf-8",
        dataType:"json",
        success: function(){
          form.submit(); // submit bypassing the jQuery bound event
        }
      });
    });
  });
});