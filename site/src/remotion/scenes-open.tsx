import React from 'react';
import {AbsoluteFill, Img, interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import items from '../items.json';
import {C, MONO, Robot, Scene, Step, fade, useAsset, useIn} from './theme';

export const ALL = items.flatMap((it, i) => it.photos.map((p) => ({p, item: i})));

// Step-1 stack geometry, shared so step 2 can pick the stacks up where step 1 left them.
const STACK_W = 215, SX = 150, SY = 250, THUMB = 150;
export const stackXY = (slot: number, k: number) => ({
  x: SX + (slot % 7) * (STACK_W + 24) + 26 + Math.min(k, 4) * 4,
  y: SY + Math.floor(slot / 7) * 370 + 16 + Math.min(k, 4) * 4,
});
export const slotOf = (uid: string) => items.findIndex((i) => i.uid === uid);

// Step 2 lifts these three stacks to the top row; step 3 picks up the DJI from there.
export const PICKS = ['R116', 'R121', 'R117'];
export const pickXY = (j: number, k: number) => ({x: 420 + j * 540 - THUMB / 2 + Math.min(k, 4) * 5, y: 150 + Math.min(k, 4) * 3});

export const Hook: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const asset = useAsset();
  const cols = 13, rows = 8, cell = 1920 / cols;
  const small = [
    {t: 'A drone. An old phone. Earbuds, hard drives, a 360 camera.', at: 6},
    {t: 'A pasta maker. Lego sets. A chair nobody sits in.', at: 26},
  ];
  const out = 1 - fade(f, 104, 116);
  const q = fade(f, 112, 126);
  return (
    <Scene bg="#16181c">
      <AbsoluteFill style={{transform: `scale(${1.04 + f / 3000})`}}>
        {Array.from({length: cols * rows}, (_, i) => {
          const x = ALL[i % ALL.length];
          const pop = spring({frame: f - random(`p${i}`) * 22, fps, config: {damping: 14}});
          return (
            <Img key={i} src={asset(x.p)} style={{position: 'absolute', left: (i % cols) * cell, top: Math.floor(i / cols) * cell - 30,
              width: cell - 6, height: cell - 6, objectFit: 'cover', borderRadius: 8, opacity: pop * 0.9, transform: `scale(${0.7 + 0.3 * pop})`}} />
          );
        })}
      </AbsoluteFill>
      <AbsoluteFill style={{background: `rgba(22,24,28,${0.35 + 0.3 * fade(f, 40, 70)})`}} />
      <AbsoluteFill style={{justifyContent: 'center', padding: '0 200px', color: '#fff', opacity: out, textShadow: '0 2px 18px rgba(0,0,0,.85)'}}>
        {small.map((l, i) => {
          const p = fade(f, l.at, l.at + 12);
          return <div key={i} style={{fontSize: 50, fontWeight: 700, color: '#fff', lineHeight: 1.3, opacity: p, transform: `translateY(${(1 - p) * 16}px)`}}>{l.t}</div>;
        })}
        <div style={{marginTop: 46, fontSize: 104, fontWeight: 800, letterSpacing: '-0.035em', lineHeight: 1.05}}>
          <span style={{opacity: fade(f, 52, 64)}}>I always say I’ll sell them.</span><br />
          <span style={{opacity: fade(f, 74, 84), color: '#ff6b5a'}}>I never do.</span>
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: q}}>
        <div style={{fontSize: 112, fontWeight: 800, color: '#fff', textAlign: 'center', textShadow: '0 2px 24px rgba(0,0,0,.9)', letterSpacing: '-0.035em', lineHeight: 1.05,
          transform: `scale(${0.94 + q * 0.06})`}}>If only I could just<br />take the pictures.</div>
      </AbsoluteFill>
    </Scene>
  );
};

export const Intro: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame: f, fps, config: {damping: 20}});
  const b = a, c = a;
  return (
    <Scene>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', gap: 28}}>
        <div style={{fontSize: 36, fontWeight: 600, color: C.muted, opacity: a, letterSpacing: '0.02em'}}>Introducing</div>
        <div style={{display: 'flex', alignItems: 'center', gap: 32, transform: `scale(${0.88 + 0.12 * b})`, opacity: b}}>
          <div style={{width: 130, height: 130, borderRadius: 65, background: C.accent, color: '#fff', display: 'grid', placeItems: 'center', fontSize: 70, fontWeight: 800}}>R</div>
          <div style={{fontSize: 140, fontWeight: 800, letterSpacing: '-0.04em'}}>Resale Hub</div>
        </div>
        <div style={{fontSize: 36, color: C.muted, opacity: c, transform: `translateY(${(1 - c) * 16}px)`, textAlign: 'center', lineHeight: 1.4}}>
          A Claude Code skill: photos become marketplace drafts,<br />and sales become a tax worksheet.
        </div>
      </AbsoluteFill>
    </Scene>
  );
};

