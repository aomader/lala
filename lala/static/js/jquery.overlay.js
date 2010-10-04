;(function($) {
    $.fn.overlay = function(options) {
        $('body:first')
            .append('<div class=overlay_bg></div><div class=overlay></div>');
        $(this).appendTo('body > div.overlay');
        $('body:first')
            .find('.overlay_bg:first')
                .css({
                    display: 'block',
                    width: $(window).width() + 'px',
                    height: $(window).height() + 'px'
                })
                .end()
            .find('.overlay:first')
                .css({
                    display: 'block',
                    left: ($(window).width() - $('body > div.overlay').width()) / 2 + 'px',
                    top: ($(window).height() - $('body > div.overlay').height()) / 2 - 20 + 'px'
                })
                .end();
        $('.overlay_bg:first').animate( {opacity:0.8} );
    };
})(jQuery);
