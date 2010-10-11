var lala =
{
    text:
    {
        current_empty: 'There are no tracks in your current playlist, I\'m sorry :\'('
    },

    current_song: null,
    current_view: null,

    init: function() {
        /* loading indicator */
        $('#loading').ajaxStart(function() { $(this).show(); }).ajaxStop(function() { $(this).hide(); });

        /* commonly used references */
        lala.controls = $('nav:first');
        lala.content = $('section:first');

        /* settings and help overlay */
        $('#settings').click(function() { lala.settings.index(); });
        $('#help').click(function() { lala.help.index(); });

        /* install simple control callbacks */
        $('#previous,#playpause,#stop,#next').click(function() {
            lala.request({
                url: '/api/control/' + ($(this).attr('id') == 'playpause' ? $(this).attr('class') : $(this).attr('id')),
                callback: lala.status.update
            });
        });

        /* install history callback */
        $.history.init(function(url) {
            lala.action(url);
        });

        /* should we install a history entry and call the desired action */
        $('a').live('click', function(e) {
            var url = $(this).attr('href').replace(/^.*#/, '');
            if (url != '')
                $.history.load(url);
            return false;
        });

        /* install update interval */
        lala.status.interval = window.setInterval(function() {
            lala.request({
                url: '/api/status',
                callback: lala.status.update,
                global: false
            });
        }, 450);

        /* visuals */
        $(window).scroll(function(eventObject) {
            if ($(window)[0].scrollY > 15) {
                lala.controls.css({opacity:0.8});
            } else {
                lala.controls.css({opacity:1});
            }
        });

        if (document.URL.replace(/.*#/, '') == '')
            $.history.load('current')
    },

    status:
    {
        value: 1,
        last_state: '',
        last_current_song: -1,

        update: function(data)
        {
            if (lala.current_view == 'current' && data.updates.indexOf('playlist') >= 0)
                lala.action('current');

            if (lala.status.last_state != data.state ||
                (data.current_song && data.current_song.id != lala.status.last_current_song))
            {
                var title = '';
                if (data.state == 'play') {
                    title += 'playing ' + data.current_song.title + ' | ';
                } else if (data.state == 'pause') {
                    title += 'paused | ';
                } else if (data.state == 'stop') {
                    title += 'stopped | ';
                }
                document.title = title + 'lala';

                var control_state = (data.state == 'play' ? 'Pause' : 'Play');
                $('#playpause')
                    .attr({
                        class: control_state.replace(/^P/, 'p'),
                        title: control_state
                    })
                    .html(control_state);
            }

            if (data.current_song) {
                if (data.current_song.id != lala.status.last_current_song || lala.status.need_update)
                    $('section > table.current')
                        .find('#current_time')
                            .remove()
                            .end()
                        .find('#' + lala.status.last_current_song)
                            .removeClass('current')
                            .end()
                        .find('#' + data.current_song.id)
                            .addClass('current')
                            .find('td:nth-child(3)')
                                .prepend('<span id=current_time></span>');

                $('#current_time').html(lala.helper.parse_time(data.current_song.time) + ' / ');

                lala.status.last_current_song = data.current_song.id;
            }

            lala.status.last_state = data.state;
        },

        disconnected: function(reason)
        {
            if (lala.status.value == 0)
                return;

            lala.status.value = 0;
            lala.content.html('<div class=disconnected><p>Sorry, but I\'m unable to connect to your mpd server.. :/<br /><span class=reason>' + reason + '</span></p><p><span class=settings>You could check your <a href=# id=check_settings title=Settings>settings</a>, though.</span></p></div>')
                .find('#check_settings')
                    .click(function() {
                        lala.settings.index();
                    });
            lala.controls.hide();
        },

        connected: function()
        {
            if (lala.status.value == 1)
                return;

            lala.status.value = 1;
            lala.controls.show();
        },

        error: function(reason)
        {
            $('<div class=error><strong>Error:</strong> ' + reason + '</div>')
                .appendTo('section:first')
                .animate({top: 45, opacity: 0.9}, 450, 'swing', function() {console.log('done');});
        }
    },

    /* everytime a link gets clicked this function processes it */
    action: function(uri, obj)
    {
        var url = lala.helper.parse_url(uri);

        if (url.path == '')
            return;
        
        /* render the current playlist */
        if (url.path == 'current') {
            lala.request({
                url: '/api/current/list',
                callback: lala.current.index
            });
        }

        /* render the library browser */
        else if (url.path == 'library') {
            lala.request({
                url: '/api/library/list',
                data: {path: decodeURIComponent(url.params.path || '')},
                callback: lala.library.index,
                extra: {path: decodeURIComponent(url.params.path || '')}
            });
        }

        lala.controls
            .find('a.active:first')
                .removeClass('active')
                .end()
            .find('#' + url.path)
                .addClass('active');
    },

    /* display the current playlist */
    current:
    {
        index: function(data, extra)
        {
            lala.current_view = 'current';

            if (data.tracks.length == 0) {
                lala.content.html('<div class=empty>Got no tracks for ya, sorry ... :\'(</div>');
                return;
            }

            lala.status.need_update = true;

            lala.content
                .html(lala.current.build(data))
                .find('a.play')
                    .click(function() {
                        lala.request({
                            url: '/api/current/play',
                            data: {track: $(this).closest('tr').attr('id')},
                            callback: lala.status.update
                        });
                        return false;
                    })
                    .end()
                .find('tr')
                    .context_menu({
                        menu: 'section > ul.context_menu:first',
                        onBeforeShow: function(menu) {
                            if ($(this).hasClass('ui-selected'))
                                menu
                                    .find('li.play:first')
                                        .remove()
                                        .end()
                                    .find('li.current_selection:first')
                                        .html('Selected');
                        },
                        onClick: function(link) {
                            if (link == 'clear') {
                                lala.request({
                                    url: '/api/current/clear',
                                    callback: function() {
                                        lala.content.html('<div class=empty>' + lala.text.current_empty + '</div>');
                                    }
                                });
                            } else if (link == 'remove') {
                                var items = $(this).hasClass('ui-selected') ? lala.content.find('tr.ui-selected') : $(this);
                                lala.request({
                                    url: '/api/current/delete',
                                    data: {tracks: items.map(function() { return $(this).attr('id'); }).get()},
                                    callback: function() {
                                        items.remove();
                                    }
                                });
                            } else if (link == 'play') {
                                lala.request({
                                    url: '/api/current/play',
                                    data: {track: ($(this).hasClass('ui-selected') ? lala.content.find('tr.ui-selected:first') : $(this)).attr('id')},
                                    callback: lala.status.update
                                });
                            }
                        }
                    })
                    .end()
                .find('table:first')
                    .selectable({
                        filter: 'tr:not(.head)',
                        cancel: 'a'
                    });
        },
        
        build: function(data) {
            var content =
                '<table class=current>' +
                    '<tr class=head>' +
                        '<th>Artist</th>' +
                        '<th>Title</th>' +
                        '<th class=right>Duration</th>' +
                    '</tr>';

            for (i in data.tracks) {
                var track = data.tracks[i];
                content +=
                    '<tr id=' + track.id + '>' +
                        '<td><a href=# class=play title="Play ' + track.artist + ' - ' + track.title + '">' + track.artist + '</a></td>' +
                        '<td><a href=# class=play title="Play ' + track.artist + ' - ' + track.title + '">' + track.title + '</a></td>' +
                        '<td class=right>' + lala.helper.parse_time(track.time) + '</td>' +
                    '</tr>';
            }

            return content +
                '</table>' +
                '<ul class=context_menu>' +
                    '<li class="head current_selection">Current</li>' +
                    '<li class=play><a href=#play>Play</a></li>' +
                    '<li><a href=#remove>Remove</a></li>' +
                    '<li class=head>All</li>' +
                    '<li><a href=#clear>Remove</a></li>' +
                '</ul>';
        }
    },

    /* show the file system to add files/folders */
    library:
    {
        index: function(data, extra)
        {
            lala.current_view = 'library';

            lala.content
                .html(lala.library.build(data, true))
                .find('tr')
                    .context_menu(lala.library.context_menu)
                    .end()
                .find('a.expand')
                    .click(function() {
                        lala.library.toggle_callback($(this), 1);
                    })
                    .end()
                .find('table:first')
                    .selectable({
                        filter: 'tr:not(.sterile):not(.head)',
                        cancel: 'a'
                    });
        },

        context_menu:
        {
            menu: 'section > ul.context_menu:first',
            filter: 'tr',
            onBeforeShow: function(menu) {
                if ($(this).hasClass('ui-selected'))
                    menu.find('li.current_selection:first').html('Selected');
            },
            onClick: function(link) {
                var items = $(this).hasClass('ui-selected') ? lala.content.find('tr.ui-selected') : $(this);
                if (link == 'add' || link == 'replace') {
                    lala.request({
                        url: '/api/current/add',
                        data: {
                            paths: items.map(function() { return $(this).attr('data-path'); }).get(),
                            replace: (link == 'replace' ? true : false)
                        }
                    });
                }
            }
        },

        build: function(data, root, level, path)
        {
            root = root || false;
            level = level || 0;
            path = path || '';
            var content = '';

            if (root) {
                content += 
                    '<table>' +
                        '<tr class=head>' +
                            '<th>Item</th>' +
                        '</tr>' +
                        (data.up != undefined ?
                        '<tr>' +
                            '<td>' +
                                '<a href="#library?path=' + encodeURIComponent(data.up) + '" class=up title="One folder up..">One folder up..</a>' +
                            '</td>' +
                        '</tr>' : '');
            } else {
                content +=
                    '<tr class=sterile data-path="sub_' + path + '">' +
                        '<td>' +
                            '<table>';
            }

            for (i in data.paths) {
                var item = data.paths[i];
                content +=
                    '<tr data-path="' + item.path + '">' +
                        '<td' + (!root ? ' style="padding-left:' + (level * 20 + 4) + 'px"' : '') + '>';
                if (item.type == 'directory') {
                    content +=
                                '<a href=# class=expand title="Toggle ' + item.name + '">Toggle ' + item.name + '</a> ' +
                                '<a href="#library?path=' + encodeURIComponent(item.path) + '" title="Go to ' + item.name + '">' + item.name + '</a>';
                } else if (item.type == 'file') {
                    content += '<span class=track>' + item.name + '</span>';
                } else {
                    content += '<span class=playlist>' + item.name + '</span>';
                }

                content +=
                        '</td>' +
                    '</tr>';
            }

            if (root) {
                content +=
                    '</table>' +
                    '<ul class=context_menu>' +
                        '<li class="head current_selection">Current</li>' +
                        '<li><a href=#add>Add</a></li>' +
                        '<li><a href=#replace>Replace</a></li>' +
                        '<li><a href=#update>Update</a></li>' +
                        '<li class=head>All</li>' +
                        '<li><a href=#update>Update</a></li>' +
                    '</ul>';
            } else {
                content +=
                            '</table>' +
                        '</td>' +
                    '</tr>';
            }

            return content;
        },

        toggle_callback: function(link, level)
        {
            var node = link.closest('tr');
            var path = node.attr('data-path');

            if (link.hasClass('expand')) {
                lala.request({
                    url: '/api/library/list',
                    data: {path: path},
                    extra: {
                        node: node,
                        link: link,
                        level: level,
                        path: path
                    },
                    callback: lala.library.expand
                });
            } else {
                lala.content.find('tr[data-path=sub_' + path + ']:first').remove();
                link.removeClass('collapse').addClass('expand');
            }
        },

        expand: function(data)
        {
            var level = this.level + 1;
            $(lala.library.build(data, false, this.level, this.path))
                .insertAfter(this.node)
                .find('tr')
                    .context_menu(lala.library.context_menu)
                    .end()
                .find('a.expand')
                    .click(function() {
                        lala.library.toggle_callback($(this), level);
                    });
            this.link.removeClass('expand').addClass('collapse');
        }
    },

    /* the settings overlay */
    settings:
    {
        index: function()
        {
            return;

            $.get('/settings', null, function(data) {
                $(data)
                    .find('input.save')
                        .click(function() {
                            var host = $('#mpd_host').val();
                            var port = $('#mpd_port').val();
                            var pass = $('#mpd_pass').val();

                            lala.request({
                                url: '/settings',
                                data: {
                                    host: host,
                                    port: port,
                                    pass: pass
                                },
                                callback: function() {
                                    $('body > div.overlay_bg').animate({opacity: 0}).remove();
                                    $('body > div.overlay').remove();
                                    $.history.load(document.URL.replace(/.*#?/, ''));
                                }
                            });

                            return false;
                        })
                        .end()
                    .find('input.abort')
                        .click(function() {
                            $('body > div.overlay_bg').animate({opacity: 0}).remove();
                            $('body > div.overlay').remove();
                            return false;
                        })
                        .end()
                    .overlay();
            });
        }
    },

    /* the main wrapper to interchange json data with the server */
    request: function(options)
    {

        if (options.data)
            options.data = JSON.stringify(options.data);

        $.ajax({
            type: 'POST',
            url: options.url,
            data: options.data,
            dataType: 'json',
            contentType: 'application/json',
            global: options.global == undefined ? true : options.global,
            success: function(data) {
                if (data.status == 'ok') {
                    lala.status.connected();
                    if (options.callback)
                        options.callback.call(options.extra || window, data.data);
                } else if (data.status == 'disconnected') {
                    lala.status.disconnected(data.reason);
                } else if (data.status == 'error') {
                    lala.status.error(data.reason);
                }
            }
        });
    },

    helper:
    {
        parse_url: function(url)
        {
            var a = document.createElement('a');
            a.href = url;
            return {path: a.pathname.replace(/^\/(.*)/, '$1'),
                params: (function(){
                    var ret = {},
                        seg = a.search.replace(/^\?/,'').split('&'),
                        len = seg.length, i = 0, s;
                    for (;i<len;i++) {
                        if (!seg[i]) { continue; }
                        s = seg[i].split('=');
                        ret[s[0]] = s[1];
                    }
                    return ret;
                })(),
                segments: a.pathname.replace(/^\//,'').split('/')}
        },

        parse_time: function(time)
        {
            var sec = time % 60;
            return Math.floor(time / 60) + ':' + (sec < 10 ? '0' : '') + sec;
        }
    }
};