// 86 photos fall into a camera roll, then sort themselves into 14 items.
export const Roll: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const asset = useAsset();
  const cols = 15, cell = 100, gx = 210, gy = 230;
  const counters = items.map(() => 0);
  const sortStart = 72;
  const label = fade(f, sortStart + 50, sortStart + 72);
  return (
    <Scene>
      <Step n={1} title="Sort the camera roll" who="Claude groups photos into items" />
      <div style={{position: 'absolute', right: 80, top: 70, fontSize: 32, fontWeight: 700, color: C.muted}}>
        {f < sortStart + 40 ? `Camera roll · ${ALL.length} photos` : `${ALL.length} photos → ${items.length} items`}
      </div>
      {ALL.map((x, i) => {
        const k = counters[x.item]++;
        const appear = spring({frame: f - i * 0.5, fps, config: {damping: 15}});
        const move = spring({frame: f - sortStart - x.item * 2, fps, config: {damping: 20, mass: 0.8}});
        const ax = gx + (i % cols) * (cell + 8), ay = gy + Math.floor(i / cols) * (cell + 8);
        const b = stackXY(x.item, k);
        const size = interpolate(move, [0, 1], [cell, THUMB]);
        return (
          <Img key={i} src={asset(x.p)} style={{position: 'absolute', left: interpolate(move, [0, 1], [ax, b.x]), top: interpolate(move, [0, 1], [ay, b.y]),
            width: size, height: size, objectFit: 'cover', borderRadius: 10, opacity: appear,
            transform: `scale(${0.6 + 0.4 * appear}) rotate(${move * ((k % 3) - 1) * 4}deg)`,
            boxShadow: move > 0.5 ? '0 2px 6px rgba(0,0,0,.25)' : 'none', zIndex: k}} />
        );
      })}
      {items.map((it, slot) => (
        <div key={it.uid} style={{position: 'absolute', left: SX + (slot % 7) * (STACK_W + 24), top: SY + Math.floor(slot / 7) * 370 + 205,
          width: STACK_W, textAlign: 'center', opacity: label}}>
          <div style={{fontSize: 23, fontWeight: 700, lineHeight: 1.2}}>{it.name}</div>
          <div style={{display: 'inline-block', marginTop: 6, fontSize: 18, fontWeight: 600, color: C.accent, background: C.accentSoft, borderRadius: 12, padding: '2px 12px'}}>
            {it.cat} · {it.photos.length}
          </div>
        </div>
      ))}
    </Scene>
  );
};

// Three stacks rise; one agent names each item from a specific photo, another looks up
// the original price for taxes later. The third item needs a human answer.
const FOUND = [
  {at: 52, name: 'DJI Mavic Air 2 Fly More Combo', from: 'photo 1: drone, RC-N1 controller, 3 batteries, charging hub', photo: 'img/roll/R116-1.jpg', ok: true},
  {at: 96, name: 'OnePlus Open, 16 GB / 512 GB', from: 'photo 14: the battery-health screen in Settings', photo: 'img/roll/R121-14.jpg', ok: true},
  {at: 140, name: 'Razer Kishi: V3 Pro or V3?', from: 'The back label isn’t in any of the 6 photos.', photo: 'img/roll/R117-1.jpg', ok: false},
];
const MSRP = [{at: 80, n: 'Mavic Air 2 Fly More Combo', v: '$988'}, {at: 122, n: 'OnePlus Open 512 GB', v: '$1,699.99'}, {at: 229, n: 'Razer Kishi V3 Pro', v: '$149.99'}];

