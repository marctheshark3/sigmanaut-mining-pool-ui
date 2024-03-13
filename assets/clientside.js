window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        triggerConfetti: function(n_clicks) {
            if(n_clicks > 0) {
                confetti({
                    particleCount: 100,
                    spread: 70,
                    origin: { y: 0.6 }
                });
            }
            return ''; // Return any necessary value for the Output of the callback
        }
    }
});
