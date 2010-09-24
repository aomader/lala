var lala = {
    controls: null,
    content: null,
    last_action: null,
    current_song: null,

    init: function() {
        lala.controls = $('nav');
        lala.content = $('section');

        $('#loading').ajaxStart(function() { $(this).show(); }).ajaxStop(function() { $(this).hide(); });

        $.history.init(function(url) {
            lala.action(url, null);
        });

        $('a').live('click', function(e) {
            var url = $(this).attr('href').replace(/^.*#/, '');
            lala.action(url);
            return false;
        });

        lala.status.interval = window.setInterval(function() { lala.parse_data('/api/status', lala.status.update); }, 5000);

        if (!lala.last_action)
            lala.action('current');

        $(window).scroll(function(eventObject) {
            if ($(window)[0].scrollY > 15) {
                lala.controls.css({opacity:0.8});
            } else {
                lala.controls.css({opacity:1});
            }
        });
    },

    status:
    {
        interval: null,
        value: 2,

        update: function(data)
        {

            if (lala.last_action == 'current') {
                var current = $('#track' + data.currentsong.id);
                if (!current.hasClass('current')) {
                    $('section tr').removeClass('current');
                    current.addClass('current');
                }
            }
        },

        disconnected: function(reason)
        {
            if (lala.status.value == 0)
                return;

            lala.status.value = 0;
            lala.content.html('<div class=disconnected>No connection to mpd server: ' + reason + '</div>');
            lala.controls.hide();
        },

        connected: function()
        {
            if (lala.status.value == 1)
                return;

            lala.status.value = 1;
            lala.action(lala.last_action);
            lala.controls.show();
        }
    },

    action: function(url, obj)
    {
        if (url == 'current') {
            lala.parse_data('/api/current', lala.page.current);
            lala.controls.find('a').removeClass('active');
            lala.controls.find('#' + url).addClass('active');
        } else if (['play', 'pause', 'stop', 'next', 'previous'].indexOf(url) >= 0) {
            lala.parse_data('/api/' + url, function (d) {});
            return;
        }

        $.history.load(url);
        lala.last_action = url;
    },

    parse_data: function(url, callback)
    {
        $.getJSON(url, function(data) {
            switch (data.status) {
                case 'disconnected':
                    lala.status.disconnected(data.reason);
                    break;
                case 'error':
                    break;
                case 'ok':
                    callback(data.data);
                    break;
                default:
                    break;
            }
        });
    },

    page:
    {
        current: function(data)
        {
            var content = '<table><tr><th>Artist</th><th>Title</th><th>Duration</th></tr>';

            for (i in data.tracks) {
                var track = data.tracks[i];
                content += '<tr id=track' + track.id + ((track.id == data.current) ? ' class=current' : '') + '><td>' + track.artist + '</td><td>' + track.title + '</td><td>' + track.time + '</td></tr>';
            }
            content += '</table>';

            lala.content.html(content);
        }
    }
};
