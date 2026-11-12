// Run only for an explicit send/reply event. Never insert chat text into this script.
(() => {
    const eventToken = __MIKA_SCROLL_EVENT__;
    const state = window.__mikaChatScroll || (window.__mikaChatScroll = {});
    if (state.lastEvent === eventToken) return;
    state.lastEvent = eventToken;
    state.cancel?.();

    const scroller = document.querySelector('[data-testid="stMain"]');
    const layout = document.querySelector('.st-key-companion_layout');
    if (!scroller || !layout) return;

    let stopped = false;
    let frame = 0;
    const timers = [];
    const scrollToLatest = () => {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
            if (!stopped) scroller.scrollTo({top: scroller.scrollHeight, behavior: 'instant'});
        });
    };
    const stop = () => {
        if (stopped) return;
        stopped = true;
        cancelAnimationFrame(frame);
        timers.forEach(clearTimeout);
        observer.disconnect();
        scroller.removeEventListener('wheel', onWheel);
        scroller.removeEventListener('touchstart', stop);
        document.removeEventListener('keydown', onKey);
    };
    const onWheel = event => { if (event.deltaY < 0) stop(); };
    const onKey = event => {
        if (!event.target.matches('input, textarea') && ['PageUp', 'Home', 'ArrowUp'].includes(event.key)) stop();
    };
    // Catch layout changes as the response renders, without monitoring indefinitely.
    const observer = new ResizeObserver(scrollToLatest);
    state.cancel = stop;
    observer.observe(layout);
    scroller.addEventListener('wheel', onWheel, {passive: true});
    scroller.addEventListener('touchstart', stop, {passive: true});
    document.addEventListener('keydown', onKey);
    scrollToLatest();
    [80, 220, 500].forEach(delay => timers.push(setTimeout(scrollToLatest, delay)));
    timers.push(setTimeout(stop, 1500));
})();