export const Identify: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const asset = useAsset();
  const lift = spring({frame: f - 4, fps, config: {damping: 22, mass: 0.9}});
  const card = FOUND.filter((c) => f >= c.at).pop();
  const waiting = f >= 150 && f < 213;
  const answered = f >= 213;
  return (
    <Scene>
      <Step n={2} title="Identify each item" who="One agent names it from the photos. Another finds the original price" />
      {items.map((it, slot) => {
        const j = PICKS.indexOf(it.uid);
        return it.photos.slice(0, 5).map((p, k) => {
          const a = stackXY(slot, k);
          if (j < 0) return <Img key={p} src={asset(p)} style={{position: 'absolute', left: a.x, top: a.y, width: THUMB, height: THUMB, objectFit: 'cover', borderRadius: 10, opacity: 1 - fade(f, 0, 12)}} />;
          const b = pickXY(j, k);
          return <Img key={p} src={asset(p)} style={{position: 'absolute', left: interpolate(lift, [0, 1], [a.x, b.x]), top: interpolate(lift, [0, 1], [a.y, b.y]), width: THUMB, height: THUMB,
            objectFit: 'cover', borderRadius: 10, zIndex: k, transform: `rotate(${((k % 3) - 1) * 4}deg)`, boxShadow: '0 2px 6px rgba(0,0,0,.25)'}} />;
        });
      })}
      {PICKS.map((uid, j) => {
        const c = FOUND[j];
        const named = j < 2 ? f >= c.at + 8 : answered;
        const label = j < 2 ? c.name : named ? 'Razer Kishi V3 Pro' : '?';
        return (
          <div key={uid} style={{position: 'absolute', left: 420 + j * 540 - 230, top: 330, width: 460, textAlign: 'center', fontSize: 28, fontWeight: 800,
            color: named ? C.ink : C.waitInk, opacity: fade(f, j < 2 ? c.at : 140, (j < 2 ? c.at : 140) + 8)}}>
            {named && <span style={{color: C.ok}}>✓ </span>}{label}
          </div>
        );
      })}
      {/* agent 1 */}
      <div style={{position: 'absolute', left: 120, top: 420, width: 1060, height: 600}}>
        <div style={{position: 'absolute', left: 260, top: 0, width: 800, height: 440, background: '#1c1e21', borderRadius: 18, padding: 14, boxShadow: '0 10px 30px rgba(0,0,0,.25)'}}>
          <div style={{width: '100%', height: '100%', background: C.card, borderRadius: 10, overflow: 'hidden', position: 'relative'}}>
            {card && <IdCard c={card} f={f} />}
            {waiting && (
              <div style={{position: 'absolute', inset: 0, background: 'rgba(247,185,40,.94)', display: 'grid', placeItems: 'center', color: '#3d2a00',
                opacity: 0.75 + 0.25 * Math.abs(Math.sin(f / 7))}}>
                <div style={{textAlign: 'center'}}>
                  <div style={{fontSize: 64, fontWeight: 900, letterSpacing: '0.04em'}}>WAITING FOR YOU</div>
                  <div style={{fontSize: 28, fontWeight: 600, marginTop: 8}}>Is the Kishi a V3 Pro or a V3?</div>
                </div>
              </div>
            )}
          </div>
        </div>
        <Robot style={{position: 'absolute', left: 0, top: 170}} size={250} f={f} paused={waiting} />
      </div>
      {f >= 183 && (
        <div style={{position: 'absolute', right: 700, top: 905, opacity: fade(f, 183, 195), background: C.accent, color: '#fff', borderRadius: 24, padding: '16px 24px', fontSize: 28}}>
          <b style={{opacity: 0.75, fontSize: 20, marginRight: 10}}>You</b>V3 Pro. It’s on the box in photo 6.
        </div>
      )}
      {/* agent 2 */}
      <div style={{position: 'absolute', right: 80, top: 420, width: 560}}>
        <div style={{background: '#1c1e21', borderRadius: 18, padding: 14, boxShadow: '0 10px 30px rgba(0,0,0,.25)'}}>
          <div style={{background: C.card, borderRadius: 10, padding: '18px 22px', minHeight: 300}}>
            <div style={{fontSize: 20, fontWeight: 800, color: C.muted}}>ORIGINAL PRICE · FOR YOUR TAXES LATER</div>
            {MSRP.map((m) => (
              <div key={m.n} style={{display: 'flex', justifyContent: 'space-between', fontSize: 25, padding: '12px 0', borderTop: `1px solid ${C.line}`, opacity: fade(f, m.at, m.at + 10)}}>
                <span>{m.n}</span><b>{m.v}</b>
              </div>
            ))}
          </div>
        </div>
        <Robot style={{position: 'absolute', left: 190, top: 330}} size={170} f={f + 13} />
      </div>
      <div style={{position: 'absolute', left: 120, bottom: 40, fontFamily: MONO, fontSize: 22, color: C.ok, opacity: fade(f, 229, 241)}}>
        ✓ folders created · items/R116-dji-mavic-air-2 · R121-oneplus-open · R117-razer-kishi-v3-pro
      </div>
    </Scene>
  );
};

const IdCard: React.FC<{c: typeof FOUND[number]; f: number}> = ({c, f}) => {
  const asset = useAsset();
  const p = fade(f, c.at, c.at + 8);
  return (
    <div style={{display: 'flex', gap: 24, padding: 26, opacity: p, transform: `translateX(${(1 - p) * 30}px)`}}>
      <Img src={asset(c.photo)} style={{width: 300, height: 300, objectFit: 'cover', borderRadius: 12, outline: `5px solid ${c.ok ? C.ok : C.wait}`}} />
      <div style={{display: 'flex', flexDirection: 'column', gap: 12, paddingTop: 6}}>
        <div style={{fontSize: 20, fontWeight: 800, color: c.ok ? C.ok : C.waitInk}}>{c.ok ? '✓ IDENTIFIED' : '? NOT SURE'}</div>
        <div style={{fontSize: 38, fontWeight: 800, lineHeight: 1.15}}>{c.name}</div>
        <div style={{fontSize: 24, color: C.muted, lineHeight: 1.35}}>{c.ok ? 'From ' : ''}{c.from}</div>
      </div>
    </div>
  );
};
