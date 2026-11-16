import React from 'react';
import {createRoot} from 'react-dom/client';
import {Player} from '@remotion/player';
import {DURATION, FPS, ResaleHub} from './remotion/ResaleHub';

const asset = (p: string) => import.meta.env.BASE_URL + p;

createRoot(document.getElementById('film')!).render(
  <Player
    component={ResaleHub}
    inputProps={{asset}}
    durationInFrames={DURATION}
    fps={FPS}
    compositionWidth={1920}
    compositionHeight={1080}
    style={{width: '100%', height: '100%'}}
    autoPlay
    loop
    controls
    initiallyMuted
    acknowledgeRemotionLicense
  />,
);
