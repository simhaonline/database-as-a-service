(function($) {


    /**
     * setup JQuery's AJAX methods to setup CSRF token in the request before sending it off.
     * http://stackoverflow.com/questions/5100539/django-csrf-check-failing-with-an-ajax-post-request
     */

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?

                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    $.ajaxSetup({
         beforeSend: function(xhr, settings) {
             if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                 // Only send the token to relative URLs i.e. locally.
                 xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
             }
         }
    });

    var Database = function() {};

    var response_aux = null;
    Database.prototype = {
        update_modal_message: function() {
            var environment_id = $("#id_environment").val() || "";
            if (environment_id) {
              $.ajax({
                  type: "GET",
                  dataType: "json",
                  url: "/logical/" + environment_id + "/credential_parameter_by_name/add_database_modal_msg"
              }).done(function (response) {
                  var msg = response.msg || "";
                  $("label[for=id_database_name] .modal_message .modal_extra_message").text(msg).css({'color': 'red'});
              });
            }
        },
        update_engines: function(engines) {
            this.filter_engines(engines);
        },
        update_replication_topology: function(){
            this.filter_replication_topology()
        },
        filter_replication_topology: function(engine_id){
           var environment_id = $("#id_environment").val() || "none";
           engine_id = engine_id || $("#id_engine").val() || "none";
           if(engine_id !== "none"){
                var engine_selector = document.getElementById("id_engine");
                var self = this;
                $.ajax({
                    type: "GET",
                    dataType: "json",
                    url: "/physical/plans_by_engine/" + engine_id + "_" + environment_id + "/"
                }).done(function (response) {
                    response_aux = response
                    if(response.plans.length !== 0){
                        response.plans.push("");
                        var options2ShowSelector = response.plans.map(function(plan) {
                          return "[value='" + plan['replication_topology_id'] + "']";
                        }).join(",");
                        var $replicationTopologyOptions = $("#id_replication_topology option");
                        $replicationTopologyOptions.hide();
                        $replicationTopologyOptions.filter(options2ShowSelector).show();
                        var selectedId = parseInt($replicationTopologyOptions.filter(':selected').val(), 10);
                        if (response.plans.indexOf(selectedId) === -1) {
                          $replicationTopologyOptions.filter("[value='']").eq(0).attr('selected', 'selected');
                        }
                    }
                    else{
                        engine_selector.innerHTML = '<option selected="selected">' +
                                                    'This environment has no active plans</option>';
                    }
                });
            }
        },
        filter_engines: function(all_engines) {
            var environment_id = $("#id_environment").val() || "none";
            var current_engine = $("#id_engine").val() || "none";
            if(environment_id !== "none"){
                var engine_selector = document.getElementById("id_engine");
                var self = this;
                $.ajax({
                    type: "GET",
                    dataType: "json",
                    url: "/physical/engines_by_env/" + environment_id + "/"
                }).done(function (response) {
                    if(response.engines.length !== 0){
                        response.engines.push("");
                        var options2ShowSelector = response.engines.map(function(id) {
                          return "[value='" + id + "']";
                        }).join(",");
                        var $engineOptions = $("#id_engine option");
                        $engineOptions.hide();
                        $engineOptions.filter(options2ShowSelector).show();
                        var selectedId = parseInt($engineOptions.filter(':selected').val(), 10);
                        if (!$engineOptions.filter(":selected").is(":visible")){
                          self.update_replication_topology()
                          $engineOptions.filter("[value='']").eq(0).attr('selected', 'selected');
                        }
                    }
                    else{
                        engine_selector.innerHTML = '<option selected="selected">' +
                                                    'This environment has no active plans</option>';
                    }
                });
            }
        }
    };

    // Document READY
    $(function() {
        var database = new Database();
        field_engine = document.getElementsByClassName("field-engine");
        if(field_engine.length !== 0){
            field_engine = field_engine[0];
        }

        field_replication_topology = document.getElementsByClassName("field-replication_topology");
        if(field_replication_topology.length !== 0){
            field_replication_topology = field_replication_topology[0];
        }

        var $replicationOptions = $("#id_replication_topology option")
        $replicationOptions.hide()

        //Saving all engines before changing it
        engine_selector = document.getElementById("id_engine");
        if(engine_selector !== null){
            var engines = {};
            for(var i=0; i< engine_selector.options.length; i++){
                option = engine_selector.options[i];
                if(option.value !== null)
                    engines[option.value] = option.text;
            }
        }

        $("#id_environment").on("change", function() {
            database.update_engines(engines);
            database.update_modal_message();
        });
        $("#id_environment").change();

        $("#id_engine").on("change", function() {
            database.update_replication_topology();
        });
        $("#id_engine").change();

        $("#id_team").on("change", function() {
            var team = document.getElementById('id_team').value;
            $.ajax({
                "type": "GET",
                "url": "/account/team_contacts/" + team
            }).done(function (response) {
                var contacts = "";
                if(response.contacts != null)
                    contacts = response.contacts;

                document.getElementsByClassName("field-team_contact")[0].innerHTML = "" +
                    '<div class="control-label"><label>Emergency contacts:</label></div>' +
                    '<div class="controls">' +
                    "<p>" + contacts + "</p></div>";
            });
        });

        $(".plan").on("click", function() {
            $("input", ".plan").removeAttr("checked");
            $("input", $(this)).attr("checked", "checked");
        });

        $("#adv_button").on("click", function(ev) {
            var $btn = $(this).button('loading')
            $btn.button('reset')
        });

        var endpoint_popover_active = null;
        $('.show-endpoint').popover({'trigger': 'manual', 'html': false})
        .on('click', function(e) {
            var $this = $(this);
            if (endpoint_popover_active && endpoint_popover_active.attr('data-content') != $this.attr('data-content')) {
                endpoint_popover_active.popover('hide');
            }
            endpoint_popover_active = $this;
            endpoint_popover_active.popover('toggle');
            e.preventDefault();
        });

        var endpoint_popover_active = null;
        $('.show-upgrade, .show-resize').popover({'trigger': 'manual', 'html': true})
        .on('click', function(e) {
            var $this = $(this);
            if (endpoint_popover_active && endpoint_popover_active.attr('data-content') != $this.attr('data-content')) {
                endpoint_popover_active.popover('hide');
            }
            endpoint_popover_active = $this;
            endpoint_popover_active.popover('toggle');
            e.preventDefault();
        });
    });

})(django.jQuery);
