import React from 'react';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {AssetCtx} from './theme';
import {Hook, Identify, Intro, Roll} from './scenes-open';
import {Books, Drafts, End, Price, PublishSold} from './scenes-close';

// [scene, frames, crossfade into the next]. Roll → Identify → Price carry the same
// photos across the cut, so they join without a fade; Hook → Intro is a hard cut on purpose.
const XF = 12;
export const SCENES: [React.FC, number, boolean][] = [
  [Hook, 175, false], [Intro, 77, true], [Roll, 119, false], [Identify, 252, false], [Price, 165, true],
  [Drafts, 165, true], [PublishSold, 136, true], [Books, 345, true], [End, 120, false],
];
export const DURATION = SCENES.reduce((a, [, d, x]) => a + d - (x ? XF : 0), 0);
export const FPS = 30;

export const ResaleHub: React.FC<{asset?: (p: string) => string}> = ({asset}) => {
  const body = (
    <TransitionSeries>
      {SCENES.flatMap(([S, d, x], i) => [
        <TransitionSeries.Sequence key={i} durationInFrames={d}><S /></TransitionSeries.Sequence>,
        ...(x ? [<TransitionSeries.Transition key={`t${i}`} presentation={fade()} timing={linearTiming({durationInFrames: XF})} />] : []),
      ])}
    </TransitionSeries>
  );
  return asset ? <AssetCtx.Provider value={asset}>{body}</AssetCtx.Provider> : body;
};
