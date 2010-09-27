var lala = {
    controls: null,
    content: null,
    last_action: null,
    current_song: null,

    init: function() {
        lala.controls = $('nav');
        lala.content = $('section');

        /* loading indicator */
        $('#loading').ajaxStart(function() { $(this).show(); }).ajaxStop(function() { $(this).hide(); });

        /* install history callback */
        $.history.init(function(url) {
            lala.action(url, null);
        });
        $('a').live('click', function(e) {
            var url = $(this).attr('href').replace(/^.*#/, '');
            lala.action(url);
            return false;
        });

        /* install update interval */
        lala.status.interval = window.setInterval(function() { lala.parse_data('/api/status', lala.status.update); }, 5000);

        if (!lala.last_action)
            lala.action('current');

        /* visuals */
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
            var title = 'lala - ';
            if (data.state == 'play') {
                title += 'playing ' + data.current_song.name;
            } else {
                title += data.state;
            }

            document.title = title;

            if (lala.last_action == 'current') {
                $('section tr').removeClass('current');
                $('section tr .time').remove();
                if (data.current_song) {
                    tr = $('#track' + data.current_song.id);
                    tr.addClass('current');
                    tr.find('td:nth-child(3)').prepend('<span class=time>' + data.current_song.time + ' / </span>');
                    
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
        },

        error: function()
        {
            /* we need a notification */
        }
    },

    /* everytime a link gets clicked this function processes it */
    action: function(url, obj)
    {
        if (url == 'current') {
            lala.parse_data('/api/playlist/info', lala.page.current);
            lala.controls.find('a').removeClass('active');
            lala.controls.find('#' + url).addClass('active');
        } else if (['play', 'pause', 'stop', 'next', 'previous'].indexOf(url) >= 0) {
            lala.parse_data('/api/control/' + url, lala.update);
            return;
        }

        var library = url.match(/^library(?:\?(.*))?$/);
        
        if (library != null) {
            lala.parse_data('/api/library' + ((library[1] != undefined) ? '?path=' + library[1] : ''), lala.page.library);
            lala.controls.find('a').removeClass('active');
            lala.controls.find('#library').addClass('active');
        }

        $.history.load(url);
        lala.last_action = url;
    },

    /* the main wrapper to read the json data and do the appropriate things */
    parse_data: function(url, callback)
    {
        $.getJSON(url, function(data) {
            if (data.status == 'ok') {
                lala.status.connected();
                callback(data.data);
            } else if (data.status == 'disconnected') {
                lala.status.disconnected(data.reason);
            } else if (data.status == 'error') {
                lala.status.error(data.reason);
            }
        });
    },

    /* render the main pages */
    page:
    {
        /* display the current playlist */
        current: function(data)
        {
            var content = '<table><tr><th>Artist</th><th>Title</th><th class=right>Duration</th></tr>';
            var i = 0;

            for (i in data.tracks) {
                var track = data.tracks[i];
                content += '<tr id=track' + track.id + ' class="' + (i % 2 == 0 ? 'odd' : '') + ((track.id == data.current) ? ' current' : '') + '"><td>' + track.artist + '</td><td>' + track.title + '</td><td class=right>' + track.time + '</td></tr>';
            }
            content += '</table>';

            lala.content.html(content);
        },

        /* show the file system to add files/folders */
        library: function(data)
        {
            var content = '<table><tr><th>Item</th><th>Action</th></tr>';

            for (i in data.items) {
                var item = data.items[i];
                content += '<tr><td>';
                if (item.directory) {
                    content += '<a href=#library?' + encodeURI(item.path) + ' title="' + item.name + '">' + item.name + '</a>';
                } else {
                    content += item.name;
                }

                content += '</td><td>Actions</td></tr>';
            }
            content += '</table>';

            lala.content.html(content);
        }
    }
};
