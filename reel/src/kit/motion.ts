import {interpolate, spring, Easing} from 'remotion';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
/** 0→1 con llegada rápida y asentado (spring), empezando en el segundo `at`. */
export const pop = (frame: number, fps: number, at: number, damping = 13) =>
  spring({frame: frame - Math.round(at * fps), fps, config: {damping, stiffness: 220, mass: 0.6}});
/** 0→1 lineal con easing, entre dos segundos. */
export const ramp = (frame: number, fps: number, from: number, to: number, ease = Easing.bezier(0.16, 1, 0.3, 1)) =>
  interpolate(frame, [from * fps, to * fps], [0, 1], {...clamp, easing: ease});
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
