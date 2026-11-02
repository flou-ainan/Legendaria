# Step 47 — Mobile: 1024 px breakpoint, bottom sheets, pinch zoom

**Date:** 2026-10-27
**Related:** plan 08 (item 6)

- All narrow-screen rules (toolbar single row, hamburger menu, drawer, header) now switch at 1024 px instead of 900.
- The drawer and the Look menu are bottom sheets on narrow screens and slide up (`svelte/transition` `fly`, 220 ms; none on desktop). The Look sheet covers the toolbar, so it has a handle at the top that closes it.
- Pinch zoom on the timeline: two touch pointers scale the zoom around the point between them (`onPinchDown/Move/End` in `Timeline.svelte`); the timeline area allows only panning, so the browser does not zoom the page.
- Tested: svelte-check, Vitest 11, e2e (a CDP two-finger pinch in the touch-emulated page zooms the timeline by more than 1.5x), screenshot of the Look sheet. Not tested on a real phone.

Not done from the plan: touch dragging polish on the timeline, a bottom contextual toolbar at the very bottom (it stays under the video).
