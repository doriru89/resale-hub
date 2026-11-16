import React from 'react';
import {Series} from 'remotion';
import {AssetCtx} from './theme';
import {Hook, Identify, Intro, Roll} from './scenes-open';
import {Books, Drafts, End, Price, PublishSold} from './scenes-close';

export const SCENES: [React.FC, number][] = [
  [Hook, 175], [Intro, 75], [Roll, 200], [Identify, 255], [Price, 180],
  [Drafts, 165], [PublishSold, 165], [Books, 270], [End, 120],
];
export const DURATION = SCENES.reduce((a, [, d]) => a + d, 0);
export const FPS = 30;

export const ResaleHub: React.FC<{asset?: (p: string) => string}> = ({asset}) => {
  const body = (
    <Series>
      {SCENES.map(([S, d], i) => (
        <Series.Sequence key={i} durationInFrames={d}><S /></Series.Sequence>
      ))}
    </Series>
  );
  return asset ? <AssetCtx.Provider value={asset}>{body}</AssetCtx.Provider> : body;
};
