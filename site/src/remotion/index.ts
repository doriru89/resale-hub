import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {DURATION, FPS, ResaleHub} from './ResaleHub';

const Root: React.FC = () =>
  React.createElement(Composition, {
    id: 'ResaleHub', component: ResaleHub, durationInFrames: DURATION, fps: FPS, width: 1920, height: 1080,
  });

registerRoot(Root);
