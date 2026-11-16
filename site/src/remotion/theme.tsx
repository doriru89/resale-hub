import React, {createContext, useContext} from 'react';
import {AbsoluteFill, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Inter';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';

export const {fontFamily: INTER} = loadFont('normal', {weights: ['400', '500', '600', '700', '800'], subsets: ['latin']});
export const {fontFamily: MONO} = loadMono('normal', {weights: ['400', '600'], subsets: ['latin']});

export const C = {
  ground: '#f0f2f5', card: '#ffffff', ink: '#1c1e21', muted: '#65676b', line: '#dadde1',
  accent: '#1877f2', accentSoft: '#e7f0fd', sold: '#e41e3f', ok: '#31a24c', okSoft: '#e6f4ea',
  wait: '#f7b928', waitSoft: '#fff5d6', waitInk: '#7a5200',
};

// Photos resolve through Remotion's public dir when rendering, through Vite's base URL in the web Player.
export const AssetCtx = createContext<(p: string) => string>((p) => staticFile(p));
export const useAsset = () => useContext(AssetCtx);

export const useIn = (delay = 0, damping = 18) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - delay, fps, config: {damping}});
};

export const fade = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

export const Scene: React.FC<{children: React.ReactNode; bg?: string}> = ({children, bg = C.ground}) => (
  <AbsoluteFill style={{background: bg, fontFamily: INTER, color: C.ink}}>{children}</AbsoluteFill>
);

export const Card: React.FC<{style?: React.CSSProperties; children: React.ReactNode}> = ({style, children}) => (
  <div style={{background: C.card, borderRadius: 16, boxShadow: '0 1px 3px rgba(0,0,0,.14)', ...style}}>{children}</div>
);

// The step label that sits top-left on every scene after the intro.
export const Step: React.FC<{n: number; title: string; who: string; human?: boolean}> = ({n, title, who, human}) => {
  const p = useIn(0);
  return (
    <div style={{position: 'absolute', left: 80, top: 56, display: 'flex', alignItems: 'center', gap: 20,
      opacity: p, transform: `translateY(${(1 - p) * -20}px)`}}>
      <div style={{width: 60, height: 60, borderRadius: 30, background: human ? C.waitSoft : C.accentSoft,
        color: human ? C.waitInk : C.accent, display: 'grid', placeItems: 'center', fontSize: 28, fontWeight: 800}}>{n}</div>
      <div>
        <div style={{fontSize: 42, fontWeight: 800, letterSpacing: '-0.02em'}}>{title}</div>
        <div style={{fontSize: 24, color: C.muted, fontWeight: 600}}>{who}</div>
      </div>
    </div>
  );
};

export const Bubble: React.FC<{from: 'claude' | 'you'; children: React.ReactNode; delay: number; style?: React.CSSProperties}> = ({from, children, delay, style}) => {
  const p = useIn(delay, 16);
  const you = from === 'you';
  return (
    <div style={{display: 'flex', justifyContent: you ? 'flex-end' : 'flex-start', opacity: p,
      transform: `translateY(${(1 - p) * 24}px) scale(${0.96 + p * 0.04})`, ...style}}>
      <div style={{maxWidth: 760, padding: '18px 24px', borderRadius: 24, fontSize: 28, lineHeight: 1.35,
        background: you ? C.accent : C.card, color: you ? '#fff' : C.ink,
        boxShadow: you ? 'none' : '0 1px 3px rgba(0,0,0,.14)'}}>
        <div style={{fontSize: 18, fontWeight: 700, opacity: 0.7, marginBottom: 4}}>{you ? 'You' : 'Claude'}</div>
        {children}
      </div>
    </div>
  );
};

export const Browser: React.FC<{url: string; label: string; style?: React.CSSProperties; dark?: boolean; children: React.ReactNode; typeFrom?: number}> = ({url, label, style, dark, children, typeFrom = 0}) => {
  const f = useCurrentFrame();
  const shown = Math.max(0, Math.min(url.length, Math.floor((f - typeFrom) * 4)));
  return (
    <div style={{borderRadius: 14, overflow: 'hidden', boxShadow: '0 12px 40px rgba(0,0,0,.18)', background: dark ? '#0f1115' : C.card, ...style}}>
      <div style={{height: 56, background: dark ? '#1d2027' : '#e4e6eb', display: 'flex', alignItems: 'center', gap: 14, padding: '0 18px'}}>
        <div style={{display: 'flex', gap: 8}}>{['#ff5f57', '#febc2e', '#28c840'].map((c) => <div key={c} style={{width: 14, height: 14, borderRadius: 7, background: c}} />)}</div>
        <div style={{flex: 1, background: dark ? '#0f1115' : '#fff', color: dark ? '#8b92a5' : C.muted, borderRadius: 18, padding: '7px 16px', fontSize: 20, fontFamily: MONO, whiteSpace: 'nowrap', overflow: 'hidden'}}>
          {url.slice(0, shown)}
        </div>
        <div style={{fontSize: 17, fontWeight: 700, color: dark ? '#8b92a5' : C.muted}}>{label}</div>
      </div>
      {children}
    </div>
  );
};

