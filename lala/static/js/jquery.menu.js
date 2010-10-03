;(function($) {
    $.fn.context_menu = function(options) {
        if (!options.menu)
            return false;

        var menu = $(options.menu);
        var my_menu = null;
        var fadeIn = options.fadeIn || 125;
        var fadeOut = options.fadeOut || 125;

        return this.each(function() {
            $(this).bind('contextmenu', function(e) {
                var element = this;
                var destroy = function() {
                    if (my_menu) {
                        my_menu.fadeOut(fadeOut).remove();
                        my_menu = null;
                    }
                };

                if (my_menu)
                    destroy();
                my_menu = menu.clone();

                if (options.onBeforeShow)
                    options.onBeforeShow.call(element, my_menu);

                my_menu
                    .css({
                        left: e.pageX + 'px',
                        top: e.pageY + 'px'
                    })
                    .mousedown(function(e) {
                        e.stopImmediatePropagation();
                        return false;
                    })
                    .mouseup(function(e) {
                        e.stopImmediatePropagation();
                        return false;
                    })
                    .insertAfter(menu)
                    .fadeIn(fadeIn)
                    .mouseleave(function(e) {
                        destroy();
                    })
                    .find('li:not(.disabled) a')
                    .click(function(e) {
                        e.stopImmediatePropagation();

                        my_menu.fadeOut(fadeOut);
                        if (options.onClick)
                            options.onClick.call(element, $(this).attr('href').substr(1));
                        my_menu.remove();

                        return false;
                    });

                $(document)
                    .one('mousedown', function() {
                        destroy();
                    })
                    .one('mouseup', function() {
                        destroy();
                    });

                return false;
            });
        });
    };
})(jQuery);
