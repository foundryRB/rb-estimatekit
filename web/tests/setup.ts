import '@testing-library/jest-dom';

// jsdom has no canvas, so HTMLCanvasElement.getContext('2d') is unimplemented and
// emits a noisy "Not implemented" error. Components that measure text off a canvas
// (e.g. TsvEditor column sizing) trip it. Stub a 2d context whose measureText gives
// a crude width so measurement code runs silently under test.
HTMLCanvasElement.prototype.getContext = function getContext() {
    return {
        font: '',
        measureText: (text: string) => ({ width: text.length * 8 }),
    };
} as unknown as HTMLCanvasElement['getContext'];

// The page loads public/vodafone-appearance.js before the app and the shell reads its runtime;
// jsdom loads no page script, so the runtime is provided here in its default state.
window.vodafoneAppearance = {
    get: () => ({ preference: 'system', resolved: 'light', motion: true, reduced: false }),
    set: () => {},
    setMotion: () => {},
};