// A plain robot at a keyboard: arms tap while it works, still while it waits.
export const Robot: React.FC<{size: number; f: number; paused?: boolean; style?: React.CSSProperties}> = ({size, f, paused, style}) => {
  const tap = paused ? 0 : Math.sin(f / 2.2) * 5;
  const blink = Math.floor(f / 45) % 6 === 0 && f % 45 < 4;
  return (
    <svg width={size} height={size * 1.1} viewBox="0 0 100 110" style={style}>
      <line x1="50" y1="4" x2="50" y2="16" stroke="#65676b" strokeWidth="3" strokeLinecap="round" />
      <circle cx="50" cy="5" r="4.5" fill={paused ? '#f7b928' : '#1877f2'} />
      <rect x="18" y="16" width="64" height="44" rx="14" fill="#e4e6eb" stroke="#1c1e21" strokeWidth="3" />
      <rect x="27" y="26" width="46" height="24" rx="8" fill="#1c1e21" />
      <ellipse cx="41" cy="38" rx="5" ry={blink ? 0.8 : 5} fill={paused ? '#f7b928' : '#7bd88f'} />
      <ellipse cx="59" cy="38" rx="5" ry={blink ? 0.8 : 5} fill={paused ? '#f7b928' : '#7bd88f'} />
      <rect x="28" y="64" width="44" height="30" rx="10" fill="#e4e6eb" stroke="#1c1e21" strokeWidth="3" />
      <path d={`M28 72 Q14 ${84 + tap} 22 ${96 + tap}`} stroke="#1c1e21" strokeWidth="5" fill="none" strokeLinecap="round" />
      <path d={`M72 72 Q86 ${84 - tap} 78 ${96 - tap}`} stroke="#1c1e21" strokeWidth="5" fill="none" strokeLinecap="round" />
      <rect x="8" y="97" width="84" height="10" rx="3" fill="#bcc0c4" stroke="#1c1e21" strokeWidth="2.5" />
    </svg>
  );
};

// Marketplace wordmarks, set in type rather than copied artwork.
export const Wordmark: React.FC<{site: 'ebay' | 'fb' | 'mercari' | 'swappa'; size?: number}> = ({site, size = 40}) => {
  if (site === 'ebay') return (
    <span style={{fontSize: size, fontWeight: 700, letterSpacing: '-0.06em', fontFamily: 'Helvetica, Arial, sans-serif'}}>
      <span style={{color: '#e53238'}}>e</span><span style={{color: '#0064d2'}}>b</span><span style={{color: '#f5af02'}}>a</span><span style={{color: '#86b817'}}>y</span>
    </span>
  );
  if (site === 'fb') return (
    <span style={{display: 'inline-flex', alignItems: 'center', gap: size * 0.25}}>
      <span style={{width: size, height: size, borderRadius: size / 2, background: '#0866ff', color: '#fff', display: 'grid', placeItems: 'center',
        fontWeight: 800, fontSize: size * 0.8, fontFamily: 'Helvetica, Arial, sans-serif', lineHeight: 1, paddingTop: size * 0.12}}>f</span>
      <span style={{fontSize: size * 0.62, fontWeight: 800, color: '#1c1e21'}}>Marketplace</span>
    </span>
  );
  if (site === 'mercari') return <span style={{fontSize: size * 0.9, fontWeight: 800, color: '#4f3cf0', letterSpacing: '-0.03em'}}>mercari</span>;
  return <span style={{fontSize: size * 0.9, fontWeight: 800, color: '#53a93f', letterSpacing: '-0.02em'}}>swappa</span>;
};

export const Stamp: React.FC<{p: number; style?: React.CSSProperties}> = ({p, style}) => (
  <div style={{position: 'absolute', background: C.sold, color: '#fff', fontWeight: 800, letterSpacing: '0.08em',
    padding: '6px 14px', borderRadius: 6, fontSize: 22, opacity: Math.min(1, p * 1.5),
    transform: `rotate(-6deg) scale(${2.2 - 1.2 * p})`, ...style}}>SOLD</div>
);
